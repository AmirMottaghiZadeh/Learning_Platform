#!/usr/bin/env python3
"""Measure smart-search admission and answer latency under load.

One credential = one simulated user, because the API allows a single active
search per account. Give it tokens (or usernames/passwords) and it submits one
question per credential as close to simultaneously as possible, reports how
many were admitted, how many queued and where, then follows every job to a
terminal status.

    python tools/smart_search_load_test.py --base-url https://api.example/api/v1 \
        --tokens-file /secure/tokens.json --count 20

    # credentials by login instead of tokens
    python tools/smart_search_load_test.py --login alice:secret --login bob:secret

Only stdlib, so it runs on a server without the app's virtualenv.
"""
import argparse
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

QUESTIONS = [
    "What is the first-line treatment for uncomplicated hypertension?",
    "Which antibiotics are recommended for community-acquired pneumonia?",
    "How is diabetic ketoacidosis managed in the emergency department?",
    "What are the criteria for diagnosing acute pancreatitis?",
    "When should anticoagulation be started in atrial fibrillation?",
    "How do you treat an acute exacerbation of COPD?",
    "What is the workup for a patient with suspected pulmonary embolism?",
    "When is surgery indicated in ulcerative colitis?",
    "How is acute decompensated heart failure treated?",
    "What is the approach to a patient with syncope?",
]


def call(method, url, token=None, body=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Accept", "application/json")
    if data is not None:
        request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
            status = response.status
    except urllib.error.HTTPError as error:
        payload = error.read()
        status = error.code
    except Exception as error:  # the report needs the failure text
        return {"status": "ERROR", "elapsed": time.monotonic() - started, "body": f"{type(error).__name__}: {error}"}
    elapsed = time.monotonic() - started
    try:
        parsed = json.loads(payload or b"{}")
    except ValueError:
        parsed = {}
    return {"status": status, "elapsed": elapsed, "body": parsed}


def login(base, credential, timeout):
    username, _, password = credential.partition(":")
    result = call("POST", f"{base}/auth/login/", body={"username": username, "password": password}, timeout=timeout)
    body = result.get("body") or {}
    token = body.get("access_token") or body.get("access") if isinstance(body, dict) else None
    if not token:
        raise SystemExit(f"login failed for {username}: {result['status']} {body}")
    return token


def percentile(values, share):
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round(share * (len(ordered) - 1))))
    return round(ordered[index], 2)


