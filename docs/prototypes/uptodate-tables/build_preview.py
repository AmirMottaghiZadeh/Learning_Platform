"""Build portable HTML previews from local, read-only UpToDate data.

Run from the repository root. The existing reader's wrap() is evaluated by the
small Node helper. Uses installed frontend dependencies; no network is needed.
"""

import base64
import json
from pathlib import Path
import sqlite3
import subprocess
import zlib


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = Path("/home/amir/Documents/UpToDate/content.db")
FONTS = ROOT / "frontend/node_modules/@expo-google-fonts/vazirmatn"


def build():
    samples = []
    connection = sqlite3.connect(f"file:{SOURCE}?mode=ro", uri=True)
    try:
        for content_id in ("112171", "112172", "141829"):
            blob = connection.execute("SELECT gzip FROM content WHERE id=?", (content_id,)).fetchone()[0]
            document = json.loads(zlib.decompress(blob))
            samples.append({"id": content_id, "title": document["title"], "body": document["bodyHtml"]})
    finally:
        connection.close()
    rendered = subprocess.run(["node", str(HERE / "render_legacy.cjs")],
                              input=json.dumps(samples), capture_output=True, text=True, check=True)
    legacy = json.loads(rendered.stdout)
    for sample in samples:
        sample["legacy"] = legacy[sample["id"]]
    template = (HERE / "preview.template.html").read_text()
    for token, filename in (("__FONT_REGULAR__", "400Regular/Vazirmatn_400Regular.ttf"),
                            ("__FONT_SEMIBOLD__", "600SemiBold/Vazirmatn_600SemiBold.ttf")):
        template = template.replace(token, base64.b64encode((FONTS / filename).read_bytes()).decode())
    template = template.replace("__SAMPLES_JSON__", json.dumps(samples, ensure_ascii=False).replace("<", "\\u003c"))
    for name, mode in (("index", "reference"), ("reference", "reference"),
                       ("reading", "reading"), ("compare", "compare"), ("mobile", "mobile")):
        target = HERE / f"{name}.html"
        target.write_text(template.replace("__DEFAULT_MODE__", mode))
        print(f"{target.name}: {target.stat().st_size:,} bytes")


if __name__ == "__main__":
    build()
