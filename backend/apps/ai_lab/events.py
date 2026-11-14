"""Account-scoped callers use ordered, replayable events. No provider credentials."""
from collections import deque
from functools import lru_cache
import json
import re
from threading import Condition
import time
import uuid
import asyncio
from weakref import WeakKeyDictionary

from django.conf import settings
import redis
import redis.asyncio
from .provider import ProviderError

TTL=900
LIMIT=2048
_condition=Condition()
_memory={}
_async_clients=WeakKeyDictionary()


@lru_cache(maxsize=4)
def _redis(url):
    return redis.Redis.from_url(url,decode_responses=True,socket_connect_timeout=2,socket_timeout=3)


def _async_redis(url):
    clients = _async_clients.setdefault(asyncio.get_running_loop(), {})
    if url not in clients:
        clients[url] = redis.asyncio.Redis.from_url(url,decode_responses=True,socket_connect_timeout=2,socket_timeout=3)
    return clients[url]


def _key(job_id):
    return "ai-search:events:"+str(uuid.UUID(str(job_id)))


def _local_allowed():
    if settings.ENVIRONMENT!="local" and not settings.RUNNING_TESTS:
        raise ProviderError("SEARCH_EVENT_STORE_REQUIRED")


def append(job_id,event):
    value=json.dumps(event,ensure_ascii=False)
    if len(value.encode())>1_000_000 or re.search(r"sk-[A-Za-z0-9_-]{16,}|Bearer\s+\S+",value):
        raise ProviderError("UNSAFE_SEARCH_EVENT")
    key=_key(job_id)
    if settings.AI_LAB_EVENT_REDIS_URL:
        script="""local n=redis.call('INCR',KEYS[2]); redis.call('XADD',KEYS[1],'MAXLEN','=',ARGV[2],n..'-0','data',ARGV[1]); redis.call('EXPIRE',KEYS[1],ARGV[3]); redis.call('EXPIRE',KEYS[2],ARGV[3]); return n"""
        try:
            return int(_redis(settings.AI_LAB_EVENT_REDIS_URL).eval(script,2,key,key+":sequence",value,LIMIT,TTL))
        except redis.RedisError:
            raise ProviderError("SEARCH_EVENT_STORE_UNAVAILABLE") from None
    _local_allowed()
    with _condition:
        now=time.monotonic()
        for expired in [k for k,v in _memory.items() if v["expires"]<now]:
            del _memory[expired]
        journal=_memory.setdefault(key,{"sequence":0,"rows":deque(maxlen=LIMIT),"expires":now+TTL})
        journal["sequence"]+=1;journal["expires"]=now+TTL
        journal["rows"].append((journal["sequence"],json.loads(value)))
        _condition.notify_all()
        return journal["sequence"]


def _decode(rows):
    result=[]
    for _,entries in rows:
        for identifier,fields in entries:
            value=json.loads(fields["data"])
            result.append({**value,"sequence":int(identifier.split("-",1)[0])})
    return result


def read(job_id,after=0,*,block_ms=1000):
    if settings.AI_LAB_EVENT_REDIS_URL:
        try:
            rows=_redis(settings.AI_LAB_EVENT_REDIS_URL).xread({_key(job_id):f"{after}-0"},count=100,block=block_ms or None)
            return _decode(rows)
        except (redis.RedisError,ValueError,KeyError):
            raise ProviderError("SEARCH_EVENT_STORE_UNAVAILABLE") from None
    _local_allowed()
    with _condition:
        key=_key(job_id)
        def pending():
            journal=_memory.get(key)
            if not journal or journal["expires"]<time.monotonic():
                return []
            return [{**event,"sequence":n} for n,event in journal["rows"] if n>after][:100]
        rows=pending()
        if not rows and block_ms:
            _condition.wait(block_ms/1000)
            rows=pending()
        return rows


async def read_async(job_id,after=0,*,block_ms=1000):
    if settings.AI_LAB_EVENT_REDIS_URL:
        try:
            rows=await _async_redis(settings.AI_LAB_EVENT_REDIS_URL).xread({_key(job_id):f"{after}-0"},count=100,block=block_ms or None)
            return _decode(rows)
        except (redis.RedisError,ValueError,KeyError):
            raise ProviderError("SEARCH_EVENT_STORE_UNAVAILABLE") from None
    import asyncio
    return await asyncio.to_thread(read,job_id,after,block_ms=block_ms)


def last_sequence(job_id):
    if settings.AI_LAB_EVENT_REDIS_URL:
        try:
            return int(_redis(settings.AI_LAB_EVENT_REDIS_URL).get(_key(job_id)+":sequence") or 0)
        except redis.RedisError:
            raise ProviderError("SEARCH_EVENT_STORE_UNAVAILABLE") from None
    _local_allowed()
    with _condition:
        return _memory.get(_key(job_id),{}).get("sequence",0)
