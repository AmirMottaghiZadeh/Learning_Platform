"""Only job IDs enter the broker; prompts/results are encrypted in durable state."""
from base64 import urlsafe_b64encode
from hashlib import sha256
import json
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.utils.crypto import salted_hmac
from django.views.decorators.debug import sensitive_variables
from .provider import ProviderError


@sensitive_variables()
def encode(value):
    key = urlsafe_b64encode(sha256(("ai-search-jobs:" + settings.SECRET_KEY).encode()).digest())
    return Fernet(key).encrypt(json.dumps(value, ensure_ascii=False).encode()).decode()


@sensitive_variables()
def decode(value):
    try:
        key = urlsafe_b64encode(sha256(("ai-search-jobs:" + settings.SECRET_KEY).encode()).digest())
        result = json.loads(Fernet(key).decrypt(value.encode()))
        if not isinstance(result,dict):
            raise ValueError
        return result
    except (InvalidToken,ValueError,TypeError,UnicodeError):
        raise ProviderError("SEARCH_JOB_STATE_UNAVAILABLE") from None


def digest(payload):
    return salted_hmac("ai-search-idempotency",json.dumps(payload,ensure_ascii=False,sort_keys=True),algorithm="sha256").hexdigest()


def snapshot(run):
    payload=decode(run.encrypted_payload)
    result=decode(run.encrypted_result) if run.encrypted_result else {}
    active=run.status in {"admitting","queued","running"}
    return {"user_id":run.owner_id,"question":payload["question"],"model":payload["model"],
        "sources":payload["sources"],"pipeline":"hybrid-v1","slot":run.slot,
        "status":"running" if active else run.status,
        "stage":"queued" if run.status in {"admitting","queued"} else "starting",
        "created_at":run.created_at.timestamp(),
        "heartbeat_at":(run.heartbeat_at or run.created_at).timestamp(),
        "revision":0,"findings":[],"workflow":[],"stages_seen":[],**result}
