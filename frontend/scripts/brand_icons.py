"""Every web icon of the app and the site, from one source image.

The installable web app (PWA) and the site's icons for search engines and
phones all come from frontend/assets/icons/Mortar.png (a white rounded square
with transparent corners, the owner's choice of 2026-11-01):

- icons a browser may show on any background keep the transparent corners;
- the iOS home-screen icon and the Android maskable icon get the corners filled
  white: iOS paints transparency black, and a maskable icon must fill its
  square (the logo sits well inside the 80% safe zone).

Run from the repository root, then bump `?v=` in frontend/public/manifest.webmanifest
and index.html so an installed web app picks the new icon up:

    python3 frontend/scripts/brand_icons.py
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "frontend/assets/icons/Mortar.png"
APP = ROOT / "frontend/public"
SITE = ROOT / "backend/apps/website/static/website/brand"


def sized(image, size, opaque=False):
    out = image.resize((size, size), Image.LANCZOS)
    if not opaque:
        return out
    flat = Image.new("RGB", out.size, "white")
    flat.paste(out, mask=out.getchannel("A"))
    return flat


def main():
    source = Image.open(SOURCE).convert("RGBA")
    files = {
        APP / "favicon.png": (48, False),
        APP / "icon-192.png": (192, False),
        APP / "icon-512.png": (512, False),
        APP / "icon-maskable-512.png": (512, True),
        APP / "apple-touch-icon.png": (180, True),
        SITE / "favicon-48x48.png": (48, False),
        SITE / "favicon-96x96.png": (96, False),
        SITE / "icon-192.png": (192, False),
        SITE / "icon-512.png": (512, False),
        SITE / "apple-touch-icon.png": (180, True),
    }
    for path, (size, opaque) in files.items():
        sized(source, size, opaque).save(path, optimize=True)
        print(path.relative_to(ROOT), size)
    ico = SITE / "favicon.ico"
    sized(source, 48).save(ico, sizes=[(16, 16), (32, 32), (48, 48)])
    print(ico.relative_to(ROOT), "16/32/48")


if __name__ == "__main__":
    main()
