"""Encode the deliverables of one episode and record them in the database.

  python3 tools/finalize.py ID [id|en]
    episodes/ID/<lang>/out/ID-<lang>.mp4              suara + subtitle bahasa itu, efek + musik
    episodes/ID/<lang>/out/ID-<lang>-tanpa-musik.mp4  suara + efek (musik dari platform)
    episodes/ID/<lang>/out/ID-<lang>.srt
"""
import os, sqlite3, subprocess, sys
from common import DBFILE, lang_dir, load_json


def run(*a):
    subprocess.run(list(a), check=True)


def srt(eid, lang):
    tl = load_json(lang_dir(eid, lang, "timeline.json"))
    ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round((t - int(t)) * 1000) % 1000)
    P = tl["pages"]
    with open(lang_dir(eid, lang, "out", f"{eid}-{lang}.srt"), "w", encoding="utf-8") as f:
        for i, p in enumerate(P):
            nx = P[i + 1] if i + 1 < len(P) else None
            end = nx["t"] - 0.08 if nx and nx["t"] - 0.08 <= p["out"] + 0.12 else p["out"]
            f.write(f"{i + 1}\n{ts(max(0.0, p['t'] - 0.08))} --> {ts(end)}\n{p['teks']}\n\n")


def main(eid, lang="id"):
    D = lambda *p: lang_dir(eid, lang, *p)
    os.makedirs(D("out"), exist_ok=True)
    outs = []
    for build, variants in (("build", [("mix", f"{eid}-{lang}", lang), ("mix-nobgm", f"{eid}-{lang}-tanpa-musik", f"{lang}-tanpa-musik")]),):
        if not os.path.exists(D(build, "video.mp4")):
            continue
        vf = D(build, "video-final.mp4")
        if not (os.path.exists(vf) and os.path.getmtime(vf) > os.path.getmtime(D(build, "video.mp4"))):
          run("ffmpeg", "-v", "error", "-y", "-i", D(build, "video.mp4"), "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "21"),
            "-maxrate", "5M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2", "-an", D(build, "video-final.mp4"))
        for mix, name, variant_lang in variants:
            run("ffmpeg", "-v", "error", "-y", "-i", D(build, "video-final.mp4"), "-i", D("build", f"{mix}.wav"), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", D("out", f"{name}.mp4"))
            outs.append((variant_lang, f"episodes/{eid}/{lang}/out/{name}.mp4"))
    srt(eid, lang)
    dur = load_json(D("timeline.json"))["duration"]
    if os.path.exists(DBFILE):
        con = sqlite3.connect(DBFILE)
        con.execute("DELETE FROM render WHERE episode_id=? AND bahasa LIKE ?", (eid, lang + "%"))
        con.executemany("INSERT INTO render (episode_id, bahasa, berkas, durasi) VALUES (?,?,?,?)", [(eid, l, f, dur) for l, f in outs])
        con.execute("UPDATE episode SET status='dirender' WHERE id=?", (eid,))
        con.commit()
    for l, f in outs:
        print(f"{l:16s} {f}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "id")
