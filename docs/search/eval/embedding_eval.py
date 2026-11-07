#!/usr/bin/env python3
"""Phase 3: compare multilingual encoders on the project's own data (ONNX, CPU).

Measures, as in the plan («روش سنجش و انتخاب»):

1. parallel: 2,000 Persian bullets of half B of pipeline_v2.db must find their
   English bullet among every distinct English bullet of half B.
2. dev: dev queries with section or paragraph judgments. Every block of the
   judged articles is encoded; blocks are ranked inside each article and a
   section scores as its best block. Article judgments: the judged candidate
   articles of a query are ranked by title.
3. drugs: the project's Persian drug names (drugs_fa.csv) must reach their
   monograph among every «…: Drug information» title.

Compression is measured on 1: shorter dimensions (models trained for it),
int8 document vectors, and a binary first pass rescored with int8.

Runs in its own environment (onnxruntime, tokenizers, numpy), one model per
process, because the laptop has 7 GB of RAM. Vectors are cached outside the
repository; UpToDate text never leaves the snapshot. Results (numbers only)
are appended to --output as JSON lines.

    ~/Documents/pharmenta-search-eval/venv-embed/bin/python docs/search/eval/embedding_eval.py \\
        --model multilingual-e5-small --models ~/Documents/pharmenta-search-eval/models \\
        --source ~/Documents/UpToDate --pipeline ~/Documents/openfda/pipeline_v2.db \\
        --cache ~/Documents/pharmenta-search-eval/embed-cache \\
        --output ~/Documents/pharmenta-search-eval/embedding-results.jsonl
"""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import random
import sys
import time

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).parent))
from apps.uptodate.search_hierarchy_source import SQLiteHierarchySource  # noqa: E402
from lexicon_parallel import bullet_pairs  # noqa: E402

EVAL = Path(__file__).parent
LEXICON = ROOT / "backend" / "apps" / "uptodate" / "search_lexicon"


def plain(prefix=""):
    return lambda title, text: prefix + (f"{title}. {text}" if title else text)


def gemma_document(title, text):
    return f"title: {title or 'none'} | text: {text}"


# pooling: "mean" or "cls" over last_hidden_state, or "sentence_embedding" (pooled in the graph).
# dims: the model card's shorter sizes (Matryoshka); others are only measured at full size.
MODELS = {
    "multilingual-e5-small": dict(file="onnx/model_quantized.onnx", pooling="mean",
                                  query="query: ", document=plain("passage: "), dims=(384,)),
    "gte-multilingual-base": dict(file="onnx/model_quantized.onnx", pooling="sentence_embedding",
                                  query="", document=plain(), dims=(768, 512, 256)),
    "arctic-embed-m-v2.0": dict(file="onnx/model_quantized.onnx", pooling="sentence_embedding",
                                query="query: ", document=plain(), dims=(768, 256)),
    # This int8 export dequantizes the whole 262k-token embedding table on every
    # run (DequantizeLinear before Gather); fold_qdq does it once at load, same numbers.
    "embeddinggemma-300m": dict(file="onnx/model_quantized.onnx", pooling="sentence_embedding",
                                query="task: search result | query: ", document=gemma_document,
                                dims=(768, 512, 256, 128), fold_qdq=True),
    "embeddinggemma-300m-q4": dict(directory="embeddinggemma-300m", file="onnx/model_q4.onnx",
                                   pooling="sentence_embedding", query="task: search result | query: ",
                                   document=gemma_document, dims=(768, 256)),
    # The same int8 weights computed as integer matmuls with int8 activations
    # (~/Documents/pharmenta-search-eval/scripts/qdq_to_integer.py), as the browser would run them.
    "embeddinggemma-300m-int8dyn": dict(directory="embeddinggemma-300m", file="onnx/model_int8_dynamic.onnx",
                                        pooling="sentence_embedding", query="task: search result | query: ",
                                        document=gemma_document, dims=(768, 256)),
    "bge-m3": dict(file="onnx/model_quantized.onnx", pooling="cls", query="", document=plain(), dims=(1024,)),
}


