"""Write the Indonesian subtitles (same pages as the burned-in captions) to out/daun-katuk.id.srt."""
import json, os
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
ts = lambda t: "%02d:%02d:%02d,%03d" % (t // 3600, t % 3600 // 60, t % 60, round((t - int(t)) * 1000) % 1000)
os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
with open(os.path.join(ROOT, "out", "daun-katuk.id.srt"), "w", encoding="utf-8") as f:
    for i, p in enumerate(tl["pages"], 1):
        f.write(f"{i}\n{ts(max(0, p['t'] - .06))} --> {ts(p['out'])}\n{' '.join(w['w'] for w in p['words'])}\n\n")
print(len(tl["pages"]), "subtitle cues -> out/daun-katuk.id.srt")
