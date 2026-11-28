"""Measure repeated, real SSE completions with frozen per-question payloads.

Usage (payloads may contain private source excerpts; keep them outside git):
  backend/.venv/bin/python docs/search/benchmarks/measure_provider_stream.py \
    --payloads /private/payloads.json --output /tmp/provider-timing

Read the API key from AI_LAB_API_KEY or a one-use --credential-file JSON file.
No retries, response cache, retrieval, or application queue are involved.
HTTP transport tracing stores event names/times only, never trace arguments,
authorization headers, response text, or provider error bodies.
"""
import argparse
import codecs
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit

import httpx


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def safe_write(path, data):
    descriptor = os.open(path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as handle:
        handle.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def measure(client, endpoint, payload, key, timeout):
    """Times are milliseconds from immediately before client.send()."""
    result = {'started_at_utc': utc_now(), 'trace': [], 'body_chunks': [],
              'content_events': [], 'tool_events': [], 'usage': {},
              'finish_reasons': [], 'done_received': False, 'content_chars': 0}
    started = None
    digest = hashlib.sha256()

    def elapsed():
        return round((time.perf_counter() - started) * 1000, 3)

    def trace(name, info):
        result['trace'].append({'event': name, 'at_ms': elapsed()})

    request = client.build_request('POST', endpoint, json=payload,
                                   headers={'Authorization': 'Bearer ' + key},
                                   timeout=timeout, extensions={'trace': trace})
    result['request_body_sha256'] = hashlib.sha256(request.content).hexdigest()
    result['request_body_bytes'] = len(request.content)
    response = None
    pending_lines = []
    line_buffer = ''
    decoder = codecs.getincrementaldecoder('utf-8')()

    def event(data):
        result.setdefault('first_sse_ms', elapsed())
        if data == '[DONE]':
            result['done_received'] = True
            result['done_ms'] = elapsed()
            return
        value = json.loads(data)
        if not isinstance(value, dict) or value.get('error'):
            raise ValueError('INVALID_STREAM_EVENT')
        if value.get('model'):
            result['reported_model'] = value['model']
        if isinstance(value.get('usage'), dict):
            result['usage'] = value['usage']
        for choice in value.get('choices', []):
            if choice.get('finish_reason'):
                result['finish_reasons'].append(choice['finish_reason'])
            delta = choice.get('delta') or {}
            content = delta.get('content')
            if content:
                timestamp = elapsed()
                result.setdefault('first_content_ms', timestamp)
                result['last_content_ms'] = timestamp
                result['content_chars'] += len(content)
                result['content_events'].append({'at_ms': timestamp, 'chars': len(content)})
                digest.update(content.encode())
            if delta.get('tool_calls'):
                result.setdefault('first_tool_ms', elapsed())
                result['tool_events'].append({'at_ms': elapsed(), 'count': len(delta['tool_calls'])})

    def line(value):
        if value.endswith('\r'):
            value = value[:-1]
        if value == '':
            if pending_lines:
                event('\n'.join(pending_lines))
                pending_lines.clear()
        elif value.startswith('data:'):
            pending_lines.append(value[5:].lstrip(' '))

    started = time.perf_counter()
    try:
        response = client.send(request, stream=True)
        result['headers_ms'] = elapsed()
        result['status_code'] = response.status_code
        result['http_version'] = response.http_version
        allowed_headers = ('content-type', 'content-encoding', 'server',
                           'x-accel-buffering', 'x-request-id', 'request-id',
                           'cf-ray', 'x-cache', 'x-cache-status', 'age',
                           'server-timing', 'openai-processing-ms',
                           'x-envoy-upstream-service-time', 'retry-after')
        result['response_headers'] = {name: response.headers[name]
                                      for name in allowed_headers if name in response.headers}
        if response.status_code != 200:
            result['status'] = 'http_error'
        else:
            for chunk in response.iter_bytes():
                timestamp = elapsed()
                result.setdefault('first_body_ms', timestamp)
                result['last_body_ms'] = timestamp
                result['body_chunks'].append({'at_ms': timestamp, 'bytes': len(chunk)})
                line_buffer += decoder.decode(chunk)
                while '\n' in line_buffer:
                    value, line_buffer = line_buffer.split('\n', 1)
                    line(value)
                if result['done_received']:
                    break
            line_buffer += decoder.decode(b'', final=True)
            if line_buffer:
                line(line_buffer)
            if pending_lines:
                event('\n'.join(pending_lines))
            result['status'] = 'ok' if result['done_received'] else 'incomplete'
    except (httpx.HTTPError, ValueError, UnicodeError, TypeError) as exc:
        # Exception messages can contain URLs, credentials, or provider bodies.
        result['status'] = 'error'
        result['error_type'] = type(exc).__name__
    finally:
        if response is not None:
            response.close()
        result['total_ms'] = elapsed()
        result['content_sha256'] = digest.hexdigest()

    def duration(suffix):
        starts = [t['at_ms'] for t in result['trace'] if t['event'].endswith(suffix + '.started')]
        ends = [t['at_ms'] for t in result['trace'] if t['event'].endswith(suffix + '.complete')]
        return round(sum(end - start for start, end in zip(starts, ends)), 3) if starts and ends else None

    result['tcp_connect_ms'] = duration('connect_tcp')
    result['tls_ms'] = duration('start_tls')
    result['new_connection'] = any(t['event'].endswith('connect_tcp.started') for t in result['trace'])
    upload_ends = [t['at_ms'] for t in result['trace']
                   if t['event'].endswith('send_request_body.complete')]
    result['request_uploaded_ms'] = max(upload_ends) if upload_ends else None
    if result.get('headers_ms') is not None and upload_ends:
        result['upload_to_headers_ms'] = round(result['headers_ms'] - max(upload_ends), 3)
    if result.get('first_content_ms') is not None:
        result['content_delivery_span_ms'] = round(result['last_content_ms'] - result['first_content_ms'], 3)
    if result.get('headers_ms') is not None:
        result['headers_to_end_ms'] = round(result['total_ms'] - result['headers_ms'], 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--payloads', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--credential-file', type=Path)
    parser.add_argument('--base-url', default='https://api.gapgpt.app/v1')
    parser.add_argument('--repeats', type=int, default=10)
    parser.add_argument('--timeout', type=float, default=90)
    parser.add_argument('--keepalive-seconds', type=float, default=30)
    args = parser.parse_args()
    parsed = urlsplit(args.base_url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        parser.error('An HTTPS provider URL without credentials/query/fragment is required')
    if not 1 <= args.repeats <= 10:
        parser.error('repeats must be between 1 and 10')
    args.output.mkdir(parents=True, exist_ok=True)
    report_path = args.output / 'measurements.json'
    if report_path.exists():
        parser.error('Output already exists; refusing to overwrite or silently repeat paid requests')
    key = os.environ.get('AI_LAB_API_KEY', '')
    if args.credential_file:
        key = json.loads(args.credential_file.read_text())['AI_LAB_API_KEY']
        args.credential_file.unlink()
    if not key:
        parser.error('Set AI_LAB_API_KEY or provide --credential-file')
    source = json.loads(args.payloads.read_text())
    fixtures = source['fixtures']
    for fixture in fixtures:
        payload = fixture['payload']
        assert payload['stream'] is True and payload['reasoning_effort'] == 'none'
        assert payload['model'] == 'gpt-6-luna'
        assert not re.search(r'sk-[A-Za-z0-9_-]{16,}', json.dumps(payload))
    report = {'created_at_utc': utc_now(), 'endpoint': args.base_url.rstrip('/') + '/chat/completions',
              'scope': 'provider_only_frozen_answer_stage_inputs_sequential_round_robin',
              'model': 'gpt-6-luna', 'reasoning_effort': 'none', 'stream': True,
              'planned_requests': args.repeats * len(fixtures), 'repeats_per_question': args.repeats,
              'concurrency': 1, 'automatic_retries': 0, 'timeout_seconds': args.timeout,
              'keepalive_seconds': args.keepalive_seconds,
              'connection_pool_scope': 'entire_benchmark_not_per_app_job',
              'environment_proxy_variables_present': [name for name in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY',
                   'http_proxy', 'https_proxy', 'all_proxy') if os.environ.get(name)],
              'fixtures': [{k: v for k, v in f.items() if k != 'payload'} for f in fixtures], 'runs': []}

    def save():
        assert key not in json.dumps(report, ensure_ascii=False)
        safe_write(report_path, report)

    save()
    client_options = {'timeout': args.timeout, 'follow_redirects': False,
                      'transport': httpx.HTTPTransport(retries=0),
                      'limits': httpx.Limits(max_connections=4, max_keepalive_connections=4,
                                             keepalive_expiry=args.keepalive_seconds)}
    # Explicit transport would suppress environment proxy routing; leave its
    # default construction to HTTPX (default retries=0) to match the application.
    del client_options['transport']
    with httpx.Client(**client_options) as client:
        for repeat in range(1, args.repeats + 1):
            for fixture in fixtures:
                result = measure(client, report['endpoint'], fixture['payload'], key, args.timeout)
                result.update(id=fixture['id'], repeat=repeat, sequence=len(report['runs']) + 1)
                report['runs'].append(result)
                save()
                print(json.dumps({k: result.get(k) for k in ('sequence', 'id', 'repeat', 'status',
                    'status_code', 'tcp_connect_ms', 'tls_ms', 'headers_ms', 'first_content_ms',
                    'total_ms', 'content_chars', 'finish_reasons')}, ensure_ascii=False), flush=True)
                if result.get('status_code') in (401, 403):
                    report['aborted_reason'] = 'provider_authorization_rejected'
                    save()
                    return 2
    report['finished_at_utc'] = utc_now()
    save()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
