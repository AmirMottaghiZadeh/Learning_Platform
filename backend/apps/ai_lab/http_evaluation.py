"""Authenticated ask/poll traffic measurements; never follow token-bearing redirects."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import threading
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener

from . import evaluation
from .provider import NoRedirect


def load_accounts(path):
    path = Path(path)
    if path.stat().st_mode & 0o077:
        raise evaluation.EvaluationError("ACCOUNT_FILE_PERMISSIONS")
    data = json.loads(path.read_text())
    accounts = data.get("accounts", [])
    if data.get("schema") != 1 or not isinstance(accounts, list) or not accounts:
        raise evaluation.EvaluationError("INVALID_ACCOUNTS")
    tokens = [account.get("access_token") for account in accounts if isinstance(account, dict)]
    if len(tokens) != len(accounts) or any(not isinstance(token, str) or not re.fullmatch(r"phx_access_[A-Za-z0-9_-]{20,}", token) for token in tokens):
        raise evaluation.EvaluationError("INVALID_ACCOUNTS")
    return accounts


class Client:
    def __init__(self, base, token, *, timeout=25, poll=1):
        parsed = urlsplit(base)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or (parsed.scheme == "http" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"})):
            raise evaluation.EvaluationError("INVALID_API_BASE_URL")
        self.base, self.token, self.timeout, self.poll = base.rstrip("/"), token, timeout, poll

    def json(self, path, payload=None):
        request = Request(self.base + path, data=None if payload is None else json.dumps(payload).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            method="GET" if payload is None else "POST")
        status = 200
        try:
            with build_opener(NoRedirect).open(request, timeout=self.timeout) as response:
                status = response.status
                raw = response.read(4000001)
        except HTTPError as error:
            status = error.code
            raw = error.read(100001)
        if len(raw) > 4000000 or self.token.encode() in raw or re.search(rb"sk-[A-Za-z0-9_-]{16,}", raw):
            raise evaluation.EvaluationError("UNSAFE_API_RESPONSE")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise evaluation.EvaluationError("INVALID_API_RESPONSE")
        return status, data

    def run(self, case, bindings, configuration):
        started = time.perf_counter()
        row = {"case_id": case["id"], "question": case["question"], "expect": case["expect"],
            "category": case.get("category", "unspecified"), "expected_sources": bindings}
        try:
            status, data = self.json("/ai-lab/ask/", {"question": case["question"], "history": case.get("history", []),
                                                   "model": "luna", "sources": ["uptodate"]})
            row["admission_status"] = status
            if status != 202:
                row.update(status="failed", error_code=data.get("code", "ADMISSION_FAILED"))
            else:
                job = data["job_id"]
                while time.perf_counter() - started <= self.timeout:
                    status, data = self.json(f"/ai-lab/results/{job}/")
                    if status != 200:
                        row.update(status="failed", error_code=data.get("code", "POLL_FAILED"))
                        break
                    if data.get("status") != "running":
                        row.update(status=data.get("status", "failed"), metrics=data.get("metrics", {}))
                        if data.get("result") is not None:
                            row["result"] = data["result"]
                        if data.get("error"):
                            row["error_code"] = data["error"]["code"]
                        break
                    time.sleep(self.poll)
                else:
                    row.update(status="failed", error_code="CLIENT_POLL_TIMEOUT")
        except Exception:
            row.update(status="failed", error_code="HTTP_EVALUATION_FAILED")
        row["client_elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        row.setdefault("metrics", {})
        row["response_digest_schema"] = 2
        row["response_digest"] = evaluation.clinical_digest(case, bindings, configuration, row.get("result"), row.get("error_code"))
        return row


def run_load(cases, accounts, base, configuration, evidence, *, concurrency=2, poll=1, max_requests=100):
    if not 1 <= concurrency <= min(16, len(accounts)) or not .05 <= poll <= 5:
        raise evaluation.EvaluationError("INVALID_LOAD_CONFIGURATION")
    bindings = {case["id"]: evidence.bind(case) for case in cases}
    work = list(enumerate(cases))
    lock, next_index = threading.Lock(), [0]
    evidence_lock = threading.Lock()
    condition = threading.Condition()
    ledger = {"used": 0, "reserved": 0}
    samples, runtime = [], []
    reservation = configuration["max_provider_requests"]

    def run_guarded(client, case, scenario):
        with condition:
            while ledger["used"] + ledger["reserved"] + reservation > max_requests and ledger["reserved"]:
                condition.wait(.1)
            if ledger["used"] + ledger["reserved"] + reservation > max_requests:
                return None
            ledger["reserved"] += reservation
        row = client.run(case, bindings[case["id"]], configuration)
        row["scenario"] = scenario
        with condition:
            # Unknown/unfetchable worker usage consumes the whole reservation.
            used = row.get("metrics", {}).get("provider_requests", reservation)
            ledger["used"] += used if type(used) is int and 0 <= used <= reservation else reservation
            ledger["reserved"] -= reservation
            condition.notify_all()
        with evidence_lock:
            row["assessment"] = evaluation.assess(case, row.get("result", {}), bindings[case["id"]], evidence)
        return row

    def worker(number):
        available = accounts[number::concurrency]
        served = 0
        while True:
            with lock:
                if next_index[0] >= len(work):
                    return
                _, case = work[next_index[0]]
                next_index[0] += 1
            client = Client(base, available[(served // 8) % len(available)]["access_token"], poll=poll)
            served += 1
            # At most one active request for each of these authenticated accounts.
            cold = run_guarded(client, case, "cold")
            if cold is None:
                return
            with lock:
                samples.append(cold)
            if cold["status"] == "complete" and cold["assessment"].get("machine_complete"):
                warm = run_guarded(client, case, "hit")
                if warm is not None:
                    with lock:
                        samples.append(warm)
            status, data = client.json("/ai-lab/status/?diagnostics=1")
            if status == 200 and data.get("runtime"):
                with lock:
                    runtime.append(data["runtime"])
    # Partitioning workers across several account groups avoids exceeding the
    # ordinary hourly cap; no rate-limit bypass or production config override.
    if len(cases) > min(len(accounts[number::concurrency]) * 8 for number in range(concurrency)) * concurrency:
        raise evaluation.EvaluationError("LOAD_ACCOUNTS_WOULD_EXCEED_HOURLY_CAP")
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        list(pool.map(worker, range(concurrency)))
    return {"runs": samples, "provider_request_upper_bound_used": ledger["used"], "runtime": runtime}