def submit_all(base, credentials, questions, timeout):
    results = [None] * len(credentials)
    barrier = threading.Barrier(len(credentials))

    def worker(index):
        token = credentials[index]
        question = questions[index % len(questions)]
        request_id = f"load-{index}-{int(time.time() * 1000)}"
        barrier.wait()
        results[index] = call("POST", f"{base}/ai-lab/ask/", token=token, timeout=timeout,
                              body={"question": question, "model": "luna", "sources": ["uptodate"],
                                    "request_id": request_id})

    threads = [threading.Thread(target=worker, args=(index,), daemon=True) for index in range(len(credentials))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return results


def follow(base, token, identifier, deadline, timeout):
    """Poll until the job leaves `running`; returns (status, seconds, error, last stage)."""
    started = time.monotonic()
    last_stage = None
    while time.monotonic() - started < deadline:
        result = call("GET", f"{base}/ai-lab/results/{identifier}/", token=token, timeout=timeout)
        body = result.get("body") or {}
        if result["status"] == 200:
            last_stage = body.get("stage") or last_stage
            if body.get("status") != "running":
                return body.get("status"), time.monotonic() - started, (body.get("error") or {}).get("code"), last_stage
        elif result["status"] not in (404, 429):
            return "error", time.monotonic() - started, body.get("code") or str(result["status"]), last_stage
        time.sleep(1.0)
    return "timeout", time.monotonic() - started, None, last_stage


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--token", action="append", default=[], help="access token (repeatable)")
    parser.add_argument("--tokens-file", help="JSON list of tokens or [{\"token\": ...}]")
    parser.add_argument("--login", action="append", default=[], help="user:password (repeatable)")
    parser.add_argument("--count", type=int, help="how many simulated users (default: all credentials)")
    parser.add_argument("--questions-file", help="one question per line; defaults to built-in clinical questions")
    parser.add_argument("--deadline", type=float, default=600.0, help="seconds to wait for each answer")
    parser.add_argument("--timeout", type=float, default=30.0, help="HTTP timeout per call")
    parser.add_argument("--json-out", help="write the summary as JSON here")
    options = parser.parse_args()

    credentials = list(options.token)
    if options.tokens_file:
        with open(options.tokens_file) as handle:
            loaded = json.load(handle)
        credentials += [item["token"] if isinstance(item, dict) else item for item in loaded]
    credentials += [login(options.base_url, pair, options.timeout) for pair in options.login]
    if not credentials:
        raise SystemExit("give at least one --token, --tokens-file or --login")
    if options.count:
        credentials = credentials[: options.count]

    questions = QUESTIONS
    if options.questions_file:
        with open(options.questions_file) as handle:
            questions = [line.strip() for line in handle if line.strip()]

    print(f"users={len(credentials)} base={options.base_url} at={datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    burst = submit_all(options.base_url, credentials, questions, options.timeout)
    submit_times = [r["elapsed"] for r in burst]
    buckets = {}
    accepted = []
    for index, result in enumerate(burst):
        key = str(result["status"])
        buckets[key] = buckets.get(key, 0) + 1
        if result["status"] == 202:
            accepted.append((index, result))
    print(f"submit: codes={buckets} wall_p50={percentile(submit_times, .5)}s "
          f"p95={percentile(submit_times, .95)}s max={round(max(submit_times), 2) if submit_times else '-'}s")
    queued = [r["body"].get("queue_position") for _, r in accepted
              if isinstance(r["body"], dict) and r["body"].get("queue_position")]
    if queued:
        print(f"queued_at_submit={len(queued)} positions={sorted(queued)[:20]}{' ...' if len(queued) > 20 else ''}")

    finished = []
    lock = threading.Lock()

    def follow_one(index, result):
        identifier = (result["body"] or {}).get("job_id") if isinstance(result["body"], dict) else None
        if not identifier:
            entry = (index, "no_job_id", 0.0, None, None)
        else:
            status, seconds, error, stage = follow(options.base_url, credentials[index], identifier,
                                                   options.deadline, options.timeout)
            entry = (index, status, seconds, error, stage)
        with lock:
            finished.append(entry)

    if accepted:
        threads = [threading.Thread(target=follow_one, args=(index, result), daemon=True) for index, result in accepted]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    durations = [entry[2] for entry in finished if entry[1] == "complete"]
    outcomes = {}
    for entry in finished:
        outcomes[entry[1]] = outcomes.get(entry[1], 0) + 1
    print(f"answers: outcomes={outcomes} complete_p50={percentile(durations, .5)}s "
          f"p95={percentile(durations, .95)}s max={round(max(durations), 1) if durations else '-'}s")
    for entry in sorted(finished):
        if entry[1] != "complete":
            print(f"  user{entry[0]} {entry[1]} after {round(entry[2], 1)}s error={entry[3]} last_stage={entry[4]}")

    if options.json_out:
        summary = {
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "users": len(credentials),
            "submit_codes": buckets,
            "submit_p50": percentile(submit_times, .5),
            "submit_p95": percentile(submit_times, .95),
            "outcomes": outcomes,
            "complete_p50": percentile(durations, .5),
            "complete_p95": percentile(durations, .95),
            "complete_mean": round(statistics.mean(durations), 2) if durations else None,
            "queued_positions": sorted(queued),
        }
        with open(options.json_out, "w") as handle:
            json.dump(summary, handle, ensure_ascii=False, indent=2)
        print(f"summary written to {options.json_out}")

    return 0 if all(entry[1] == "complete" for entry in finished) or not finished else 1


if __name__ == "__main__":
    sys.exit(main())
