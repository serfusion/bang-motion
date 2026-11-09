"""Lay the VO clips on the BGM beat grid and build the subtitle pages.

Every scene cut lands on a beat of the music (122 BPM, T = 0.4918 s, beat 0 at
video t = 0); the voice of a scene starts LEAD seconds after its cut.
Writes timeline.json (single source of truth for the page, the SFX table and the mix).
"""
import json, math, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
T = 0.49180              # beat length (s), fitted with librosa (see README)
DURATION = 60.0          # = 122 beats
GAP = 0.15               # min silence after a line before the next cut
LEAD = 0.12              # voice starts this long after the cut
FIRST = 0.05             # hook voice starts almost immediately
BAR_CUTS = {"s8"}        # the BGM jumps to its breakdown here (see tools/mix.py)

import sys; sys.path.insert(0, HERE)
from script import LINES, speech  # noqa: E402

vo = json.load(open(os.path.join(ROOT, "assets/vo/words.json"), encoding="utf-8"))
lines = {l["key"]: l for l in vo["lines"]}
ceil_beat = lambda t: math.ceil(t / T - 1e-6) * T

# spoken number phrases -> what the subtitle shows
MERGE = [
    (["seratus", "enam", "puluh", "empat", "miligram,"], "164 mg,"),
    (["empat", "puluh", "sembilan."], "49."),
    (["dua", "ratus", "tiga", "puluh", "tiga", "miligram,"], "233 mg,"),
]
norm = lambda s: re.sub(r"[^0-9a-z\-]", "", s.lower())

scenes, t_end = [], None
for i, (key, text) in enumerate(LINES):
    L = lines[key]; w0 = L["words"][0]
    if i == 0:
        cut = 0.0; first = FIRST
    else:
        cut = ceil_beat(t_end + GAP); first = cut + LEAD
        if key in BAR_CUTS:                   # music edit points must sit on a bar line
            cut = math.ceil(round(cut / T) / 4) * 4 * T; first = cut + LEAD
    a = first - w0["t"]                       # where the clip's own t=0 sits
    raw = text.split(); toks, breaks = [], set()
    for x in raw:
        if x == "|": breaks.add(len(toks) - 1)
        else: toks.append(x)
    assert len(toks) == len(L["words"]), (key, toks, [w["w"] for w in L["words"]])
    words = []
    for tok, w in zip(toks, L["words"]):
        assert norm(tok) == norm(w["w"]), (key, tok, w["w"])
        words.append({"w": tok, "t": round(a + w["t"], 3), "e": round(a + w["t"] + w["d"], 3),
                      "brk": (len(words) in breaks)})
    # merge number phrases for display
    j = 0; disp = []
    while j < len(words):
        for seq, rep in MERGE:
            if [x["w"] for x in words[j:j + len(seq)]] == seq:
                last = words[j + len(seq) - 1]
                disp.append({"w": rep, "t": words[j]["t"], "e": last["e"], "brk": last["brk"]}); j += len(seq); break
        else:
            disp.append(words[j]); j += 1
    t_end = words[-1]["e"]
    scenes.append({"key": key, "cut": round(cut, 3), "beat": round(cut / T), "voStart": round(a, 4),
                   "voFile": L["file"], "speechStart": words[0]["t"], "speechEnd": t_end,
                   "text": speech(text), "words": disp,
                   "raw": [{"w": x["w"], "t": x["t"], "e": x["e"]} for x in words]})

# subtitle pages: hand-placed breaks ("|" in script.py) + end of line
pages = []
for s in scenes:
    cur = []
    for k, w in enumerate(s["words"]):
        cur.append(w)
        if w.pop("brk", False) or k + 1 == len(s["words"]):
            pages.append({"scene": s["key"], "t": cur[0]["t"], "e": cur[-1]["e"],
                          "words": [dict(x) for x in cur]}); cur = []
# each page stays until the next page starts (max +0.6 s), never across the next cut
cuts = [s["cut"] for s in scenes] + [DURATION]
for n, p in enumerate(pages):
    nxt_t = pages[n + 1]["t"] if n + 1 < len(pages) else DURATION
    scene_i = [s["key"] for s in scenes].index(p["scene"])
    hard = cuts[scene_i + 1] - 0.05
    p["out"] = round(min(nxt_t, p["e"] + 0.6, hard) if n + 1 < len(pages) else min(p["e"] + 1.2, DURATION - .3), 3)

out = {"T": T, "duration": DURATION, "beats": round(DURATION / T), "scenes": scenes, "pages": pages}
json.dump(out, open(os.path.join(ROOT, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for s in scenes:
    print(f"{s['key']} cut {s['cut']:6.2f}s (beat {s['beat']:3d})  voice {s['speechStart']:6.2f}-{s['speechEnd']:6.2f}")
print(f"end hold: {DURATION - scenes[-1]['speechEnd']:.2f}s  pages: {len(pages)}")
for p in pages: print(f"  {p['t']:6.2f}-{p['out']:6.2f} | {' '.join(w['w'] for w in p['words'])}")
