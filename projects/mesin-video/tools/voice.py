"""Voice-over for one episode.

1. ElevenLabs TTS per scene with character timestamps (cached: a scene is only re-generated when its text,
   voice or settings change). The API key is never read here: in this environment a network proxy adds it to
   requests to api.elevenlabs.io; elsewhere set XI_API_KEY and it is sent as the xi-api-key header.
2. Tighten pauses (max 0.24 s; deliberate suspense pauses after "..." and "?" inside a scene), cut only at the
   quietest point of a gap, then speed up with rubberband (pitch kept). Word times follow every edit.

  python3 tools/voice.py ID [id|en]    -> episodes/ID/<lang>/vo/sK.mp3, sK.align.json, sK.edit.wav, words.edit.json
Keys: tools/elevenlabs.py tries every saved key in order (failover).
"""
import base64, hashlib, json, os, re, subprocess, sys
import numpy as np
from common import ep_dir, lang_dir, load_json, save_json, parse_vo, script, PACE
import elevenlabs

SR = 48000
TAGRE = re.compile(r"\[[^\]]*\]")


def words_from_alignment(text, al):
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    s = "".join(chars)
    assert s == text, "alignment text differs from request"
    spoken = [True] * len(s)
    for m in TAGRE.finditer(s):
        for i in range(m.start(), m.end()):
            spoken[i] = False
    out, i = [], 0
    while i < len(s):
        if not spoken[i] or s[i].isspace():
            i += 1
            continue
        j = i
        while j < len(s) and spoken[j] and not s[j].isspace():
            j += 1
        out.append({"w": s[i:j], "t": round(st[i], 3), "e": round(en[j - 1], 3)})
        i = j
    return out


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def save(path, x):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", path],
                   input=x.astype(np.float32).tobytes(), check=True)


def voice_for(ep, lang):
    return ep["suara_en"] if lang == "en" else ep["suara"]


def plan(ep, lang="id"):
    """Per scene: (key, seed, tts text, words, hash, cached?). A scene is sent to the TTS service only when its text,
    voice or settings changed since the last run, so re-rendering an edited episode costs only the edited scenes."""
    V, out, rows = voice_for(ep, lang), lang_dir(ep["id"], lang, "vo"), []
    km = elevenlabs.komersial()
    for k, sc in enumerate(ep["adegan"]):
        key, seed = f"s{k + 1}", 4200 + k
        text, words = parse_vo(script(sc, lang))
        h = hashlib.sha1(json.dumps([text, V["voice_id"], V["model"], V.get("pengaturan"), seed]).encode()).hexdigest()[:16]
        ap = os.path.join(out, key + ".align.json")
        old = load_json(ap) if os.path.exists(ap) else {}
        # mode komersial: suara lama dari kunci gratis / tak diketahui dibuat ulang dengan kunci berbayar
        cached = old.get("hash") == h and (not km or old.get("paket") == "berbayar")
        rows.append((key, seed, text, words, h, cached))
    return rows


def tts(ep, lang="id"):
    V, out, lines = voice_for(ep, lang), lang_dir(ep["id"], lang, "vo"), []
    os.makedirs(out, exist_ok=True)
    for key, seed, text, words, h, cached in plan(ep, lang):
        ap = os.path.join(out, key + ".align.json")
        d = load_json(ap) if cached else None
        if not d:
            d = elevenlabs.tts_with_timestamps(V, text, seed)
            with open(os.path.join(out, key + ".mp3"), "wb") as f:
                f.write(base64.b64decode(d.pop("audio_base64")))
            d["hash"] = h
            save_json(ap, d)
            print(f"{key}: TTS {len(text)} karakter (kunci {d.get('paket')})")
        aw = words_from_alignment(text, d["alignment"])
        assert len(aw) == len(words), (key, [w["w"] for w in aw], [w["w"] for w in words])
        lines.append({"key": key, "file": f"vo/{key}.mp3", "words": aw})
    return lines


