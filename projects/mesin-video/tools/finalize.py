"""Encode the deliverables of one episode and record them in the database.

  python3 tools/finalize.py ID
    episodes/ID/out/ID.mp4             subtitle ID, suara + efek + musik
    episodes/ID/out/ID-tanpa-musik.mp4 subtitle ID, suara + efek (musik dari platform)
    episodes/ID/out/ID-en.mp4          subtitle EN (bila build-en/video.mp4 ada)
    episodes/ID/out/ID.id.srt, ID.en.srt
"""
import os, sqlite3, subprocess, sys
from common import DBFILE, ep_dir, load_json


def run(*a):
    subprocess.run(list(a), check=True)


def srt(eid):
    tl = load_json(ep_dir(eid, "timeline.json"))
    ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round((t - int(t)) * 1000) % 1000)
    P = tl["pages"]
    for lang in ("id", "en"):
        with open(ep_dir(eid, "out", f"{eid}.{lang}.srt"), "w", encoding="utf-8") as f:
            for i, p in enumerate(P):
                nx = P[i + 1] if i + 1 < len(P) else None
                end = nx["t"] - 0.12 if nx and nx["t"] - 0.12 <= p["out"] + 0.12 else p["out"]
                f.write(f"{i + 1}\n{ts(max(0.0, p['t'] - 0.12))} --> {ts(end)}\n{p[lang]}\n\n")


def main(eid):
    D = lambda *p: ep_dir(eid, *p)
    os.makedirs(D("out"), exist_ok=True)
    outs = []
    for build, variants in (("build", [("mix", eid, "id"), ("mix-nobgm", f"{eid}-tanpa-musik", "id-tanpa-musik")]),
                            ("build-en", [("mix", f"{eid}-en", "en")])):
        if not os.path.exists(D(build, "video.mp4")):
            continue
        run("ffmpeg", "-v", "error", "-y", "-i", D(build, "video.mp4"), "-c:v", "libx264", "-preset", "slow", "-crf", os.environ.get("CRF", "21"),
            "-maxrate", "5M", "-bufsize", "10M", "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.2", "-an", D(build, "video-final.mp4"))
        for mix, name, lang in variants:
            run("ffmpeg", "-v", "error", "-y", "-i", D(build, "video-final.mp4"), "-i", D("build", f"{mix}.wav"), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", D("out", f"{name}.mp4"))
            outs.append((lang, f"episodes/{eid}/out/{name}.mp4"))
    srt(eid)
    dur = load_json(D("timeline.json"))["duration"]
    if os.path.exists(DBFILE):
        con = sqlite3.connect(DBFILE)
        con.execute("DELETE FROM render WHERE episode_id=?", (eid,))
        con.executemany("INSERT INTO render (episode_id, bahasa, berkas, durasi) VALUES (?,?,?,?)", [(eid, l, f, dur) for l, f in outs])
        con.execute("UPDATE episode SET status='dirender' WHERE id=?", (eid,))
        con.commit()
    for l, f in outs:
        print(f"{l:16s} {f}")


if __name__ == "__main__":
    main(sys.argv[1])
