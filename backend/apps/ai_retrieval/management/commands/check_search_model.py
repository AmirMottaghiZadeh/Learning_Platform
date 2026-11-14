import json
from django.core.management.base import BaseCommand, CommandError
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.streaming import stream_chat


class Command(BaseCommand):
    help = "One bounded streaming/tool-calling capability probe, without a clinical answer or credential output."

    def handle(self, *args, **options):
        tool = {"type":"function","function":{"name":"search_references",
            "description":"Search the local medical reference database.",
            "parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":False}}}
        try:
            message, metadata = stream_chat([
                {"role":"system","content":"Call search_references for the reference question. Do not give a clinical answer."},
                {"role":"user","content":"دارودرمانی شب ادراری در کودکان چیست؟"}],
                tools=[tool],tool_choice={"type":"function","function":{"name":"search_references"}},max_tokens=768)
            calls = message.get("tool_calls",[])
            if len(calls)!=1 or calls[0]["function"]["name"]!="search_references":
                raise ProviderError("INVALID_MODEL_OUTPUT")
            arguments = json.loads(calls[0]["function"]["arguments"])
            self.stdout.write(json.dumps({"ok":True,"streaming":True,"tool_calling":True,
                "has_query":isinstance(arguments.get("query"),str),**metadata}))
        except (ProviderError,ValueError) as exc:
            raise CommandError(f"{getattr(exc,'code','INVALID_MODEL_OUTPUT')} status={getattr(exc,'status',0)}") from None
