"""Mix v2: expressive voice-over + SFX pins + edited music (ducked under the voice).

Music: "Kids" — Michael Ramir C. (Mixkit Stock Music Free License), 171.8 BPM, bar = 1.397 s.
  video 0 .. countdown      <- song from bar 8 (11.46 s, full band from the first frame)
  countdown .. reveal       -> music drops out (ticks + roulette clicks in the clear)
  reveal beat .. twist cut  <- song restarts from bar 8 on the first beat at "DAUN INI!" (cut grid unchanged)
  twist cut                 -> vinyl-scratch SFX, music stops, then the song's break (bar 39) low-passed under the story
  CTA cut .. 60 s           <- song placed so its final chord (85.51 s) lands just after the last word
Outputs: build/mix.wav, build/mix-nobgm.wav (48 kHz stereo, -14 LUFS / -1.5 dBTP), assets/audio/mix.m4a
"""
import json, math, os, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SR = 48000
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)
SONG = os.path.join(ROOT, "assets/audio/bgm/kids.mp3")
BAR8, BREAK, FINAL_HIT = 11.46, 54.77, 85.51          # song positions (s)


def load(path, ch=1, ss=None, t=None, af=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.4f}"] if ss is not None else []) + (["-t", f"{t:.4f}"] if t else []) + \
          ["-i", path] + (["-af", af] if af else []) + ["-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def write_wav(path, x):
    x = np.ascontiguousarray(x.astype(np.float32))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-",
                    "-c:a", "pcm_s16le", path], input=x.tobytes(), check=True)


def lufs(x):
    p = os.path.join(BUILD, "_meter.wav"); write_wav(p, x)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def place(bus, sig, start):
    i0 = int(round(start * SR))
    if sig.ndim == 1:
        sig = np.stack([sig, sig], 1)
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    n = min(len(sig), len(bus) - i0)
    if n > 0:
        bus[i0:i0 + n] += sig[:n]


def fade(sig, fin=0.0, fout=0.0):
    sig = sig.copy(); a, b = int(fin * SR), int(fout * SR)
    if a > 0: sig[:a] *= (np.linspace(0, 1, a) if sig.ndim == 1 else np.linspace(0, 1, a)[:, None])
    if b > 0: sig[-b:] *= (np.linspace(1, 0, b) if sig.ndim == 1 else np.linspace(1, 0, b)[:, None])
    return sig


