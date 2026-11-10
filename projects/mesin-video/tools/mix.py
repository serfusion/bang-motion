"""Mix one episode: voice-over + SFX pins + music edited on the beat grid, ducked under the voice.

Music edit (all derived from the timeline, nothing per episode):
  0 .. countdown            song from its first full beat ('mulai'), full band
  countdown .. reveal       music drops to a muffled low-pass bed (-13 dB) under the ticks and roulette clicks
  answer word .. twist      full band slams back ON the answer word, song positioned so its beats stay on the cut grid
  twist                     stops on the record scratch, continues low-passed under the twist
  next scene (CTA) .. end   full band again, 1 s fade at the end
Levels: music -24 LUFS where nobody speaks, -10 dB under the voice (hold 0.45 s, release 0.5 s; kept big for
0.7 s on the reveal and the CTA), voice -16 LUFS, SFX peak-normalised; master -14 LUFS / -1.5 dBTP.

  python3 tools/mix.py ID   -> episodes/ID/build/mix.wav, mix-nobgm.wav, stems; episodes/ID/mix.m4a (page playback)
"""
import json, math, os, subprocess, sys
import numpy as np
from common import ENGINE, ep_dir, load_json

SR = 48000


def load(path, ch=1, ss=None, t=None, af=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", f"{ss:.4f}"] if ss is not None else []) + (["-t", f"{t:.4f}"] if t else []) + \
          ["-i", path] + (["-af", af] if af else []) + ["-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]
    x = np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, dtype=np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def write_wav(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-",
                    "-c:a", "pcm_s16le", path], input=np.ascontiguousarray(x.astype(np.float32)).tobytes(), check=True)


def lufs(x, tmp):
    write_wav(tmp, x)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", tmp, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in out.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def reverb(x, dur=0.38, wet=0.45):
    """Small synthetic room so a 70 ms tick rings instead of stopping dead."""
    n = int(dur * SR)
    ir = np.random.default_rng(7).standard_normal(n).astype(np.float32) * np.exp(-np.arange(n) / SR / 0.1).astype(np.float32)
    y = np.convolve(x, ir)
    y *= (np.max(np.abs(x)) / (np.max(np.abs(y)) + 1e-9)) * wet
    out = np.zeros(len(x) + n, np.float32); out[:len(x)] += x; out[:len(y)] += y[:len(out)]
    return out


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
    sh = (lambda v: v) if sig.ndim == 1 else (lambda v: v[:, None])
    if a > 0: sig[:a] *= sh(np.linspace(0, 1, a))
    if b > 0: sig[-b:] *= sh(np.linspace(1, 0, b))
    return sig