def refine(words, env):
    """TTS alignment often starts a word inside the silence before it (and ends it late). Snap each word's start
    to the first 10 ms frame above -30 dB (re the clip's loud speech) and its end to the last such frame."""
    ref = np.percentile(env[env > 1e-5], 95) if np.any(env > 1e-5) else 1.0
    loud = 20 * np.log10(env / ref + 1e-9) > -30
    out = []
    for w in words:
        a, b = int(w["t"] * 100), max(int(w["t"] * 100) + 1, int(w["e"] * 100))
        idx = np.nonzero(loud[a:b])[0]
        t, e = w["t"], w["e"]
        if len(idx):
            t = max(t, (a + idx[0]) * 0.01 - 0.02)
            e = min(e, (a + idx[-1] + 1) * 0.01 + 0.02)
        if e - t < 0.08:
            t, e = w["t"], w["e"]
        out.append({**w, "t": round(t, 3), "e": round(e, 3)})
    return out


def edit(ep, lines, lang="id"):
    pace = PACE[ep.get("format", "tebakan")]
    CAP, SUSPENSE, QUESTION = pace["cap"], pace["suspense"], pace["question"]
    tempo = float(ep.get("tempo") or pace["tempo"] or voice_for(ep, lang).get("tempo") or 1.12)
    out_lines = []
    for L in lines:
        key = L["key"]
        x = load(lang_dir(ep["id"], lang, L["file"]))
        hop = int(0.01 * SR)
        env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
        ws = refine(L["words"], env)
        quiet = lambda t0, t1: (t0 + 0.01 * int(np.argmin(env[int(t0 * 100):max(int(t0 * 100) + 1, int(t1 * 100))]))) if t1 > t0 else t0
        seg_start, pieces, new_words, cur = max(0.0, ws[0]["t"] - 0.20), [], [], 0.0
        for i, w in enumerate(ws):
            nxt = ws[i + 1] if i + 1 < len(ws) else None
            new_words.append({"w": w["w"], "t": cur + (w["t"] - seg_start), "e": cur + (w["e"] - seg_start)})
            if nxt is None:
                end = min(len(x) / SR, w["e"] + 0.25)
                pieces.append((seg_start, end)); cur += end - seg_start
                break
            gap = nxt["t"] - w["e"]
            want = SUSPENSE if re.search(r"(\.\.\.|…)$", w["w"]) else QUESTION if w["w"].endswith("?") else min(gap, CAP)
            if abs(gap - want) < 0.03:
                continue
            keep = min(gap, want)
            q = quiet(w["e"], nxt["t"])
            c0 = min(max(q - (gap - keep) / 2, w["e"] + 0.03), nxt["t"] - 0.03 - (gap - keep))
            pieces.append((seg_start, c0)); cur += c0 - seg_start
            if want - keep > 0:
                pieces.append(("sil", want - keep)); cur += want - keep
            seg_start = c0 + (gap - keep)
        y, xf = [], 0.012
        for p in pieces:
            if p[0] == "sil":
                y.append(np.zeros(int(p[1] * SR), np.float32)); continue
            s = x[int(p[0] * SR):int(p[1] * SR)].copy()
            n = min(int(xf * SR), len(s) // 4)
            if n > 0:
                s[:n] *= np.linspace(0, 1, n); s[-n:] *= np.linspace(1, 0, n)
            y.append(s)
        raw, outp = lang_dir(ep["id"], lang, "vo", key + ".tight.wav"), lang_dir(ep["id"], lang, "vo", key + ".edit.wav")
        save(raw, np.concatenate(y))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", f"rubberband=tempo={tempo}:transients=mixed:window=standard",
                        "-ar", str(SR), outp], check=True)
        os.remove(raw)
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", outp],
                                   capture_output=True, text=True).stdout)
        nw = [{"w": w["w"], "t": round(w["t"] / tempo, 3), "e": round(w["e"] / tempo, 3)} for w in new_words]
        out_lines.append({"key": key, "file": f"vo/{key}.edit.wav", "dur": round(dur, 3), "words": nw})
        print(f"{key}: {ws[-1]['e'] - ws[0]['t']:5.2f}s -> {nw[-1]['e'] - nw[0]['t']:5.2f}s")
    save_json(lang_dir(ep["id"], lang, "vo", "words.edit.json"), {"tempo": tempo, "lang": lang, "lines": out_lines})
    print("total ucapan", round(sum(l["words"][-1]["e"] - l["words"][0]["t"] for l in out_lines), 2), "s")


if __name__ == "__main__":
    ep, lang = load_json(ep_dir(sys.argv[1], "episode.json")), (sys.argv[2] if len(sys.argv) > 2 else "id")
    edit(ep, tts(ep, lang), lang)
