import os
import json
from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory

from django.conf import settings
from django.test import SimpleTestCase
from unittest import skipUnless


@skipUnless(shutil.which("bash"),"Container entrypoint uses bash")
class ContainerRoleTests(SimpleTestCase):
    def run_entrypoint(self, role, concurrency="2"):
        with TemporaryDirectory() as directory:
            for command in ("python","celery"):
                file=Path(directory)/command
                file.write_text('#!/bin/sh\nprintf "%s\\n" "'+command+' $*"\n')
                file.chmod(0o700)
            env={**os.environ,"PATH":directory+os.pathsep+os.environ["PATH"],
                 "SERVICE_ROLE":role,"AI_LAB_WORKER_CONCURRENCY":concurrency}
            return subprocess.run([shutil.which("bash"),str(settings.BASE_DIR/"docker-start.sh")],
                env=env,capture_output=True,text=True,timeout=5)

    def test_worker_role_uses_same_image_and_only_consumes_the_search_queue(self):
        result=self.run_entrypoint("ai-search-worker","3")
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("celery -A config worker -Q ai_search -c 3 --prefetch-multiplier 1",result.stdout)
        self.assertNotIn("manage.py migrate",result.stdout)
        self.assertNotIn("uvicorn",result.stdout)

    def test_invalid_role_or_concurrency_stops_before_migrations_or_worker(self):
        for role,concurrency in [("invalid","2"),("ai-search-worker","0"),("ai-search-worker","100"),
                                 ("ai-search-worker","2; exit 0")]:
            with self.subTest(role=role,concurrency=concurrency):
                result=self.run_entrypoint(role,concurrency)
                self.assertEqual(result.returncode,1)
                self.assertNotIn("manage.py migrate",result.stdout)
                self.assertNotIn("celery -A",result.stdout)

    def run_redis(self, password):
        with TemporaryDirectory() as directory:
            path=Path(directory)
            entry=path/"entrypoint"
            entry.write_text('''#!/usr/bin/env python3
import json, os, pathlib, sys
p=pathlib.Path(sys.argv[2]); text=p.read_text()
result={"private":p.stat().st_mode & 0o777 == 0o600,
        "password":("requirepass "+os.environ["REDIS_PASSWORD"]+"\\n") in text,
        "persistent":"appendonly yes\\n" in text,
        "noeviction":"maxmemory-policy noeviction\\n" in text}
p.unlink(); print(json.dumps(result))
''')
            entry.chmod(0o700)
            # Exercise the unprivileged container path; image entrypoint owns
            # the real root -> redis user transition in production.
            identity=path/"id";identity.write_text('#!/bin/sh\necho 1000\n');identity.chmod(0o700)
            source=settings.BASE_DIR.parent/"deploy/runflare/redis-start.sh"
            script=path/"start.sh"
            script.write_text(source.read_text().replace("/usr/local/bin/docker-entrypoint.sh",str(entry)))
            return subprocess.run(["/bin/sh",str(script)],env={**os.environ,"REDIS_PASSWORD":password,
                "PATH":directory+os.pathsep+os.environ["PATH"]},capture_output=True,text=True,timeout=5)

    def test_redis_config_keeps_runtime_password_private_and_enables_persistent_queue_storage(self):
        password="test_only_secret_"+"a"*32
        result=self.run_redis(password)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertNotIn(password,result.stdout+result.stderr)
        self.assertTrue(all(json.loads(result.stdout).values()))

    def test_redis_rejects_empty_short_or_config_injection_password_without_echoing_it(self):
        for password in ("","short","a"*129,"a"*32+"\nprotected-mode no"):
            with self.subTest(length=len(password)):
                result=self.run_redis(password)
                self.assertEqual(result.returncode,1)
                if password:self.assertNotIn(password,result.stdout+result.stderr)