def main(eid):
    D = lambda *p: ep_dir(eid, *p)
    tl, ep = load_json(D("timeline.json")), load_json(D("episode.json"))
    sfx = load_json(D("sfx.json")) if os.path.exists(D("sfx.json")) else []
    os.makedirs(D("build"), exist_ok=True); tmp = D("build", "_meter.wav")
    dur, T, N = tl["duration"], tl["T"], int(round(tl["duration"] * SR))
    S = tl["scenes"]
    # ---------- voice ----------
    vo = np.zeros((N, 2), np.float32)
    for s in S:
        place(vo, load(D(s["voFile"])), s["voStart"])
    g = lufs(vo, tmp); vo *= 10 ** ((-16.0 - g) / 20)
    # ---------- SFX ----------
    fx, cache = np.zeros((N, 2), np.float32), {}
    for p in sfx:
        path = os.path.join(ENGINE, "audio", "sfx", p["src"] + ".mp3")
        if path not in cache:
            x = load(path); x = x * (10 ** (-1 / 20) / (float(np.max(np.abs(x))) or 1))
            cache[path] = (x, int(np.argmax(np.abs(x))), int(np.argmax(np.abs(x) > 0.1)))
        x, ipk, on = cache[path]; mx = p.get("max")
        if p["al"] == "pkwin":
            pre = min(ipk, int(0.012 * SR)); seg = fade(x[ipk - pre: ipk + int((mx or .08) * SR)], .003, .03)
            if p.get("rv"): seg = reverb(seg)
            place(fx, seg * p["vol"], p["t"] - pre / SR); continue
        if p["al"] == "tail" and mx:
            seg = fade(x[max(0, ipk - int(mx * SR)):ipk], 0.25, 0.02); place(fx, seg * p["vol"], p["t"] + mx - len(seg) / SR); continue
        if mx: x = fade(x[:int(mx * SR)], 0, min(0.06, mx / 4))
        place(fx, x * p["vol"], p["t"] - (ipk if p["al"] == "pk" else on) / SR)
    # ---------- music edit ----------
    song, start = os.path.join(ENGINE, "audio", "bgm", ep["musik"]["berkas"]), float(ep["musik"]["mulai"])
    bgm = np.zeros((N, 2), np.float32)
    marks = []                                                # (video time, kind)
    j = next((s for s in S if s["jenis"] == "jawaban"), None)
    tw = next((s for s in S if s["jenis"] == "twist"), None)
    pos = lambda t, t0, s0: s0 + (t - t0)                     # song position for continuous playback from (t0 -> s0)
    seg_list = []                                             # (v0, v1, song_start, lowpass)
    v, s0 = 0.0, start
    back = None
    if j:
        q = S[S.index(j) - 1]
        cd0, R = q["speechEnd"] + 0.02, j["cues"].get("jawab", j["speechStart"] + .8)
        back = math.ceil((R - 0.02) / T - 1e-6) * T                     # first beat at/after the answer (grid anchor)
        S2 = start + 16 * T                                              # a downbeat four bars in: full band
        seg_list.append((0.0, cd0 + 0.12, start, False, 0.12))           # full band until the countdown
        seg_list.append((cd0, R + 0.02, start + cd0, "bed", 0.04))       # muffled bed under 3-2-1: no dead air
        r0 = R - 0.03                                                    # full band again ON the answer word,
        v, s0 = r0, S2 - (back - r0)                                     # positioned so its beats stay on the cut grid
        back = r0
    if tw:
        i = S.index(tw); after = S[i + 1]["cut"] if i + 1 < len(S) else dur
        seg_list.append((v, tw["cut"] + 0.05, s0, False, 0.05))
        s1 = pos(tw["cut"] + 0.45, v, s0)
        seg_list.append((tw["cut"] + 0.45, after + 0.05, s1, True, 0.05))
        seg_list.append((after, dur, pos(after, v, s0), False, 0.0))
    else:
        seg_list.append((v, dur, s0, False, 0.0))
    for v0, v1, ss, lp, fo in seg_list:
        bed = lp == "bed"
        a = load(song, 2, ss, v1 - v0, af=("lowpass=f=420,lowpass=f=420" if bed else "lowpass=f=700,lowpass=f=700") if lp else None)
        if lp: a *= 10 ** ((-13 if bed else -3) / 20)
        place(bgm, fade(a, 0.12 if bed else 0.35 if lp else (0.004 if v0 > 0 else 0.0), fo), v0)
    bgm = fade(bgm, 0.0, 1.0)
    m0 = lufs(bgm, tmp); bgm *= 10 ** ((-24.0 - m0) / 20)
    env = np.sqrt(np.convolve(vo[:, 0] ** 2, np.ones(int(0.05 * SR)) / (0.05 * SR), "same"))
    talk = (env > 10 ** (-38 / 20)).astype(np.float32); B = 48
    tb = talk[:len(talk) // B * B].reshape(-1, B).max(1)
    held, hold = np.empty_like(tb), 0
    for i, on in enumerate(tb):
        hold = 450 if on > 0 else max(0, hold - 1); held[i] = 1.0 if hold > 0 else 0.0
    cta = next((s for s in S if s["jenis"] == "cta"), None)
    lift = ([(back, back + 0.7, -3.0)] if back else []) + ([(cta["cut"], cta["cut"] + 0.5, -4.0)] if cta else [])
    a_att, a_rel = np.exp(-1 / 40), np.exp(-1 / 500); gb, cur = np.empty_like(tb), 0.0
    for i, on in enumerate(held):
        tgt = -10.0 if on > 0 else 0.0; ts = i * B / SR
        for l0, l1, lv in lift:
            if l0 <= ts < l1: tgt = max(tgt, lv)
        c_ = a_att if tgt < cur else a_rel; cur = c_ * cur + (1 - c_) * tgt; gb[i] = cur
    gg = np.pad(np.repeat(gb, B), (0, N - len(gb) * B), mode="edge")
    bgm *= (10 ** (gg / 20))[:, None]
    for name, stem in (("stem-vo", vo), ("stem-fx", fx), ("stem-bgm", bgm)):
        write_wav(D("build", name + ".wav"), stem)
    for name, mix in (("mix", vo + fx + bgm), ("mix-nobgm", vo + fx)):
        raw = D("build", f"{name}-raw.wav"); write_wav(raw, mix)
        mm = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                            capture_output=True, text=True).stderr
        jn = json.loads(mm[mm.rindex("{"):mm.rindex("}") + 1])
        af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={jn['input_i']}:measured_TP={jn['input_tp']}:measured_LRA={jn['input_lra']}:"
              f"measured_thresh={jn['input_thresh']}:offset={jn['target_offset']}:linear=true")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af + ",alimiter=limit=0.79:level=false:attack=1:release=60",
                        "-ar", str(SR), D("build", f"{name}.wav")], check=True)       # safety limiter: true peak stays under -1 dBTP after AAC
        os.remove(raw)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", D("build", "mix.wav"), "-c:a", "aac", "-b:a", "192k", D("mix.m4a")], check=True)
    os.remove(tmp)
    print(f"mix: suara -16 LUFS, musik {m0:.1f} -> -24 LUFS (sebelum ducking), {len(sfx)} SFX" + (f", musik kembali {back:.2f}s" if back else ""))


if __name__ == "__main__":
    main(sys.argv[1])