def main():
    tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
    sfx_path = os.path.join(ROOT, "sfx.json")
    sfx = json.load(open(sfx_path, encoding="utf-8")) if os.path.exists(sfx_path) else []
    dur, T = tl["duration"], tl["T"]
    N = int(round(dur * SR))
    sc = {s["block"] if s["block"] in ("twist", "cta") else s["key"]: s for s in tl["scenes"]}
    twist, cta = sc["twist"]["cut"], sc["cta"]["cut"]
    last_word = tl["scenes"][-1]["speechEnd"]

    # ---------- voice ----------
    vo = np.zeros((N, 2), np.float32)
    for s in tl["scenes"]:
        place(vo, load(os.path.join(ROOT, s["voFile"])), s["voStart"])
    g = lufs(vo); vo *= 10 ** ((-16.0 - g) / 20); print(f"VO {g:.1f} -> -16 LUFS")

    # ---------- SFX ----------
    fx = np.zeros((N, 2), np.float32); cache = {}
    for p in sfx:
        path = os.path.join(ROOT, "assets/audio/sfx", p["src"] + ".mp3")
        if path not in cache:
            x = load(path); x = x * (10 ** (-1 / 20) / (float(np.max(np.abs(x))) or 1))
            cache[path] = (x, int(np.argmax(np.abs(x))), int(np.argmax(np.abs(x) > 0.1)))
        x, ipk, on = cache[path]; mx = p.get("max")
        if p["al"] == "pkwin":                       # one transient cut out of a longer file, its peak on the pin
            pre = min(ipk, int(0.012 * SR)); seg = fade(x[ipk - pre: ipk + int((mx or 0.08) * SR)], 0.003, 0.03)
            place(fx, seg * p["vol"], p["t"] - pre / SR); continue
        if p["al"] == "tail" and mx:
            seg = fade(x[max(0, ipk - int(mx * SR)):ipk], 0.25, 0.02); place(fx, seg * p["vol"], p["t"] + mx - len(seg) / SR); continue
        if mx: x = fade(x[:int(mx * SR)], 0, min(0.06, mx / 4))
        place(fx, x * p["vol"], p["t"] - (ipk if p["al"] == "pk" else on) / SR)

    # ---------- music edit ----------
    bgm = np.zeros((N, 2), np.float32)
    # full band from the first frame; it drops out for the countdown + roulette and slams back on the beat of the reveal
    s1 = tl["scenes"][0]; s2 = tl["scenes"][1]
    cd0 = s1["raw"][-1]["e"] + 0.02                                          # countdown starts after "banyak?"
    rv = next(w["t"] for w in s2["raw"] if w["w"].upper().startswith("DAUN"))
    back = math.ceil((rv - 0.02) / T - 1e-6) * T                            # first beat at the reveal (keeps the cut grid)
    a1 = load(SONG, 2, BAR8, cd0 + 0.12)
    place(bgm, fade(a1, 0.0, 0.12), 0.0)
    a2 = load(SONG, 2, BAR8, twist + 0.05 - back)                           # restart on a downbeat (bar 8) at the reveal
    place(bgm, fade(a2, 0.004, 0.05), back)
    print(f"music out {cd0:.2f}s (countdown), back {back:.3f}s (reveal word at {rv:.3f}s)")
    gap = 0.45                                                               # dead air after the scratch
    b = load(SONG, 2, BREAK, cta - twist - gap + 0.05, af="lowpass=f=700,lowpass=f=700")
    place(bgm, fade(b, 0.35, 0.05) * 10 ** (-3 / 20), twist + gap)          # muffled under the Taiwan story
    hit_v = min(dur - 0.6, round((last_word + 0.15) / T) * T)               # final chord on a beat after the last word
    c_start = FINAL_HIT - (hit_v - cta)
    c = load(SONG, 2, c_start, dur - cta)
    place(bgm, fade(c, 0.03, 0.0), cta)
    bgm = fade(bgm, 0.0, 0.5)
    m0 = lufs(bgm); bgm *= 10 ** ((-24.0 - m0) / 20)                         # level where nobody speaks
    # duck under the voice (1 ms blocks, attack 40 ms, hold 450 ms, release 500 ms) -> music ~-34 LUFS under speech
    env = np.sqrt(np.convolve(vo[:, 0] ** 2, np.ones(int(0.05 * SR)) / (0.05 * SR), "same"))
    talk = (env > 10 ** (-38 / 20)).astype(np.float32); B = 48
    tb = talk[:len(talk) // B * B].reshape(-1, B).max(1)
    held, hold = np.empty_like(tb), 0
    for i, on in enumerate(tb):                                              # hold: short pauses between words stay ducked
        hold = 450 if on > 0 else max(0, hold - 1); held[i] = 1.0 if hold > 0 else 0.0
    a_att, a_rel = np.exp(-1 / 40), np.exp(-1 / 500); gb, cur = np.empty_like(tb), 0.0
    lift = [(back, back + 0.7, -3.0), (cta, cta + 0.5, -4.0)]                 # the music "drop" on the reveal and the CTA stays big
    for i, on in enumerate(held):
        tgt = -10.0 if on > 0 else 0.0; ts_ = i * B / SR
        for l0, l1, lv in lift:
            if l0 <= ts_ < l1: tgt = max(tgt, lv)
        c_ = a_att if tgt < cur else a_rel; cur = c_ * cur + (1 - c_) * tgt; gb[i] = cur
    gg = np.pad(np.repeat(gb, B), (0, N - len(gb) * B), mode="edge")
    bgm *= (10 ** (gg / 20))[:, None]
    m = lufs(bgm); print(f"music {m0:.1f} -> -24 LUFS before ducking, {m:.1f} LUFS after  final chord at {hit_v:.2f}s")

    for name, stem in (("stem-vo", vo), ("stem-fx", fx), ("stem-bgm", bgm)):
        write_wav(os.path.join(BUILD, name + ".wav"), stem)
    for name, mix in (("mix", vo + fx + bgm), ("mix-nobgm", vo + fx)):
        raw = os.path.join(BUILD, f"{name}-raw.wav"); write_wav(raw, mix)
        mm = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        j = json.loads(mm[mm.rindex("{"):mm.rindex("}") + 1])
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
              f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), os.path.join(BUILD, f"{name}.wav")], check=True)
        print(f"{name}: in {j['input_i']} LUFS")
    os.makedirs(os.path.join(ROOT, "assets/audio"), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(BUILD, "mix.wav"), "-c:a", "aac", "-b:a", "192k",
                    os.path.join(ROOT, "assets/audio/mix.m4a")], check=True)


if __name__ == "__main__":
    main()
