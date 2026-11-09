"""Timeline v2: scene cuts on the music beat grid, subtitle pages (ID + EN), mouth envelope for the mascot.

Music: "Kids" (Michael Ramir C., Mixkit), 171.8 BPM, T = 0.3493 s. Video beat 0 = song bar 8 (11.46 s),
the twist scene is cut on the song's break (bar 39 = video beat 124).
Reads episode.json + assets/vo/words.edit.json, writes timeline.json.
"""
import json, math, os, re, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
T = 0.34930
DURATION = 60.0
GAP = 0.06                      # min air after a line before the next cut
LEAD = 0.03                     # voice starts this long after its cut
TWIST_BEAT = 0                  # twist is cut on a beat; a vinyl scratch hides the music edit there
EP = json.load(open(os.path.join(ROOT, "episode.json"), encoding="utf-8"))
VO = {l["key"]: l for l in json.load(open(os.path.join(ROOT, "assets/vo/words.edit.json"), encoding="utf-8"))["lines"]}
TAG = re.compile(r"\[[^\]]*\]\s*")
ceil_beat = lambda t: math.ceil(t / T - 1e-6) * T
norm = lambda s: re.sub(r"[^0-9a-z\-]", "", s.lower())


def pages_of(sc, keep):
    """Split scene text into subtitle pages (by '|'), dropping words cut from the audio."""
    id_pages = [TAG.sub("", p).split() for p in sc["vo"].split("|")]
    en_pages = [p.strip() for p in sc["en"].split("|")]
    flat = [(pi, w) for pi, ws in enumerate(id_pages) for w in ws]
    a, b = keep
    kept = flat[a:b]
    return id_pages, en_pages, kept


def main():
    scenes, t_end, pages = [], None, []
    rep = EP.get("display_replace", {})
    for i, sc in enumerate(EP["scenes"]):
        key, L = sc["key"], VO[sc["key"]]
        w0 = L["words"][0]
        if i == 0:
            cut, first = 0.0, 0.06
        else:
            cut = ceil_beat(t_end + GAP + sc.get("pause_before", 0))
            if sc["block"] == "twist":
                cut = max(cut, TWIST_BEAT * T)
            first = cut + LEAD
        if sc.get("pause_before"):           # countdown: the reveal scene is cut BEFORE its pause
            cut = ceil_beat(t_end + GAP)
            first = max(first, cut + sc["pause_before"])
            first = ceil_beat(first) if abs(ceil_beat(first) - first) < 0.12 else first
        a = first - w0["t"]
        words = [{"w": w["w"], "t": round(a + w["t"], 3), "e": round(a + w["e"], 3)} for w in L["words"]]
        id_pages, en_pages, kept = pages_of(sc, L.get("keep", [0, len(L["words"])]))
        assert len(kept) == len(words), (key, len(kept), len(words))
        for (pi, tw), w in zip(kept, words):
            assert norm(tw) == norm(w["w"]), (key, tw, w["w"])
            w["p"] = pi
        # subtitle pages: group kept words by page index; EN page timed to the same window
        for pi in sorted({w["p"] for w in words}):
            ws = [dict(w) for w in words if w["p"] == pi]
            txt = " ".join(x["w"] for x in ws)
            for k_, v_ in rep.items():
                if k_ in txt:
                    txt = txt.replace(k_, v_)
            pages.append({"scene": key, "t": ws[0]["t"], "e": ws[-1]["e"], "words": ws, "id": txt, "en": en_pages[pi]})
        t_end = words[-1]["e"]
        scenes.append({"key": key, "block": sc["block"], "n": sc.get("n"), "cut": round(cut, 3), "beat": round(cut / T, 2),
                       "voStart": round(a, 4), "voFile": L["file"], "speechStart": words[0]["t"], "speechEnd": t_end,
                       "raw": [{"w": w["w"], "t": w["t"], "e": w["e"]} for w in words], "facts": sc.get("facts", {})})
    # page out-times
    cuts = [s["cut"] for s in scenes] + [DURATION]
    keys = [s["key"] for s in scenes]
    for n, p in enumerate(pages):
        nxt = pages[n + 1]["t"] if n + 1 < len(pages) else DURATION
        hard = cuts[keys.index(p["scene"]) + 1] - 0.04
        p["out"] = round(min(nxt, p["e"] + 0.55, hard) if n + 1 < len(pages) else min(p["e"] + 1.0, DURATION - .2), 3)
        p["t"], p["e"] = round(p["t"], 3), round(p["e"], 3)
        # display words: apply replacements per word group (e.g. "tiga kali lipat" -> "3x lipat")
        disp, i = [], 0
        ws = p["words"]
        while i < len(ws):
            hit = False
            for k_, v_ in rep.items():
                kk = k_.split()
                if [norm(x["w"]) for x in ws[i:i + len(kk)]] == [norm(x) for x in kk]:
                    disp.append({"w": v_, "t": ws[i]["t"], "e": ws[i + len(kk) - 1]["e"]}); i += len(kk); hit = True; break
            if not hit:
                disp.append({"w": ws[i]["w"], "t": ws[i]["t"], "e": ws[i]["e"]}); i += 1
        p["words"] = disp
    # EN word timing: spread the page window over the EN words by character length
    for p in pages:
        ew = p["en"].split()
        t0, t1 = p["t"], max(p["e"], p["t"] + 0.3)
        tot = sum(len(w) + 1 for w in ew)
        acc, out = 0, []
        for w in ew:
            a_ = t0 + (t1 - t0) * acc / tot; acc += len(w) + 1; b_ = t0 + (t1 - t0) * acc / tot
            out.append({"w": w, "t": round(a_, 3), "e": round(b_, 3)})
        p["en_words"] = out
    # mouth envelope (30 fps) of the voice-over, for the mascot's lip flaps
    SR = 16000
    vo = np.zeros(int(DURATION * SR), np.float32)
    for s in scenes:
        x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(ROOT, s["voFile"]), "-ac", "1", "-ar", str(SR),
                                          "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
        i0 = int(round(s["voStart"] * SR)); x = x[max(0, -i0):]; i0 = max(0, i0)
        n = min(len(x), len(vo) - i0); vo[i0:i0 + n] += x[:n]
    hop = SR // 30
    rms = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same"))[hop // 2::hop][:int(DURATION * 30)]
    ref = np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1
    mouth = [round(float(min(1, max(0, (20 * np.log10(v / ref + 1e-9) + 30) / 26))), 2) for v in rms]
    out = {"T": T, "duration": DURATION, "scenes": scenes, "pages": pages, "mouth": mouth}
    json.dump(out, open(os.path.join(ROOT, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    for s in scenes:
        print(f"{s['key']} {s['block']:8s} cut {s['cut']:6.2f}s (beat {s['beat']:6.2f})  voice {s['speechStart']:6.2f}-{s['speechEnd']:6.2f}")
    print(f"end hold {DURATION - scenes[-1]['speechEnd']:.2f}s, {len(pages)} pages")


if __name__ == "__main__":
    main()
