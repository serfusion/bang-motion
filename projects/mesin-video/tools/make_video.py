"""One command from the database to finished videos (no AI step; the voice is a TTS service call).

  python3 tools/make_video.py ID [ID ...] [--tanpa-en] [--dari LANGKAH] [--sampai LANGKAH]

Steps (each one reads the previous one's files, so a run can resume with --dari):
  export   db -> episodes/ID/episode.json (validated)
  voice    ElevenLabs TTS per scene (cached) + pause/tempo edit
  layout   cuts on the beat grid, cues, subtitle pages, mouth envelope -> timeline.json
  page     single-file HTML page (engine + data + icons) -> index.html
  sfx      SFX pin table computed by the page -> sfx.json
  mix      voice + SFX + music -> build/mix*.wav, mix.m4a
  render   frame-accurate export (Chromium) -> build/video.mp4, build-en/video.mp4
  final    encode + mux + SRT -> out/*.mp4, out/*.srt; status 'dirender' in the db
Needs: python3 (numpy, librosa for `db.py musik`), node (npm install), ffmpeg with rubberband, Chromium
(PUPPETEER_EXECUTABLE_PATH if puppeteer has none).
"""
import os, subprocess, sys, time
from common import PROJ, ep_dir
import db, voice, layout, build_page, mix, finalize
from common import load_json

STEPS = ["export", "voice", "layout", "page", "sfx", "mix", "render", "final"]


def node(script, *args, env=None):
    subprocess.run(["node", os.path.join(PROJ, "tools", script), *args], check=True, env={**os.environ, **(env or {})})


def make(eid, start="export", en=True, stop="final"):
    t0 = time.time()
    todo = STEPS[STEPS.index(start):STEPS.index(stop) + 1]
    for step in todo:
        print(f"== {eid}: {step}")
        if step == "export":
            db.cmd_export(eid)
        elif step == "voice":
            ep = load_json(ep_dir(eid, "episode.json")); voice.edit(ep, voice.tts(ep))
        elif step == "layout":
            layout.main(eid)
        elif step == "page":
            build_page.main(eid)
        elif step == "sfx":
            node("dump_sfx.mjs", eid)
        elif step == "mix":
            mix.main(eid)
        elif step == "render":
            url = "file://" + ep_dir(eid, "index.html") + "?clean=1"
            node("export.mjs", env={"URL": url, "OUT": ep_dir(eid, "build"), "SHARDS": os.environ.get("SHARDS", "4")})
            if en:
                node("export.mjs", env={"URL": url + "&lang=en", "OUT": ep_dir(eid, "build-en"), "SHARDS": os.environ.get("SHARDS", "4")})
        elif step == "final":
            finalize.main(eid)
    print(f"== {eid}: selesai dalam {time.time() - t0:.0f} s")


if __name__ == "__main__":
    a = sys.argv[1:]
    start = a[a.index("--dari") + 1] if "--dari" in a else "export"
    stop = a[a.index("--sampai") + 1] if "--sampai" in a else "final"
    en = "--tanpa-en" not in a
    ids = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--dari", "--sampai"))]
    for eid in ids:
        make(eid, start, en, stop)
