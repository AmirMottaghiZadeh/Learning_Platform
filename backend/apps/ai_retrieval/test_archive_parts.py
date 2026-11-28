import gzip
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase

from . import archive_parts
from .archive_parts import ArchivePartsError, join_archive, split_archive


class ArchivePartsTests(SimpleTestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "vectors.jsonl.gz"
        self.payload = gzip.compress(bytes(range(256)) * 50, mtime=0)
        self.source.write_bytes(self.payload)
        self.output = self.root / "joined.jsonl.gz"

    def split(self, **kwargs):
        result = split_archive(self.source, **kwargs)
        self.manifest = Path(result["manifest"])
        self.metadata = json.loads(self.manifest.read_text())
        return result

    def test_ten_balanced_parts_round_trip_byte_identically_without_changing_source(self):
        split_events = []
        result = self.split(progress=split_events.append)
        self.assertEqual(result["parts"], 10)
        sizes = [entry["bytes"] for entry in self.metadata["parts"]]
        self.assertEqual(sum(sizes), len(self.payload))
        self.assertLessEqual(max(sizes) - min(sizes), 1)
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.assertEqual(self.manifest.stat().st_mode & 0o777, 0o600)
        self.assertEqual(self.manifest.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(len(split_events), 10)
        self.assertEqual(split_events[-1]["written_bytes"], len(self.payload))
        for entry in self.metadata["parts"]:
            part = self.manifest.parent / entry["name"]
            self.assertEqual(part.stat().st_mode & 0o777, 0o600)
        join_events = []
        joined = join_archive(self.manifest, output=self.output, progress=join_events.append)
        self.assertEqual(joined["sha256"], sha256(self.payload).hexdigest())
        self.assertEqual(self.output.read_bytes(), self.payload)
        self.assertEqual(gzip.decompress(self.output.read_bytes()), bytes(range(256)) * 50)
        self.assertEqual(joined["provider_requests"], 0)
        self.assertEqual(len(join_events), 10)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)

    def test_corrupted_part_rejects_join_and_removes_only_incomplete_output(self):
        self.split()
        part = self.manifest.parent / self.metadata["parts"][3]["name"]
        original = part.read_bytes()
        part.write_bytes(bytes([original[0] ^ 1]) + original[1:])
        with self.assertRaisesMessage(ArchivePartsError, "PART_CHECKSUM_MISMATCH"):
            join_archive(self.manifest, output=self.output)
        self.assertFalse(self.output.exists())
        self.assertTrue(part.exists())
        self.assertEqual(self.source.read_bytes(), self.payload)

    def test_missing_or_truncated_part_does_not_leave_a_ready_output(self):
        self.split()
        part = self.manifest.parent / self.metadata["parts"][0]["name"]
        original = part.read_bytes()
        part.unlink()
        with self.assertRaises(FileNotFoundError):
            join_archive(self.manifest, output=self.output)
        self.assertFalse(self.output.exists())
        part.write_bytes(original[:-1])
        with self.assertRaisesMessage(ArchivePartsError, "PART_SIZE_MISMATCH"):
            join_archive(self.manifest, output=self.output)
        self.assertFalse(self.output.exists())

    def test_an_existing_archive_or_parts_directory_is_never_overwritten(self):
        result = self.split()
        self.output.write_bytes(b"keep existing output")
        with self.assertRaises(FileExistsError):
            join_archive(self.manifest, output=self.output)
        self.assertEqual(self.output.read_bytes(), b"keep existing output")
        with self.assertRaises(FileExistsError):
            split_archive(self.source)
        self.assertEqual(json.loads(self.manifest.read_text())["sha256"], result["sha256"])
        self.assertEqual(self.source.read_bytes(), self.payload)

    def test_bad_part_names_duplicates_and_total_sizes_are_rejected_before_output_creation(self):
        self.split()
        for change in [
            lambda value: value["parts"][0].update(name="../outside-file"),
            lambda value: value["parts"][0].update(name=value["parts"][1]["name"]),
            lambda value: value.update(file="/outside-file"),
            lambda value: value.update(bytes=value["bytes"] + 1),
        ]:
            value = json.loads(json.dumps(self.metadata))
            change(value)
            self.manifest.write_text(json.dumps(value))
            with self.assertRaisesMessage(ArchivePartsError, "INVALID_PARTS_MANIFEST"):
                join_archive(self.manifest, output=self.output)
            self.assertFalse(self.output.exists())

    def test_whole_archive_checksum_is_verified_separately(self):
        self.split()
        self.metadata["sha256"] = "f" * 64
        self.manifest.write_text(json.dumps(self.metadata))
        with self.assertRaisesMessage(ArchivePartsError, "ARCHIVE_CHECKSUM_MISMATCH"):
            join_archive(self.manifest, output=self.output)
        self.assertFalse(self.output.exists())

    def test_a_source_still_growing_is_rejected_and_partial_parts_are_removed(self):
        def grow(event):
            if event["part"] == 1:
                with self.source.open("ab") as target:
                    target.write(b"still exporting")
        with self.assertRaisesMessage(ArchivePartsError, "SOURCE_CHANGED_DURING_SPLIT"):
            split_archive(self.source, progress=grow)
        self.assertFalse(Path(str(self.source) + ".parts").exists())
        self.assertTrue(self.source.read_bytes().endswith(b"still exporting"))

    def test_interrupted_split_and_join_preserve_source_and_completed_parts(self):
        def interrupt(_event):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            split_archive(self.source, progress=interrupt)
        self.assertFalse(Path(str(self.source) + ".parts").exists())
        self.assertEqual(self.source.read_bytes(), self.payload)
        self.split()
        with self.assertRaises(KeyboardInterrupt):
            join_archive(self.manifest, output=self.output, progress=interrupt)
        self.assertFalse(self.output.exists())
        self.assertTrue(self.manifest.exists())

    def test_invalid_part_counts_and_tiny_files_fail_without_output(self):
        for count in [1, 1001, True, 2.5]:
            with self.assertRaisesMessage(ArchivePartsError, "INVALID_PART_COUNT"):
                split_archive(self.source, parts=count)
        self.source.write_bytes(b"x")
        with self.assertRaisesMessage(ArchivePartsError, "ARCHIVE_TOO_SMALL_OR_NOT_REGULAR"):
            split_archive(self.source)
        self.assertFalse(Path(str(self.source) + ".parts").exists())

    def test_the_single_copied_script_works_without_django_or_the_repository(self):
        tool = self.root / "archive_parts.py"
        shutil.copyfile(archive_parts.__file__, tool)
        split = subprocess.run([sys.executable, str(tool), "split", "--input", str(self.source), "--parts", "10"],
                               cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(split.returncode, 0, split.stderr)
        manifest = json.loads(split.stdout.splitlines()[-1])["manifest"]
        uploaded_tool = Path(manifest).parent / "archive_parts.py"
        joined = subprocess.run([sys.executable, str(uploaded_tool), "join", "--manifest", manifest, "--output", str(self.output)],
                                cwd=self.root, capture_output=True, text=True, timeout=15)
        self.assertEqual(joined.returncode, 0, joined.stderr)
        self.assertEqual(self.output.read_bytes(), self.payload)

    def test_export_can_split_after_completion_and_rejects_existing_parts_before_export(self):
        self.source.unlink()
        def export(_generation, output, **kwargs):
            Path(output).write_bytes(self.payload)
            return {"exported": 3}
        command = "apps.ai_retrieval.management.commands.export_hybrid_vectors"
        with patch(command + ".RetrievalGeneration.objects.get", return_value=SimpleNamespace()), \
                patch(command + ".export_vectors", side_effect=export) as exported:
            call_command("export_hybrid_vectors", "fixture", output=str(self.source), parts=10, stdout=StringIO())
            self.assertTrue(Path(str(self.source) + ".parts/manifest.json").is_file())
            self.assertEqual(exported.call_count, 1)
            with self.assertRaisesMessage(CommandError, "PARTS_DIRECTORY_EXISTS"):
                call_command("export_hybrid_vectors", "fixture", output=str(self.source), parts=10, stdout=StringIO())
            self.assertEqual(exported.call_count, 1)

    def test_split_failure_after_export_keeps_completed_archive_for_retry(self):
        self.source.unlink()
        def export(_generation, output, **kwargs):
            Path(output).write_bytes(self.payload)
            return {"exported": 3}
        command = "apps.ai_retrieval.management.commands.export_hybrid_vectors"
        with patch(command + ".RetrievalGeneration.objects.get", return_value=SimpleNamespace()), \
                patch(command + ".export_vectors", side_effect=export), \
                patch(command + ".split_archive", side_effect=OSError("private-path-must-not-be-printed")):
            with self.assertRaises(CommandError) as error:
                call_command("export_hybrid_vectors", "fixture", output=str(self.source), parts=10, stdout=StringIO())
        self.assertIn("VECTOR_SPLIT_FAILED", str(error.exception))
        self.assertNotIn("private-path", str(error.exception))
        self.assertEqual(self.source.read_bytes(), self.payload)
