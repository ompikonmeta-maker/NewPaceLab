#!/usr/bin/env python3
"""Build a portable Windows ZIP: the official embeddable Python + NewPaceLab.

  python tools/make_portable.py --arch amd64        (Intel/AMD)
  python tools/make_portable.py --arch arm64        (Windows on ARM)
  python tools/make_portable.py --arch amd64 --embed python-3.12.10-embed-amd64.zip

Result: dist-portable/NewPaceLab-portable-win-<arch>.zip with a top folder
NewPaceLab/. Extracting it over an existing C:\\NewPaceLab keeps keys/,
programs/ and data/ (the ZIP only carries placeholders there).
"""
import argparse
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY_VERSION = "3.12.10"
URL = "https://www.python.org/ftp/python/{v}/python-{v}-embed-{arch}.zip"
APP = ["pacelab.py", "config.json", "README.md", "Update Dashboard.bat", "Demo Dashboard.bat",
       "pacelab", "tools/mock_garmin.py", "tools/fitgen.py"]

README = """NewPaceLab portable - Windows {arch}

Python {v} sudah ada di folder python\\ - tidak perlu install apa-apa.

SEKALI SAJA
1. Simpan key Garmin sebagai file teks di folder keys\\
     keys\\TAOFIK.key   (isinya hanya key, tanpa spasi/enter)
     keys\\REZA.key
2. Copy file Excel program ke folder programs\\
     programs\\Program_Marathon_TAOFIK.xlsx
     programs\\Program_Marathon_PRAMANA.xlsx

SETIAP HARI
   Klik dua kali "Update Dashboard.bat".
   Data Garmin ditarik, dashboard dibuat dan terbuka di browser.
   File dashboard: dist\\dashboard.html (bisa dikirim lewat WA, terbuka tanpa internet).

COBA DULU TANPA KEY
   Klik dua kali "Demo Dashboard.bat" (data rekaan).
"""


def build(arch, embed, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp())
    top = work / "NewPaceLab"
    if embed is None:
        embed = work / ("python-%s-embed-%s.zip" % (PY_VERSION, arch))
        url = URL.format(v=PY_VERSION, arch=arch)
        print("download %s" % url)
        urllib.request.urlretrieve(url, embed)
    with zipfile.ZipFile(embed) as z:
        if not any(n.lower() == "python.exe" for n in z.namelist()):
            raise SystemExit("%s bukan paket Python embeddable (python.exe tidak ada)" % embed)
        z.extractall(top / "python")
    for item in APP:
        src = ROOT / item
        dst = top / item
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        else:
            shutil.copy2(src, dst)
    (top / "keys").mkdir()
    (top / "keys" / "TARUH-KEY-DI-SINI.txt").write_text(
        "Simpan key Garmin di folder ini: TAOFIK.key dan REZA.key (isinya hanya key).\r\n")
    (top / "programs").mkdir()
    (top / "programs" / "TARUH-EXCEL-DI-SINI.txt").write_text(
        "Program_Marathon_TAOFIK.xlsx dan Program_Marathon_PRAMANA.xlsx\r\n")
    (top / "BACA-SAYA.txt").write_text(README.format(arch=arch, v=PY_VERSION).replace("\n", "\r\n"))
    out = out_dir / ("NewPaceLab-portable-win-%s.zip" % arch)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(top.rglob("*")):
            z.write(p, p.relative_to(work).as_posix())
    shutil.rmtree(work)
    print("%s  (%.1f MB)" % (out, out.stat().st_size / 1e6))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arch", required=True, choices=["amd64", "arm64"])
    ap.add_argument("--embed", type=Path, help="embeddable Python zip yang sudah diunduh")
    ap.add_argument("--out", type=Path, default=ROOT / "dist-portable")
    a = ap.parse_args()
    build(a.arch, a.embed, a.out)


if __name__ == "__main__":
    main()
