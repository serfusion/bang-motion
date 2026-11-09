"""Write the subtitle pages (the same pages as the burned-in captions) as SRT: out/daun-katuk-v2.id.srt + .en.srt."""
import json, os
ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round((t - int(t)) * 1000) % 1000)
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
P = tl["pages"]
for lang in ("id", "en"):
    path = os.path.join(ROOT, "out", f"daun-katuk-v2.{lang}.srt")
    with open(path, "w", encoding="utf-8") as f:
        for i, p in enumerate(P):
            a = max(0.0, p["t"] - 0.06)
            nx = P[i + 1] if i + 1 < len(P) else None          # same rule as the page: the next page replaces this one
            end = nx["t"] - 0.06 if nx and nx["t"] - 0.06 <= p["out"] + 0.12 else p["out"]
            f.write(f"{i + 1}\n{ts(a)} --> {ts(end)}\n{p[lang]}\n\n")
    print(len(P), "cues ->", os.path.relpath(path, ROOT))