class Encoder:
    def __init__(self, directory, spec, threads, max_tokens):
        self.spec = spec
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        pad = self.tokenizer.token_to_id("<pad>")
        self.tokenizer.enable_padding(pad_id=pad if pad is not None else 0, pad_token="<pad>")
        self.max_tokens = max_tokens
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        if spec.get("fold_qdq"):
            options.add_session_config_entry("session.disable_quant_qdq", "1")
        self.session = ort.InferenceSession(str(directory / spec["file"]), options,
                                            providers=["CPUExecutionProvider"])
        self.inputs = {i.name for i in self.session.get_inputs()}
        self.outputs = [o.name for o in self.session.get_outputs()]
        model = directory / spec["file"]
        data = [p for p in model.parent.glob(model.name + "*")] or [model]
        if model.name == "model_int8_dynamic.onnx":
            data = [model, model.parent / "model_quantized.onnx_data"]
        self.size_mb = sum(p.stat().st_size for p in data) / 1e6

    def encode(self, texts, *, batch=16, max_tokens=None):
        self.tokenizer.enable_truncation(max_length=max_tokens or self.max_tokens)
        order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
        vectors = None
        for start in range(0, len(order), batch):
            chunk = order[start:start + batch]
            encoded = self.tokenizer.encode_batch([texts[i] for i in chunk])
            ids = np.array([e.ids for e in encoded], dtype=np.int64)
            mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)
            feed = {"input_ids": ids, "attention_mask": mask}
            if "token_type_ids" in self.inputs:
                feed["token_type_ids"] = np.zeros_like(ids)
            pooled = self._pool(dict(zip(self.outputs, self.session.run(None, feed))), mask)
            if vectors is None:
                vectors = np.zeros((len(texts), pooled.shape[1]), dtype=np.float32)
            vectors[chunk] = pooled
        return normalize(vectors)

    def _pool(self, outputs, mask):
        if self.spec["pooling"] == "sentence_embedding":
            return outputs["sentence_embedding"]
        hidden = outputs["last_hidden_state"]
        if self.spec["pooling"] == "cls":
            return hidden[:, 0]
        weights = mask[:, :, None].astype(np.float32)
        return (hidden * weights).sum(1) / np.maximum(weights.sum(1), 1e-9)


def normalize(vectors):
    return vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)


class Cache:
    """Vectors on disk, keyed by model and the exact texts."""

    def __init__(self, directory, model, encoder):
        self.directory, self.model, self.encoder = Path(directory), model, encoder
        self.directory.mkdir(parents=True, exist_ok=True)
        self.seconds = defaultdict(float)
        self.count = defaultdict(int)

    def __call__(self, name, texts, **kwargs):
        digest = hashlib.sha256("\n".join(texts).encode()).hexdigest()[:16]
        path = self.directory / f"{self.model}-{name}-{digest}.npy"
        if path.exists():
            return np.load(path)
        start = time.time()
        vectors = self.encoder.encode(texts, **kwargs)
        self.seconds[name] += time.time() - start
        self.count[name] += len(texts)
        np.save(path, vectors)
        return vectors


def ranks(scores, targets):
    """1-based rank of each row's target column."""
    target_scores = scores[np.arange(len(targets)), targets]
    return (scores > target_scores[:, None]).sum(1) + 1


def retrieval(rank):
    rank = np.asarray(rank)
    return {"r1": float((rank <= 1).mean()), "r10": float((rank <= 10).mean()), "mrr": float((1 / rank).mean())}


def parallel_texts(pipeline, sample):
    pairs = bullet_pairs(pipeline)["B"]
    english = sorted({en for en, _ in pairs})
    seen, chosen = set(), []
    shuffled = pairs[:]
    random.Random(0).shuffle(shuffled)
    for en, fa in shuffled:
        if fa not in seen and len(fa) >= 15:
            seen.add(fa)
            chosen.append((en, fa))
        if len(chosen) == sample:
            break
    index = {en: i for i, en in enumerate(english)}
    return english, [fa for _, fa in chosen], np.array([index[en] for en, _ in chosen])


