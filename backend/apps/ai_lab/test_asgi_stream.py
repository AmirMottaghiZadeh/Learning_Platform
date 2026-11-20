"""Real socket test: ASGI must flush sources before the answer finishes."""
import json
import socket
from threading import Thread
import time
from unittest.mock import patch

import httpx
import uvicorn
from django.contrib.auth import get_user_model
from django.db import transaction, connections
from django.test import TransactionTestCase, override_settings

from apps.accounts.services import issue_user_session
from . import views
from .test_durable import TEST_CACHES


@override_settings(CACHES=TEST_CACHES, AI_LAB_ENABLED=True, AI_LAB_SEARCH_ENGINE="hybrid",
                   AI_LAB_EVENT_REDIS_URL="", AI_LAB_EXECUTOR="thread", ENVIRONMENT="local",
                   AI_LAB_FEEDBACK_ENABLED=False, AI_LAB_STREAM_ANSWER_DRAFTS=False,
                   ALLOWED_HOSTS=["127.0.0.1", "localhost", "testserver"])
class ActualASGIStreamTests(TransactionTestCase):
    def test_source_event_crosses_a_real_socket_before_final_answer(self):
        from config.asgi import application
        user = get_user_model().objects.create_user("asgi-stream-owner", is_staff=True, is_superuser=True)
        with transaction.atomic():
            session = issue_user_session(user)
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        server = uvicorn.Server(uvicorn.Config(application, lifespan="off", log_level="error", access_log=False))
        thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
        def produce(*args, **kwargs):
            time.sleep(.3)
            args[6]({"part_index": 0, "question_fa": "سؤال", "article_id": "10", "citations": [
                {"source_id": "P1", "verification": "retrieved", "summary_fa": "", "quote": "Original source paragraph."}]})
            time.sleep(.5)
            return {"parts": [], "model": "luna"}
        try:
            with patch.object(views, "answer", side_effect=produce):
                thread.start()
                expires = time.monotonic() + 5
                while not server.started and time.monotonic() < expires:
                    time.sleep(.01)
                self.assertTrue(server.started)
                with httpx.Client(base_url=f"http://127.0.0.1:{port}/api/v1", timeout=5,
                                  headers={"Authorization": "Bearer " + session.access_token}) as client:
                    accepted = client.post("/ai-lab/ask/", json={"question": "سؤال دربارهٔ منبع", "model": "luna",
                        "sources": ["uptodate"], "request_id": "socket-test"})
                    self.assertEqual(accepted.status_code, 202)
                    identifier = accepted.json()["job_id"]
                    source_at, complete_at = None, None
                    with client.stream("GET", f"/ai-lab/results/{identifier}/stream/", headers={"Accept": "application/x-ndjson"}) as response:
                        self.assertEqual(response.status_code, 200)
                        for raw in response.iter_lines():
                            event = json.loads(raw)
                            if event["type"] == "sources":
                                source_at = time.monotonic()
                            if event["type"] == "complete":
                                complete_at = time.monotonic()
                    self.assertIsNotNone(source_at)
                    self.assertIsNotNone(complete_at)
                    self.assertGreater(complete_at - source_at, .25)
        finally:
            server.should_exit = True
            thread.join(timeout=5)
            sock.close()
            connections.close_all()
