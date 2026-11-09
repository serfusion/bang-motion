"""Tighten the expressive VO for a 60 s short: shorten long pauses (keep/insert suspense pauses on purpose),
then speed the voice up with rubberband (pitch preserved). Word timings are carried through every edit.

Run:  python3 tools/vo_edit.py            -> assets/vo/<key>.edit.wav + assets/vo/words.edit.json
"""
import json, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SR = 48000
TEMPO = float(os.environ.get("TEMPO", "1.17"))
CAP = 0.24                        # max pause between words
PAD = 0.05                        # keep this much air around each word
# deliberate pauses (seconds of silence after a word), a little drama before each reveal
AFTER = {("s2", "Jawabannya..."): 0.42, ("s5", "dari..."): 0.42, ("s8", "Hasilnya?"): 0.48}
# phrases cut from the generated audio at word boundaries: keep words [a, b) of the clip
KEEP = {"s3": (0, 17), "s6": (0, 5), "s8": (1, 30)}
TEMPO_FOR = {"s6": 1.05}           # short line: speed it up less so "wortel" keeps its final consonant


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def save(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", path],
                   input=x.astype(np.float32).tobytes(), check=True)


def main():
    W = json.load(open(os.path.join(ROOT, "assets/vo/words.json"), encoding="utf-8"))
    out_lines = []
    for L in W["lines"]:
        key, ws = L["key"], L["words"]
        a, b = KEEP.get(key, (0, len(ws)))
        ws = ws[a:b]
        x = load(os.path.join(ROOT, L["file"]))
        allw = L["words"]
        # 10 ms RMS envelope: cuts go to the quietest point, not to the (approximate) alignment time
        hop = int(0.01 * SR)
        env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
        quiet = lambda t0, t1: (t0 + 0.01 * int(np.argmin(env[int(t0 * 100):max(int(t0 * 100) + 1, int(t1 * 100))]))) if t1 > t0 else t0
        # first kept word: its own clip start, or the quietest point after the dropped word before it
        seg_start = max(0.0, ws[0]["t"] - 0.20) if a == 0 else quiet(allw[a - 1]["e"] - 0.02, ws[0]["t"] + 0.02)
        pieces, new_words, cur = [], [], 0.0
        xf = 0.012                                       # crossfade at each cut
        for i, w in enumerate(ws):
            nxt = ws[i + 1] if i + 1 < len(ws) else None
            new_words.append({"w": w["w"], "t": cur + (w["t"] - seg_start), "e": cur + (w["e"] - seg_start)})
            if nxt is None:
                end = min(len(x) / SR, w["e"] + 0.25) if b == len(allw) else quiet(w["e"] - 0.02, allw[b]["t"] + 0.02)
                pieces.append((seg_start, end)); cur += end - seg_start
                break
            gap = nxt["t"] - w["e"]
            want = AFTER.get((key, w["w"]), None)
            if want is None:
                want = min(gap, CAP)
            if abs(gap - want) < 0.03:
                continue                                  # keep as is, segment continues
            # remove (or insert) silence around the quietest point of the gap
            keep = min(gap, want)
            q = quiet(w["e"], nxt["t"])
            c0 = min(max(q - (gap - keep) / 2, w["e"] + 0.03), nxt["t"] - 0.03 - (gap - keep))
            pieces.append((seg_start, c0)); cur += c0 - seg_start
            extra = want - keep                           # inserted silence when the pause is lengthened
            if extra > 0:
                pieces.append(("sil", extra)); cur += extra
            seg_start = c0 + (gap - keep)
        # assemble with short crossfades
        y = []
        for p in pieces:
            if p[0] == "sil":
                y.append(np.zeros(int(p[1] * SR), np.float32)); continue
            s = x[int(p[0] * SR):int(p[1] * SR)].copy()
            n = min(int(xf * SR), len(s) // 4)
            if n > 0:
                s[:n] *= np.linspace(0, 1, n); s[-n:] *= np.linspace(1, 0, n)
            y.append(s)
        y = np.concatenate(y)
        raw = os.path.join(ROOT, "assets/vo", key + ".tight.wav")
        save(raw, y)
        outp = os.path.join(ROOT, "assets/vo", key + ".edit.wav")
        tempo = TEMPO_FOR.get(key, TEMPO) if TEMPO != 1.0 else 1.0
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"rubberband=tempo={tempo}:transients=mixed:window=standard",
                        "-ar", str(SR), outp], check=True)
        os.remove(raw)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", outp],
                                   capture_output=True, text=True).stdout)
        nw = [{"w": w["w"], "t": round(w["t"] / tempo, 3), "e": round(w["e"] / tempo, 3)} for w in new_words]
        out_lines.append({"key": key, "file": f"assets/vo/{key}.edit.wav", "dur": round(dur, 3), "keep": [a, b], "words": nw})
        print(f"{key}: {ws[-1]['e'] - ws[0]['t']:5.2f}s -> {nw[-1]['e'] - nw[0]['t']:5.2f}s (file {dur:.2f}s)")
    json.dump({"tempo": TEMPO, "lines": out_lines}, open(os.path.join(ROOT, "assets/vo/words.edit.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("speech total", round(sum(l["words"][-1]["e"] - l["words"][0]["t"] for l in out_lines), 2))


if __name__ == "__main__":
    main()
