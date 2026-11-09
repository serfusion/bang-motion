"""Generate the expressive voice-over with ElevenLabs (eleven_v3 + emotion tags), one clip per scene,
with character timestamps -> word timings for the subtitles.

The API key is never read here: the session's network proxy injects it into requests to
api.elevenlabs.io (header xi-api-key). On another machine set XI_API_KEY and it is sent as that header.

Run:  python3 tools/tts_el.py [s3 s5 ...]     (no args = all scenes; existing clips are reused unless named)
Out:  assets/vo/<key>.mp3, assets/vo/<key>.align.json, assets/vo/words.json
"""
import base64, json, os, re, subprocess, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
EP = json.load(open(os.path.join(ROOT, "episode.json"), encoding="utf-8"))
V = EP["voice"]
OUT = os.path.join(ROOT, "assets", "vo")
TAG = re.compile(r"\[[^\]]*\]")


def tts(text, seed):
    body = json.dumps({"text": text, "model_id": V["model"], "language_code": V["language_code"],
                       "voice_settings": V["settings"], "seed": seed}).encode()
    req = urllib.request.Request(
        f"https://api.elevenlabs.io/v1/text-to-speech/{V['voice_id']}/with-timestamps?output_format=mp3_44100_128",
        data=body, method="POST", headers={"Content-Type": "application/json"})
    if os.environ.get("XI_API_KEY"):
        req.add_header("xi-api-key", os.environ["XI_API_KEY"])
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def words_from_alignment(text, al):
    """Map every spoken word (tags removed) to the start/end time of its characters."""
    chars, st, en = al["characters"], al["character_start_times_seconds"], al["character_end_times_seconds"]
    s = "".join(chars)
    assert s == text, "alignment text differs from request"
    spoken = [True] * len(s)
    for m in TAG.finditer(s):
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


def main():
    only = set(sys.argv[1:])
    os.makedirs(OUT, exist_ok=True)
    res = []
    for k, sc in enumerate(EP["scenes"]):
        key = sc["key"]
        text = " ".join(sc["vo"].replace("|", " ").split())
        ap = os.path.join(OUT, key + ".align.json")
        if only and key not in only and os.path.exists(ap) or (not only and os.path.exists(ap)):
            d = json.load(open(ap, encoding="utf-8"))
        else:
            d = tts(text, seed=4200 + k)
            open(os.path.join(OUT, key + ".mp3"), "wb").write(base64.b64decode(d.pop("audio_base64")))
            json.dump(d, open(ap, "w", encoding="utf-8"), ensure_ascii=False)
        words = words_from_alignment(text, d["alignment"])
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                    os.path.join(OUT, key + ".mp3")], capture_output=True, text=True).stdout)
        res.append({"key": key, "text": text, "file": f"assets/vo/{key}.mp3", "dur": round(dur, 3), "words": words})
        print(f"{key}: {words[0]['t']:.2f}-{words[-1]['e']:.2f}s of {dur:.2f}s  ({len(words)} words)")
    json.dump({"voice": V, "lines": res}, open(os.path.join(OUT, "words.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("speech total", round(sum(r["words"][-1]["e"] - r["words"][0]["t"] for r in res), 2), "s")


if __name__ == "__main__":
    main()