def measure_parallel(spec, embed, pipeline, sample):
    english, persian, targets = parallel_texts(pipeline, sample)
    docs = embed("parallel-en", [spec["document"]("", en) for en in english], max_tokens=128)
    queries = embed("parallel-fa", [spec["query"] + fa for fa in persian], max_tokens=128)
    result = {"pool": len(english), "queries": len(persian)}
    for dim in spec["dims"]:
        q, d = normalize(queries[:, :dim]), normalize(docs[:, :dim])
        exact = q @ d.T
        row = retrieval(ranks(exact, targets))
        # int8 documents: one symmetric scale per dimension, as an index would store them.
        scale = np.abs(d).max(0) / 127
        d8 = np.round(d / scale).astype(np.int8)
        int8 = (q * scale) @ d8.T.astype(np.float32)
        row["int8"] = retrieval(ranks(int8, targets))
        # Binary first pass (Hamming on signs), then int8 rescoring of the shortlist.
        # Signs are taken around the documents' mean vector: some models put every
        # vector in one narrow cone, where raw signs carry little.
        center = d.mean(0)
        signs_q = np.where(q > center, 1.0, -1.0).astype(np.float32)
        signs_d = np.where(d > center, 1.0, -1.0).astype(np.float32)
        hamming = (dim - signs_q @ signs_d.T) / 2
        top_exact = np.argsort(-exact, 1)[:, :10]
        for shortlist in (100, 200):
            keep = np.argsort(hamming, 1, kind="stable")[:, :shortlist]
            rescored = np.full_like(exact, -np.inf)
            rows = np.arange(len(q))[:, None]
            rescored[rows, keep] = int8[rows, keep]
            top = np.argsort(-rescored, 1)[:, :10]
            overlap = np.mean([len(set(a) & set(b)) / 10 for a, b in zip(top, top_exact)])
            row[f"binary{shortlist}"] = {**retrieval(ranks(rescored, targets)), "top10_overlap": float(overlap)}
        result[str(dim)] = row
    return result


def load_dev():
    queries = {r["query_id"]: r for r in csv.DictReader((EVAL / "dev-queries.csv").open(encoding="utf-8"))}
    judgments = list(csv.DictReader((EVAL / "dev-judgments.csv").open(encoding="utf-8")))
    return queries, judgments


def measure_dev(spec, embed, source):
    queries, judgments = load_dev()
    deep = [j for j in judgments if j["level"] in ("section", "paragraph") and int(j["grade"]) > 0]
    articles = sorted({j["article_id"] for j in deep})
    with SQLiteHierarchySource(source) as snapshot:
        blocks = {a: snapshot.load_article(a)[0].blocks for a in articles}
        titles = {a.article_id: a.title for a in snapshot.catalog.articles}
    flat = [(a, b) for a in articles for b in blocks[a]]
    doc_vectors = embed("dev-blocks", [spec["document"](b.section_title, b.text) for _, b in flat], max_tokens=256)
    position = {(a, b.paragraph_id): i for i, (a, b) in enumerate(flat)}
    query_ids = sorted({j["query_id"] for j in judgments})
    query_vectors = dict(zip(query_ids, embed("dev-queries", [spec["query"] + queries[q]["query"] for q in query_ids],
                                                max_tokens=64)))
    result = {}
    for level in ("section", "paragraph"):
        groups = defaultdict(dict)
        for j in deep:
            if j["level"] == level:
                groups[j["query_id"], j["article_id"]][j["section_id"] if level == "section" else j["paragraph_id"]] = \
                    int(j["grade"])
        found = []
        for (query, article), grades in groups.items():
            rows = [position[article, b.paragraph_id] for b in blocks[article]]
            scores = doc_vectors[rows] @ query_vectors[query]
            if level == "section":
                best = defaultdict(lambda: -1.0)
                for b, s in zip(blocks[article], scores):
                    best[b.section_id] = max(best[b.section_id], float(s))
                ranked = sorted(best, key=best.get, reverse=True)
            else:
                ranked = [blocks[article][i].paragraph_id for i in np.argsort(-scores)]
            top = max(grades.values())
            found.append(next(i for i, key in enumerate(ranked, 1) if grades.get(key, 0) == top))
        rank = np.array(found)
        result[level] = {"groups": len(found), "hit1": float((rank <= 1).mean()), "hit3": float((rank <= 3).mean()),
                         "hit5": float((rank <= 5).mean()), "mrr": float((1 / rank).mean())}
    # Articles: the judged candidates of each query ranked by title.
    by_query = defaultdict(dict)
    for j in judgments:
        if j["level"] == "article":
            by_query[j["query_id"]][j["article_id"]] = int(j["grade"])
    candidates = sorted({a for grades in by_query.values() for a in grades if a in titles})
    title_vectors = dict(zip(candidates, embed("dev-titles", [spec["document"]("", titles[a]) for a in candidates],
                                               max_tokens=64)))
    ndcg, top1 = [], []
    for query, grades in by_query.items():
        grades = {a: g for a, g in grades.items() if a in title_vectors}
        if len(grades) < 2 or max(grades.values()) == 0:
            continue
        ranked = sorted(grades, key=lambda a: -float(title_vectors[a] @ query_vectors[query]))
        gain = sum((2 ** grades[a] - 1) / np.log2(i + 2) for i, a in enumerate(ranked))
        ideal = sum((2 ** g - 1) / np.log2(i + 2) for i, g in enumerate(sorted(grades.values(), reverse=True)))
        ndcg.append(gain / ideal)
        top1.append(grades[ranked[0]] == max(grades.values()))
    result["article_by_title"] = {"queries": len(ndcg), "ndcg": float(np.mean(ndcg)), "top1_best": float(np.mean(top1))}
    return result


