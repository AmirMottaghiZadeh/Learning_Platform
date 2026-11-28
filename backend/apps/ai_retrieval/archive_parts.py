"""Split/join a finished vector archive with bounded memory and SHA-256 checks.

Pure standard library: this file can be uploaded beside the parts and run on
the server without installing anything or accessing Django, a database or API.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import stat
import sys

FORMAT = "pharmenta-vector-parts-v1"
BUFFER_BYTES = 4 * 1024 * 1024
MAX_PARTS = 1000


class ArchivePartsError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


def _private_file(path):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    return os.fdopen(fd, "wb")


def _signature(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def split_archive(source, *, parts=10, output_dir=None, progress=lambda _: None):
    if type(parts) is not int or not 2 <= parts <= MAX_PARTS:
        raise ArchivePartsError("INVALID_PART_COUNT")
    source = Path(source)
    destination = Path(output_dir) if output_dir is not None else Path(str(source) + ".parts")
    created = []
    owns_directory = False
    try:
        with source.open("rb") as stream:
            original = os.fstat(stream.fileno())
            if not stat.S_ISREG(original.st_mode) or original.st_size < parts:
                raise ArchivePartsError("ARCHIVE_TOO_SMALL_OR_NOT_REGULAR")
            # A completed previous split is never overwritten or removed.
            destination.mkdir(mode=0o700)
            owns_directory = True
            whole = sha256()
            entries = []
            written = 0
            width = max(3, len(str(parts)))
            base, extra = divmod(original.st_size, parts)
            for index in range(parts):
                size = base + (index < extra)
                name = f"{source.name}.part-{index + 1:0{width}d}-of-{parts:0{width}d}"
                part_path = destination / name
                digest = sha256()
                with _private_file(part_path) as target:
                    created.append(part_path)
                    remaining = size
                    while remaining:
                        block = stream.read(min(BUFFER_BYTES, remaining))
                        if not block:
                            raise ArchivePartsError("SOURCE_CHANGED_DURING_SPLIT")
                        target.write(block)
                        digest.update(block)
                        whole.update(block)
                        remaining -= len(block)
                    target.flush()
                    os.fsync(target.fileno())
                entries.append({"name": name, "bytes": size, "sha256": digest.hexdigest()})
                written += size
                progress({"stage": "split", "part": index + 1, "parts": parts,
                          "written_bytes": written, "total_bytes": original.st_size})
            if (stream.read(1) or _signature(os.fstat(stream.fileno())) != _signature(original)
                    or _signature(source.stat()) != _signature(original)):
                raise ArchivePartsError("SOURCE_CHANGED_DURING_SPLIT")
        manifest = {"format": FORMAT, "file": source.name, "bytes": original.st_size,
                    "sha256": whole.hexdigest(), "parts": entries}
        helper_path = destination / "archive_parts.py"
        with _private_file(helper_path) as target:
            created.append(helper_path)
            target.write(Path(__file__).read_bytes())
            target.flush()
            os.fsync(target.fileno())
        manifest_path = destination / "manifest.json"
        with _private_file(manifest_path) as target:
            created.append(manifest_path)
            target.write((json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode())
            target.flush()
            os.fsync(target.fileno())
        return {"parts": parts, "bytes": original.st_size, "sha256": whole.hexdigest(),
                "manifest": str(manifest_path), "join_tool": str(helper_path), "provider_requests": 0}
    except BaseException:
        # Clean only files created by this invocation; never touch the source.
        for path in reversed(created):
            path.unlink(missing_ok=True)
        if owns_directory:
            try:
                destination.rmdir()
            except OSError:
                pass
        raise


def _leaf(value):
    return (isinstance(value, str) and value not in {"", ".", ".."}
            and not any(character in value for character in ("/", "\\", "\x00")))


def _digest(value):
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _manifest(path):
    with path.open("rb") as stream:
        raw = stream.read(1024 * 1024 + 1)
    try:
        value = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ArchivePartsError("INVALID_PARTS_MANIFEST") from None
    if (len(raw) > 1024 * 1024 or not isinstance(value, dict) or value.get("format") != FORMAT
            or not _leaf(value.get("file")) or not _digest(value.get("sha256"))
            or type(value.get("bytes")) is not int or value["bytes"] < 1
            or not isinstance(value.get("parts"), list) or not 2 <= len(value["parts"]) <= MAX_PARTS):
        raise ArchivePartsError("INVALID_PARTS_MANIFEST")
    names = set()
    total = 0
    for entry in value["parts"]:
        if (not isinstance(entry, dict) or not _leaf(entry.get("name")) or entry["name"] in names
                or entry["name"] == path.name or not _digest(entry.get("sha256"))
                or type(entry.get("bytes")) is not int or entry["bytes"] < 1):
            raise ArchivePartsError("INVALID_PARTS_MANIFEST")
        names.add(entry["name"])
        total += entry["bytes"]
    if total != value["bytes"]:
        raise ArchivePartsError("INVALID_PARTS_MANIFEST")
    return value


def join_archive(manifest, *, output=None, progress=lambda _: None):
    manifest = Path(manifest)
    metadata = _manifest(manifest)
    destination = Path(output) if output is not None else manifest.parent.parent / metadata["file"]
    # Exclusive output creation also rejects a destination symlink or a part
    # chosen as the destination. Existing archives always remain untouched.
    created = False
    try:
        with _private_file(destination) as target:
            created = True
            whole = sha256()
            written = 0
            for index, entry in enumerate(metadata["parts"], 1):
                part_path = manifest.parent / entry["name"]
                fd = os.open(part_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
                with os.fdopen(fd, "rb") as stream:
                    original = os.fstat(stream.fileno())
                    if not stat.S_ISREG(original.st_mode) or original.st_size != entry["bytes"]:
                        raise ArchivePartsError("PART_SIZE_MISMATCH")
                    digest = sha256()
                    remaining = entry["bytes"]
                    while remaining:
                        block = stream.read(min(BUFFER_BYTES, remaining))
                        if not block:
                            raise ArchivePartsError("PART_SIZE_MISMATCH")
                        digest.update(block)
                        whole.update(block)
                        target.write(block)
                        remaining -= len(block)
                    if (stream.read(1) or digest.hexdigest() != entry["sha256"]
                            or _signature(os.fstat(stream.fileno())) != _signature(original)):
                        raise ArchivePartsError("PART_CHECKSUM_MISMATCH")
                written += entry["bytes"]
                progress({"stage": "join", "part": index, "parts": len(metadata["parts"]),
                          "written_bytes": written, "total_bytes": metadata["bytes"]})
            if written != metadata["bytes"] or whole.hexdigest() != metadata["sha256"]:
                raise ArchivePartsError("ARCHIVE_CHECKSUM_MISMATCH")
            target.flush()
            os.fsync(target.fileno())
        return {"joined": len(metadata["parts"]), "bytes": written, "sha256": whole.hexdigest(),
                "output": str(destination), "provider_requests": 0}
    except BaseException:
        if created:
            destination.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="Split/join a completed vector export; no database or API access.")
    commands = parser.add_subparsers(dest="command", required=True)
    split = commands.add_parser("split", help="Run after export completes. Original file is preserved.")
    split.add_argument("--input", required=True)
    split.add_argument("--parts", type=int, default=10)
    split.add_argument("--output-dir")
    join = commands.add_parser("join", help="Reassemble and verify all part/whole SHA-256 checksums.")
    join.add_argument("--manifest", required=True)
    join.add_argument("--output", required=True)
    options = parser.parse_args()
    def report(value):
        print(json.dumps(value), flush=True)
    try:
        if options.command == "split":
            result = split_archive(options.input, parts=options.parts, output_dir=options.output_dir, progress=report)
        else:
            result = join_archive(options.manifest, output=options.output, progress=report)
        report(result)
        return 0
    except ArchivePartsError as exc:
        print(f"Archive transfer failed: {exc.code}", file=sys.stderr)
    except OSError as exc:
        print(f"Archive transfer failed: FILE_IO_ERROR errno={exc.errno}", file=sys.stderr)
    except KeyboardInterrupt:
        print("Archive transfer interrupted; incomplete output removed; source files preserved.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
