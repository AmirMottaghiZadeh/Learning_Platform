"""Offline EmbeddingGemma inference. Loads local artifacts; never downloads or calls HTTP."""
from functools import lru_cache
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import Lock
import time

from django.conf import settings
from apps.ai_lab.provider import ProviderError

ARTIFACTS = ("onnx/model_quantized.onnx", "onnx/model_quantized.onnx_data", "tokenizer.json", "config.json")
QUERY_PREFIX = "task: search result | query: "
MAX_TOKENS = 2048
OVERLAP = 128


@lru_cache(maxsize=16)
def _digest(path, size, mtime_ns, inode):
    value = sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def profile():
    if settings.AI_LAB_EMBEDDING_MODEL != "onnx-community/embeddinggemma-300m-ONNX":
        raise ProviderError("LOCAL_EMBEDDING_MODEL_UNSUPPORTED")
    if settings.AI_LAB_EMBEDDING_DIMENSIONS not in {768, 512, 256, 128}:
        raise ProviderError("INVALID_EMBEDDING_CONFIGURATION")
    root = Path(settings.AI_LAB_LOCAL_EMBEDDING_DIR).expanduser().resolve()
    hashes = {}
    try:
        for name in ARTIFACTS:
            path = (root / name).resolve()
            if not path.is_relative_to(root):
                raise ProviderError("LOCAL_EMBEDDING_ARTIFACT_INVALID")
            info = path.stat()
            if not path.is_file() or info.st_size == 0:
                raise ProviderError("LOCAL_EMBEDDING_ARTIFACT_INVALID")
            hashes[name] = _digest(str(path), info.st_size, info.st_mtime_ns, info.st_ino)
    except OSError:
        raise ProviderError("LOCAL_EMBEDDING_MODEL_FILES_REQUIRED") from None
    value = {"backend":"onnx", "model":settings.AI_LAB_EMBEDDING_MODEL,
        "dimensions":settings.AI_LAB_EMBEDDING_DIMENSIONS, "base_url":"local://onnx",
        "revision":settings.AI_LAB_EMBEDDING_REVISION, "normalization":"l2-v1", "artifacts":hashes,
        "input_format":"gemma-title-path-v1", "query_prefix":QUERY_PREFIX,
        "window_policy":{"max_tokens":MAX_TOKENS, "overlap":OVERLAP, "aggregation":"unique-token-weighted-mean-v1"}}
    value["id"] = sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    return value


def format_input(text, purpose):
    if purpose == "query":
        return QUERY_PREFIX + text
    if purpose != "document":
        raise ProviderError("INVALID_EMBEDDING_PURPOSE")
    title, separator, body = text.partition("\n")
    return f"title: {title if separator else 'none'} | text: {body if separator else text}"


