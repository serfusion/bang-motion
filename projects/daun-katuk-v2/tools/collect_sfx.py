"""Copy every SFX referenced by sfx.json from the video-shotcraft library into assets/audio/sfx/
and write assets/audio/ATTRIBUTION.md (music + SFX + voice). Refuses files whose source URL is not recorded.

usage: python3 tools/collect_sfx.py <path-to-video-shotcraft>/assets/audio
"""
import json, os, re, shutil, sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
LIB = sys.argv[1]
att = open(os.path.join(LIB, "ATTRIBUTION.md"), encoding="utf-8").read()
rows = {}
for line in att.splitlines():
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) < 4 or not c[0].startswith("`") or not c[1].startswith("`"):
        continue
    key = c[1].strip("`").rstrip("/") + "/" + c[0].strip("`")
    url = re.search(r"https?://\S+", c[-1])
    title = c[2] if len(c) == 4 and url and c[3].startswith("http") else re.sub(r"\s*·\s*https?://\S+", "", c[-1])
    rows[key] = (title, url.group(0) if url else None)

sfx = json.load(open(os.path.join(ROOT, "sfx.json"), encoding="utf-8"))
used = sorted(set(p["src"] for p in sfx))
lines = []
for s in used:
    key = f"sfx/{s}.mp3"
    title, url = rows.get(key, (None, None))
    if not url:
        sys.exit(f"no recorded source URL for {key}: pick another file")
    dst = os.path.join(ROOT, "assets/audio", key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(LIB, key), dst)
    lines.append(f"| `{key}` | {title} | {url} |")

md = f"""# Atribusi audio

## Suara (voice-over)

Dibuat dengan **ElevenLabs** (model `eleven_v3`, suara premade "Liam"), bahasa Indonesia, dengan tag emosi.
Akun gratis ElevenLabs: hasilnya untuk penggunaan **non-komersial** dan **wajib mencantumkan atribusi** ("Suara: ElevenLabs" sudah ada di frame penutup).
Untuk monetisasi/komersial, buat ulang suara dengan paket berbayar ElevenLabs (lihat `tools/tts_el.py`).

## Musik

| Berkas | Judul | Artis | Lisensi | Sumber |
|---|---|---|---|---|
| `bgm/kids.mp3` | Kids | Michael Ramir C. | Mixkit Stock Music Free License | https://assets.mixkit.co/music/786/786.mp3 |

## Efek suara ({len(lines)} berkas, dari pustaka video-shotcraft; Mixkit Sound Effects Free License)

Hanya berkas yang URL sumbernya tercatat yang dipakai (`tools/collect_sfx.py` menolak yang tidak tercatat).

| Berkas | Judul asli | Sumber |
|---|---|---|
""" + "\n".join(lines) + "\n"
open(os.path.join(ROOT, "assets/audio/ATTRIBUTION.md"), "w", encoding="utf-8").write(md)
print(f"{len(used)} SFX copied; ATTRIBUTION.md written")
