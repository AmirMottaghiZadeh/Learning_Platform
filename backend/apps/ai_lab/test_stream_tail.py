from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import time
import httpx
from django.test import SimpleTestCase, override_settings
from .streaming import response_events


class StreamTailTests(SimpleTestCase):
    def server(self, delay):
        ports=[]
        class Handler(BaseHTTPRequestHandler):
            protocol_version="HTTP/1.1"
            def log_message(self,*args):pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length",0)))
                ports.append(self.client_address[1])
                self.send_response(200);self.send_header("Content-Type","text/event-stream")
                self.send_header("Transfer-Encoding","chunked");self.end_headers()
                body=b"data: [DONE]\n\n"
                try:
                    self.wfile.write(("%x\r\n"%len(body)).encode()+body+b"\r\n");self.wfile.flush()
                    time.sleep(delay)
                    self.wfile.write(b"0\r\n\r\n");self.wfile.flush()
                except (OSError,ValueError):self.close_connection=True
        server=ThreadingHTTPServer(("127.0.0.1",0),Handler)
        thread=Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return server,ports

    def test_completed_http_body_reuses_one_connection_for_two_sse_requests(self):
        server,ports=self.server(.02)
        with httpx.Client(timeout=3,trust_env=False) as client:
            for _ in range(2):
                with client.stream("POST",f"http://127.0.0.1:{server.server_port}",content=b"{}") as response:
                    self.assertEqual(list(response_events(response)),["[DONE]"])
        self.assertEqual(len(ports),2)
        self.assertEqual(len(set(ports)),1)

    @override_settings(AI_LAB_HTTP_DRAIN_SECONDS=.05)
    def test_logically_complete_answer_does_not_wait_for_a_stalled_http_tail(self):
        server,_=self.server(3)
        with httpx.Client(timeout=5,trust_env=False) as client:
            started=time.monotonic()
            with client.stream("POST",f"http://127.0.0.1:{server.server_port}",content=b"{}") as response:
                self.assertEqual(list(response_events(response)),["[DONE]"])
            self.assertLess(time.monotonic()-started,1.5)
