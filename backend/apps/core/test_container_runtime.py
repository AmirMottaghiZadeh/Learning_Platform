import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from unittest import skipUnless
from unittest.mock import patch

from django.test import SimpleTestCase

import container_runtime


@skipUnless(os.name == "posix", "Container process groups require POSIX")
class CombinedRuntimeTests(SimpleTestCase):
    def launch(self, directory, *, exit_mode="exit", stubborn_web=False, missing_worker=False):
        root=Path(directory)
        child=root/"child.py"
        child.write_text('''import os, signal, sys, time
from pathlib import Path
root=Path(sys.argv[1]); name=sys.argv[2]; mode=sys.argv[3]
def stop(sig, frame):
    (root/(name+".stopped")).write_text("stopped")
    raise SystemExit(0)
signal.signal(signal.SIGTERM, signal.SIG_IGN if mode=="ignore" else stop)
(root/(name+".ready")).write_text(str(os.getpid()))
if mode in {"exit", "clean-exit"}:
    end=time.monotonic()+4
    while not all((root/(n+".ready")).exists() for n in ("web","search","platform")):
        if time.monotonic()>end: raise SystemExit(99)
        time.sleep(.01)
    raise SystemExit(23 if mode=="exit" else 0)
while True: time.sleep(.02)
''')
        modes={"web":"ignore" if stubborn_web else "wait", "search":exit_mode, "platform":"wait"}
        commands=[(name,[sys.executable,str(child),str(root),name,mode]) for name,mode in modes.items()]
        if missing_worker:
            commands[1]=("search",[str(root/"missing-command")])
        code="import json,sys; from container_runtime import supervise; raise SystemExit(supervise(json.loads(sys.argv[1]), shutdown_seconds=.2))"
        return subprocess.Popen([sys.executable,"-c",code,json.dumps(commands)],
            cwd=Path(container_runtime.__file__).parent,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

    def finish(self, process):
        try:
            return process.communicate(timeout=8)
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill(); process.communicate()

    def test_worker_failure_stops_web_and_platform_worker_and_fails_container(self):
        with TemporaryDirectory() as directory:
            process=self.launch(directory)
            output,error=self.finish(process)
            self.assertEqual(process.returncode,23,(output,error))
            self.assertTrue((Path(directory)/"web.stopped").exists())
            self.assertTrue((Path(directory)/"platform.stopped").exists())

    def test_unexpected_successful_exit_still_fails_container(self):
        with TemporaryDirectory() as directory:
            process=self.launch(directory,exit_mode="clean-exit")
            self.finish(process)
            self.assertEqual(process.returncode,1)

    def test_sigterm_is_forwarded_and_all_processes_exit_cleanly(self):
        with TemporaryDirectory() as directory:
            process=self.launch(directory,exit_mode="wait")
            try:
                end=time.monotonic()+4
                while not all((Path(directory)/(n+".ready")).exists() for n in ("web","search","platform")):
                    if process.poll() is not None or time.monotonic()>end:
                        self.fail("Runtime failed to start all children")
                    time.sleep(.01)
                process.send_signal(signal.SIGTERM)
            finally:
                self.finish(process)
            self.assertEqual(process.returncode,0)
            for name in ("web","search","platform"):
                self.assertTrue((Path(directory)/(name+".stopped")).exists())

    def test_grace_timeout_kills_a_child_ignoring_sigterm(self):
        with TemporaryDirectory() as directory:
            process=self.launch(directory,stubborn_web=True)
            output,error=self.finish(process)
            self.assertEqual(process.returncode,23,(output,error))
            pid=int((Path(directory)/"web.ready").read_text())
            with self.assertRaises(ProcessLookupError):
                os.kill(pid,0)

    def test_spawn_failure_cleans_up_already_started_process(self):
        with TemporaryDirectory() as directory:
            process=self.launch(directory,missing_worker=True)
            output,error=self.finish(process)
            self.assertEqual(process.returncode,1,(output,error))
            self.assertIn("process start failed: FileNotFoundError",output)
            pid=int(output.split("web pid=",1)[1].splitlines()[0])
            with self.assertRaises(ProcessLookupError):
                os.kill(pid,0)

    def test_search_and_platform_queues_have_distinct_workers(self):
        commands=dict(container_runtime.commands({"AI_LAB_WORKER_CONCURRENCY":"3"}))
        search=commands["search-worker"]; platform=commands["platform-worker"]
        self.assertEqual(search[search.index("-Q")+1],"ai_search")
        self.assertEqual(search[search.index("-c")+1],"3")
        self.assertEqual(platform[platform.index("-Q")+1],"default,events,maintenance")
        self.assertEqual(platform[platform.index("-c")+1],"1")
        self.assertNotIn("ai_indexing",platform)

    def test_invalid_runtime_configuration_does_not_start_children_or_log_value(self):
        for values in ({"AI_LAB_WORKER_CONCURRENCY":"0"},
                       {"AI_LAB_WORKER_CONCURRENCY":"1; unsafe"},
                       {"AI_LAB_WORKER_SHUTDOWN_SECONDS":"invalid-sensitive-value"}):
            with self.subTest(values=values), patch.dict(os.environ,values,clear=True), \
                    patch.object(container_runtime,"supervise") as run, patch("builtins.print") as log:
                self.assertEqual(container_runtime.main(),1)
                run.assert_not_called()
                self.assertEqual(log.call_args.args[0],"[container-runtime] invalid worker runtime configuration")
