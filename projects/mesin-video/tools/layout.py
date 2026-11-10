"""Timeline for one episode: scene cuts on the music beat grid, word times, visual cues ({nama} in the script),
subtitle pages (ID + EN), mascot mouth envelope, credits.

Rules: the first word is spoken at 0.06 s; every next scene is cut on the first beat after the previous line;
a reveal (jawaban) leaves 1.25 s for the countdown; a twist leaves a short breath after the record scratch;
the video ends 2 s after the last word (time to read the credits).

  python3 tools/layout.py ID     -> episodes/ID/timeline.json
"""
import math, os, subprocess, sys
import numpy as np
from common import ep_dir, load_json, save_json, parse_vo, pages_en

GAP, LEAD, COUNTDOWN, TWIST_PAUSE, END_HOLD = 0.06, 0.03, 1.25, 0.32, 2.0


def main(eid):
    ep = load_json(ep_dir(eid, "episode.json"))
    lines = load_json(ep_dir(eid, "vo", "words.edit.json"))["lines"]
    T = 60.0 / float(ep["musik"]["bpm"])
    ceil_beat = lambda t: math.ceil(t / T - 1e-6) * T
    scenes, pages, t_end = [], [], 0.0
    for i, (sc, L) in enumerate(zip(ep["adegan"], lines)):
        _, sw = parse_vo(sc["vo"])
        if i == 0:
            cut, first = 0.0, 0.06
        else:
            cut = ceil_beat(t_end + GAP)
            pause = COUNTDOWN if sc["jenis"] == "jawaban" else TWIST_PAUSE if sc["jenis"] == "twist" else 0.0
            first = cut + max(LEAD, pause)
            if pause:
                fb = ceil_beat(first)
                first = fb if fb - first < 0.12 else first
        a = first - L["words"][0]["t"]
        words = [{"w": sw[j]["w"], "t": round(a + w["t"], 3), "e": round(a + w["e"], 3), "p": sw[j]["page"], "tag": sw[j]["tag"]}
                 for j, w in enumerate(L["words"])]
        cues = {c: words[j]["t"] for j, x in enumerate(sw) for c in x["cues"]}
        en = pages_en(sc["vo_en"])
        for p in sorted({w["p"] for w in words}):
            ws = [{"w": w["w"], "t": w["t"], "e": w["e"]} for w in words if w["p"] == p]
            pages.append({"scene": L["key"], "t": ws[0]["t"], "e": ws[-1]["e"], "words": ws,
                          "id": " ".join(w["w"] for w in ws), "en": en[p]})
        scenes.append({"key": L["key"], "jenis": sc["jenis"], "param": sc["param"], "cut": round(cut, 3), "beat": round(cut / T, 2),
                       "voStart": round(a, 4), "voFile": L["file"], "speechStart": words[0]["t"], "speechEnd": words[-1]["e"],
                       "words": words, "cues": cues})
        t_end = words[-1]["e"]
    DURATION = math.ceil((t_end + END_HOLD) * 30) / 30
    cuts = [s["cut"] for s in scenes] + [DURATION]
    keys = [s["key"] for s in scenes]
    for n, p in enumerate(pages):
        nxt = pages[n + 1]["t"] if n + 1 < len(pages) else DURATION
        hard = cuts[keys.index(p["scene"]) + 1] - 0.04
        p["out"] = round(min(nxt, p["e"] + 0.55, hard) if n + 1 < len(pages) else min(p["e"] + 1.0, DURATION - .2), 3)
        ew = p["en"].split()
        t0, t1 = p["t"], max(p["e"], p["t"] + 0.3)
        tot, acc, outw = sum(len(w) + 1 for w in ew), 0, []
        for w in ew:
            a_ = t0 + (t1 - t0) * acc / tot; acc += len(w) + 1; b_ = t0 + (t1 - t0) * acc / tot
            outw.append({"w": w, "t": round(a_, 3), "e": round(b_, 3)})
        p["en_words"] = outw
    # mouth envelope (30 fps) for the mascot's lip flaps
    SR = 16000
    vo = np.zeros(int(DURATION * SR), np.float32)
    for s in scenes:
        x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", ep_dir(eid, s["voFile"]), "-ac", "1", "-ar", str(SR),
                                          "-f", "f32le", "-"], capture_output=True).stdout, np.float32)
        i0 = int(round(s["voStart"] * SR)); x = x[max(0, -i0):]; i0 = max(0, i0)
        n = min(len(x), len(vo) - i0); vo[i0:i0 + n] += x[:n]
    hop = SR // 30
    rms = np.sqrt(np.convolve(vo ** 2, np.ones(hop) / hop, "same"))[hop // 2::hop][:int(DURATION * 30)]
    ref = np.percentile(rms[rms > 1e-4], 95) if np.any(rms > 1e-4) else 1
    mouth = [round(float(min(1, max(0, (20 * np.log10(v / ref + 1e-9) + 30) / 26))), 2) for v in rms]
    meta = {"id": eid, "judul": ep["judul"], "sumber": [s.get("singkat") or s["judul"] for s in ep["sumber"]],
            "suara": "Suara: ElevenLabs." if ep["suara"]["penyedia"] == "elevenlabs" else "",
            "musik": f"Musik: {ep['musik']['judul']} — {ep['musik']['artis']} (Mixkit)."}
    save_json(ep_dir(eid, "timeline.json"), {"T": T, "duration": DURATION, "scenes": scenes, "pages": pages, "mouth": mouth, "meta": meta}, indent=None)
    for s in scenes:
        print(f"{s['key']} {s['jenis']:8s} cut {s['cut']:6.2f}s  suara {s['speechStart']:6.2f}-{s['speechEnd']:6.2f}  isyarat {sorted(s['cues'])}")
    print(f"durasi {DURATION:.2f}s, {len(pages)} halaman subtitle")


if __name__ == "__main__":
    main(sys.argv[1])
