"""Copy every SFX the scene templates use (scanned from engine/js) from the video-shotcraft audio library into
engine/audio/sfx and write engine/audio/ATTRIBUTION.md (SFX + music + voice). Files without a recorded source URL
are refused.

  python3 tools/collect_sfx.py <video-shotcraft>/assets/audio
"""
import glob, json, os, re, shutil, sys
from common import ENGINE, DATA, load_json

LIB = sys.argv[1]
rows = {}
for line in open(os.path.join(LIB, "ATTRIBUTION.md"), encoding="utf-8"):
    c = [x.strip() for x in line.strip().strip("|").split("|")]
    if len(c) < 4 or not c[0].startswith("`") or not c[1].startswith("`"):
        continue
    url = re.search(r"https?://\S+", c[-1])
    title = c[2] if len(c) == 4 and url and c[3].startswith("http") else re.sub(r"\s*·\s*https?://\S+", "", c[-1])
    rows[c[1].strip("`").rstrip("/") + "/" + c[0].strip("`")] = (title, url.group(0) if url else None)
js = "".join(open(f, encoding="utf-8").read() for f in glob.glob(os.path.join(ENGINE, "js", "*.js")))
used = sorted(set(re.findall(r"'((?:transition|impact|paper|text|light|fluid|crowd|counter|ui|film|camera|glass|riser|data|mech|scifi)/[a-z0-9\-]+)'", js)))
lines = []
for s in used:
    key = f"sfx/{s}.mp3"
    title, url = rows.get(key, (None, None))
    if not url:
        sys.exit(f"tidak ada URL sumber tercatat untuk {key}")
    dst = os.path.join(ENGINE, "audio", key)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(os.path.join(LIB, key), dst)
    lines.append(f"| `{key}` | {title} | {url} |")
music = "\n".join(f"| `bgm/{m['berkas']}` | {m['judul']} | {m['artis']} | {m['lisensi']} | {m['url']} |" for m in load_json(os.path.join(DATA, "musik.json")))
md = f"""# Atribusi audio mesin-video

## Suara
ElevenLabs (`eleven_v3`, suara premade "Liam"). Akun gratis: non-komersial dan wajib atribusi ("Suara: ElevenLabs" tampil
di penutup tiap video). Untuk monetisasi, pakai paket berbayar lalu jalankan ulang `tools/voice.py`.

## Musik (Mixkit Stock Music Free License)

| Berkas | Judul | Artis | Lisensi | Sumber |
|---|---|---|---|---|
{music}

## Efek suara ({len(lines)} berkas dari pustaka video-shotcraft; Mixkit Sound Effects Free License)

| Berkas | Judul asli | Sumber |
|---|---|---|
""" + "\n".join(lines) + "\n\n## Ikon\nFluent Emoji Flat (Microsoft, lisensi MIT) lewat paket npm `@iconify-json/fluent-emoji-flat`; ikon tempe dibuat untuk proyek ini.\n"
open(os.path.join(ENGINE, "audio", "ATTRIBUTION.md"), "w", encoding="utf-8").write(md)
print(f"{len(used)} SFX disalin; engine/audio/ATTRIBUTION.md ditulis")
