"""One command from the database to finished videos (no AI step; the voice is a TTS service call).

  python3 tools/make_video.py ID [ID ...] [--bahasa id,en] [--dari LANGKAH] [--sampai LANGKAH]

--bahasa  id = suara + subtitle Indonesia, en = suara + subtitle Inggris (default: id)
Steps (each one reads the previous one's files, so a run can resume with --dari):
  export   db -> episodes/ID/episode.json (validated for the chosen languages)
  voice    ElevenLabs TTS per scene (cached, key failover) + pause/tempo edit
  layout   cuts on the beat grid, cues, subtitle pages, mouth envelope -> <lang>/timeline.json
  page     single-file HTML page (engine + data + icons) -> <lang>/index.html
  sfx      SFX pin table computed by the page -> <lang>/sfx.json
  mix      voice + SFX + music -> <lang>/build/mix*.wav, <lang>/mix.m4a
  render   frame-accurate export (Chromium) -> <lang>/build/video.mp4
  final    encode + mux + SRT -> <lang>/out/*.mp4, *.srt; status 'dirender' in the db
Progress lines "== ID [lang]: step" are read by the web panel.
"""
import os, subprocess, sys, time
from common import PROJ, ep_dir, lang_dir, load_json
import db, voice, layout, build_page, mix, finalize

STEPS = ["export", "voice", "layout", "page", "sfx", "mix", "render", "final"]


def node(script, *args, env=None):
    subprocess.run(["node", os.path.join(PROJ, "tools", script), *args], check=True, env={**os.environ, **(env or {})})


def make(eid, langs=("id",), start="export", stop="final"):
    t0 = time.time()
    todo = STEPS[STEPS.index(start):STEPS.index(stop) + 1]
    # the database is the source of truth: re-export whenever a step that reads episode.json will run
    if any(s in todo for s in ("export", "voice", "layout", "page")):
        print(f"== {eid}: export", flush=True)
        db.cmd_export(eid, langs)
    for lang in langs:
        for step in todo:
            if step == "export":
                continue
            print(f"== {eid} [{lang}]: {step}", flush=True)
            if step == "voice":
                ep = load_json(ep_dir(eid, "episode.json")); voice.edit(ep, voice.tts(ep, lang), lang)
            elif step == "layout":
                layout.main(eid, lang)
            elif step == "page":
                build_page.main(eid, lang)
            elif step == "sfx":
                node("dump_sfx.mjs", eid, lang)
            elif step == "mix":
                mix.main(eid, lang)
            elif step == "render":
                node("export.mjs", env={"URL": "file://" + lang_dir(eid, lang, "index.html") + "?clean=1",
                                        "OUT": lang_dir(eid, lang, "build"), "SHARDS": os.environ.get("SHARDS", "4")})
            elif step == "final":
                finalize.main(eid, lang)
    print(f"== {eid}: selesai dalam {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    a = sys.argv[1:]
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    start, stop, langs = opt("--dari", "export"), opt("--sampai", "final"), tuple(opt("--bahasa", "id").split(","))
    flags = {"--dari", "--sampai", "--bahasa"}
    ids = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in flags)]
    for eid in ids:
        make(eid, langs, start, stop)