def measure_drugs(spec, embed, source):
    with SQLiteHierarchySource(source) as snapshot:
        monographs = {a.article_id: a.title for a in snapshot.catalog.articles if a.title.endswith(": Drug information")}
    ids = sorted(monographs)
    names = [r for r in csv.DictReader((LEXICON / "drugs_fa.csv").open(encoding="utf-8"))
             if r["status"] == "project" and r["article_id"] in monographs]
    docs = embed("drug-titles", [spec["document"]("", monographs[a]) for a in ids], max_tokens=32)
    queries = embed("drug-names", [spec["query"] + r["fa"] for r in names], max_tokens=32)
    targets = np.array([ids.index(r["article_id"]) for r in names])
    return {"pool": len(ids), "names": len(names), **retrieval(ranks(queries @ docs.T, targets))}


def measure_speed(encoder, spec, repeats=50):
    queries = ["دوز سفتریاکسون در نارسایی کلیه", "عوارض متفورمین", "treatment of community acquired pneumonia",
               "تداخل وارفارین و آسپرین در سالمندان", "پنومونی"]
    timings = []
    for i in range(repeats):
        start = time.perf_counter()
        encoder.encode([spec["query"] + queries[i % len(queries)]], batch=1, max_tokens=64)
        timings.append((time.perf_counter() - start) * 1000)
    timings = sorted(timings[5:])
    return {"query_ms_p50": timings[len(timings) // 2], "query_ms_p95": timings[int(len(timings) * 0.95)]}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", choices=sorted(MODELS), required=True)
    parser.add_argument("--models", type=Path, required=True, help="directory of downloaded models")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--pipeline", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=2000)
    parser.add_argument("--threads", type=int, default=6)
    parser.add_argument("--only", choices=("parallel", "dev", "drugs", "speed"), action="append")
    args = parser.parse_args()
    spec = MODELS[args.model]
    encoder = Encoder(args.models / spec.get("directory", args.model), spec, args.threads, 256)
    embed = Cache(args.cache, args.model, encoder)
    result = {"model": args.model, "file": spec["file"], "size_mb": round(encoder.size_mb, 1),
              "dim": int(encoder.encode(["x"]).shape[1]), "threads": args.threads}
    steps = {"speed": lambda: measure_speed(encoder, spec),
             "drugs": lambda: measure_drugs(spec, embed, args.source),
             "dev": lambda: measure_dev(spec, embed, args.source),
             "parallel": lambda: measure_parallel(spec, embed, args.pipeline, args.sample)}
    for name in args.only or steps:
        start = time.time()
        result[name] = steps[name]()
        print(f"{args.model} {name} ({time.time() - start:.0f}s): {json.dumps(result[name])}", flush=True)
    result["encode_per_text_ms"] = {k: round(embed.seconds[k] / embed.count[k] * 1000, 1) for k in embed.count}
    with args.output.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(result) + "\n")


if __name__ == "__main__":
    main()
