"""Mix the soundtrack: voice-over + SFX pins + edited BGM (ducked under the voice).

Inputs : timeline.json (VO placement), sfx.json (pin table dumped from the page),
         assets/audio/sfx/** + assets/audio/bgm/house-vibez.mp3 (copied from video-shotcraft).
Outputs: build/mix.wav, build/mix-nobgm.wav (48 kHz stereo, -14 LUFS / -1 dBTP)
         assets/audio/daun-katuk-mix.m4a (played by index.html in sync with the timeline).

BGM edit (all cuts on bar lines, 122 BPM, beat 0 = 0.069 s in the song):
  video   0.00-43.28 s  <- song beats   0-88   (intro + groove)
  video  43.28-49.18 s  <- song beats 100-112  (breakdown under "Tapi ingat")
  video  49.18-60.00 s  <- song beats 124-146  (build bar, then the drop lands on the CTA cut)
"""
import json, os, subprocess, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
SR = 48000
T = 0.49180
SONG0 = 0.069
BUILD = os.path.join(ROOT, "build")
os.makedirs(BUILD, exist_ok=True)


def load(path, ch=1):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, dtype=np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def lufs(x):
    """Integrated loudness via ffmpeg ebur128 (x: (n,2) float32)."""
    p = os.path.join(BUILD, "_tmp_meter.wav")
    write_wav(p, x)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", p, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    vals = [l for l in out.splitlines() if l.strip().startswith("I:")]
    return float(vals[-1].split()[1])


def write_wav(path, x):
    x = np.ascontiguousarray(x.astype(np.float32))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-",
                    "-c:a", "pcm_s16le", path], input=x.tobytes(), check=True)


def place(bus, sig, start):
    """Add mono/stereo signal to the stereo bus at time `start` (s); negative start trims the head."""
    i0 = int(round(start * SR))
    if sig.ndim == 1:
        sig = np.stack([sig, sig], 1)
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    n = min(len(sig), len(bus) - i0)
    if n > 0:
        bus[i0:i0 + n] += sig[:n]


def fade(sig, fin=0.0, fout=0.0):
    sig = sig.copy()
    a, b = int(fin * SR), int(fout * SR)
    if a > 0:
        r = np.linspace(0, 1, a)
        sig[:a] *= r if sig.ndim == 1 else r[:, None]
    if b > 0:
        r = np.linspace(1, 0, b)
        sig[-b:] *= r if sig.ndim == 1 else r[:, None]
    return sig


def main():
    tl = json.load(open(os.path.join(ROOT, "timeline.json"), encoding="utf-8"))
    sfx = json.load(open(os.path.join(ROOT, "sfx.json"), encoding="utf-8"))
    dur = tl["duration"]
    N = int(round(dur * SR))

    # ---------------- voice-over ----------------
    vo = np.zeros((N, 2), np.float32)
    for s in tl["scenes"]:
        sig = load(os.path.join(ROOT, s["voFile"]))
        # gentle high-pass (remove rumble) via first-order filter
        place(vo, sig, s["voStart"])
    vo_l = lufs(vo)
    vo *= 10 ** ((-16.0 - vo_l) / 20)
    print(f"VO {vo_l:.1f} LUFS -> -16.0")

    # ---------------- SFX ----------------
    fx = np.zeros((N, 2), np.float32)
    cache = {}
    for p in sfx:
        path = os.path.join(ROOT, "assets/audio/sfx", p["src"] + ".mp3")
        if path not in cache:
            x = load(path)
            pk = float(np.max(np.abs(x))) or 1.0
            x = x * (10 ** (-1 / 20) / pk)                       # peak-normalise to -1 dBFS (sound-design 4.1 #2)
            ipk = int(np.argmax(np.abs(x)))
            on = int(np.argmax(np.abs(x) > 0.1))                # first sample above -20 dB of peak
            cache[path] = (x, ipk, on)
        x, ipk, on = cache[path]
        mx = p.get("max")
        if p["al"] == "tail" and mx:                              # riser: take the window that ends at its peak
            seg = x[max(0, ipk - int(mx * SR)):ipk]
            seg = fade(seg, 0.25, 0.02)
            place(fx, seg * p["vol"], p["t"] + mx - len(seg) / SR)
            continue
        if mx:
            x = fade(x[:int(mx * SR)], 0, min(0.06, mx / 4))
        start = p["t"] - (ipk if p["al"] == "pk" else on) / SR
        place(fx, x * p["vol"], start)
    fx *= 10 ** (-3.0 / 20)                                       # SFX bus trim

    # ---------------- BGM (edited on bar lines + ducking) ----------------
    song = load(os.path.join(ROOT, "assets/audio/bgm/house-vibez.mp3"), 2)
    plan = [(0, 88, 0), (100, 112, 88), (124, 146 + 1, 100)]     # (song beat a, song beat b, video beat)
    bgm = np.zeros((N, 2), np.float32)
    for a, b, v in plan:
        i0, i1 = int((SONG0 + a * T) * SR), int((SONG0 + b * T) * SR)
        piece = fade(song[i0:i1], 0.012 if v else 0.0, 0.012)
        place(bgm, piece, v * T)
    # duck under the voice: RMS envelope of VO -> gain (attack 40 ms, release 350 ms)
    env = np.sqrt(np.convolve(vo[:, 0] ** 2, np.ones(int(0.05 * SR)) / (0.05 * SR), "same"))
    talk = (env > 10 ** (-38 / 20)).astype(np.float32)
    B = 48                                                       # smooth on 1 ms blocks, then upsample
    tb = talk[:len(talk) // B * B].reshape(-1, B).max(1)
    a_att, a_rel = np.exp(-1 / (0.04 * 1000)), np.exp(-1 / (0.35 * 1000))
    gb, cur = np.empty_like(tb), 0.0
    for i, on in enumerate(tb):                                  # one-pole attack/release in dB
        tgt = -7.0 if on > 0 else 0.0
        c = a_att if tgt < cur else a_rel
        cur = c * cur + (1 - c) * tgt
        gb[i] = cur
    g = np.repeat(gb, B)
    g = np.pad(g, (0, N - len(g)), mode="edge")
    bgm *= (10 ** (g / 20))[:, None]
    bgm = fade(bgm, 0.0, 1.0)                                    # last second fades out
    b_l = lufs(bgm)
    bgm *= 10 ** ((-27.5 - b_l) / 20)
    print(f"BGM {b_l:.1f} LUFS (ducked) -> -27.5")

    for name, stem in (("stem-vo", vo), ("stem-fx", fx), ("stem-bgm", bgm)):
        write_wav(os.path.join(BUILD, name + ".wav"), stem)       # for level checks only
    for name, mix in (("mix", vo + fx + bgm), ("mix-nobgm", vo + fx)):
        raw = os.path.join(BUILD, f"{name}-raw.wav")
        write_wav(raw, mix)
        out = os.path.join(BUILD, f"{name}.wav")
        # two-pass loudnorm to -14 LUFS / -1 dBTP (social platforms)
        m = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json",
                            "-f", "null", "-"], capture_output=True, text=True).stderr
        j = json.loads(m[m.rindex("{"):m.rindex("}") + 1])
        af = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
              f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", str(SR), out], check=True)
        print(f"{name}: in {j['input_i']} LUFS, tp {j['input_tp']} -> {out}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(BUILD, "mix.wav"), "-c:a", "aac", "-b:a", "192k",
                    os.path.join(ROOT, "assets/audio/daun-katuk-mix.m4a")], check=True)
    print("assets/audio/daun-katuk-mix.m4a written")


if __name__ == "__main__":
    main()