class Encoder:
    def __init__(self, configuration, root, threads, batch_size):
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError:
            raise ProviderError("LOCAL_EMBEDDING_DEPENDENCIES_REQUIRED") from None
        if not 1 <= threads <= 16 or not 1 <= batch_size <= 32:
            raise ProviderError("INVALID_LOCAL_EMBEDDING_RESOURCES")
        self.np, self.configuration, self.batch_size = np, configuration, batch_size
        self.lock = Lock()
        self.tokenizer = Tokenizer.from_file(str(Path(root) / "tokenizer.json"))
        # Every overflow window is retained below; source tails are never silently discarded.
        self.tokenizer.enable_truncation(max_length=MAX_TOKENS, stride=OVERLAP)
        self.pad_id = self.tokenizer.token_to_id("<pad>")
        if self.pad_id is None:
            raise ProviderError("LOCAL_EMBEDDING_TOKENIZER_INVALID")
        self.tokenizer.no_padding()
        options = ort.SessionOptions()
        options.intra_op_num_threads, options.inter_op_num_threads = threads, 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        # Same original int8 model/configuration as the old project evaluation.
        options.add_session_config_entry("session.disable_quant_qdq", "1")
        options.log_severity_level = 3
        self.session = ort.InferenceSession(str(Path(root) / ARTIFACTS[0]), options,
            providers=["CPUExecutionProvider"])
        self.inputs = {item.name for item in self.session.get_inputs()}
        if not {"input_ids", "attention_mask"} <= self.inputs or "sentence_embedding" not in {
                item.name for item in self.session.get_outputs()}:
            raise ProviderError("LOCAL_EMBEDDING_GRAPH_INVALID")

    def encode(self, texts, purpose, check_cancelled):
        np = self.np
        with self.lock:
            check_cancelled()
            encoded = self.tokenizer.encode_batch([format_input(text,purpose) for text in texts])
            windows, native_tokens = [], 0
            for index, encoding in enumerate(encoded):
                all_windows = [encoding, *encoding.overflowing]
                if purpose == "query" and len(all_windows) > 1:
                    raise ProviderError("LOCAL_EMBEDDING_QUERY_TOO_LONG")
                for position, window in enumerate(all_windows):
                    count = sum(window.attention_mask)
                    weight = max(1, count - (OVERLAP if position else 0))
                    native_tokens += weight
                    windows.append((index, window.ids, weight))
            windows.sort(key=lambda row:len(row[1]))
            totals = np.zeros((len(texts),768),dtype=np.float64)
            weights = np.zeros(len(texts),dtype=np.float64)
            for start in range(0,len(windows),self.batch_size):
                check_cancelled()
                rows = windows[start:start+self.batch_size]
                width = max(len(row[1]) for row in rows)
                ids = np.full((len(rows),width),self.pad_id,dtype=np.int64)
                mask = np.zeros((len(rows),width),dtype=np.int64)
                for position,(_,tokens,_) in enumerate(rows):
                    ids[position,:len(tokens)] = tokens
                    mask[position,:len(tokens)] = 1
                feed = {"input_ids":ids,"attention_mask":mask}
                if "token_type_ids" in self.inputs:
                    feed["token_type_ids"] = np.zeros_like(ids)
                values = self.session.run(["sentence_embedding"],feed)[0]
                if values.shape != (len(rows),768) or not np.isfinite(values).all():
                    raise ProviderError("INVALID_EMBEDDING_RESPONSE")
                norms = np.linalg.norm(values,axis=1,keepdims=True)
                if not (norms>0).all():
                    raise ProviderError("INVALID_EMBEDDING_RESPONSE")
                values = values/norms
                for position,(index,_,weight) in enumerate(rows):
                    totals[index] += values[position]*weight
                    weights[index] += weight
                check_cancelled()
            values = totals/weights[:,None]
            values = values[:,:self.configuration["dimensions"]]
            norms = np.linalg.norm(values,axis=1,keepdims=True)
            if not np.isfinite(values).all() or not (norms>0).all():
                raise ProviderError("INVALID_EMBEDDING_RESPONSE")
            return (values/norms).tolist(), {"native_input_tokens":native_tokens,
                "windows":len(windows),"windowed_inputs":sum(bool(e.overflowing) for e in encoded)}


@lru_cache(maxsize=1)
def _encoder(pid, profile_json, root, threads, batch_size):
    return Encoder(json.loads(profile_json),root,threads,batch_size)


def embed(texts, *, purpose="document", check_cancelled=lambda:None):
    configuration = profile()
    started = time.monotonic()
    encoder = _encoder(os.getpid(),json.dumps(configuration,sort_keys=True),
        str(Path(settings.AI_LAB_LOCAL_EMBEDDING_DIR).expanduser().resolve()),
        settings.AI_LAB_LOCAL_EMBEDDING_THREADS,settings.AI_LAB_LOCAL_EMBEDDING_BATCH_SIZE)
    values, metadata = encoder.encode(texts,purpose,check_cancelled)
    return values, {"backend":"onnx","provider_requests":0,"paid_input_tokens":0,
        "inputs":len(texts),"latency_ms":round((time.monotonic()-started)*1000),**metadata}
