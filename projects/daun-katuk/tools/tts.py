"""Generate the Indonesian voice-over, one clip per scene, with word timings.

Voice: Microsoft Edge neural TTS, id-ID-ArdiNeural (via the edge-tts package).
Output: assets/vo/s{n}.mp3 + assets/vo/words.json (per-word offsets, seconds).
Run:    python3 tools/tts.py            (from projects/daun-katuk)
"""
import asyncio, json, os, ssl, subprocess, sys
import edge_tts
import edge_tts.communicate as _ec

# Behind a TLS-intercepting proxy edge-tts must trust the proxy CA as well.
CA = os.environ.get("SSL_CERT_FILE") or "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    _ec._SSL_CTX = ssl.create_default_context(cafile=CA)

VOICE = "id-ID-ArdiNeural"
RATE = os.environ.get("RATE", "+0%")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "assets", "vo")

sys.path.insert(0, HERE)
from script import LINES, speech  # noqa: E402

async def gen(key, text):
    c = edge_tts.Communicate(text, VOICE, rate=RATE, boundary="WordBoundary")
    words, path = [], os.path.join(OUT, f"{key}.mp3")
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio":
                f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "t": round(ch["offset"] / 1e7, 3),
                              "d": round(ch["duration"] / 1e7, 3)})
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", path], capture_output=True, text=True).stdout)
    return {"key": key, "text": text, "file": f"assets/vo/{key}.mp3", "dur": round(dur, 3), "words": words}

async def main():
    os.makedirs(OUT, exist_ok=True)
    res = []
    for key, text in LINES:
        text = speech(text)
        r = await gen(key, text)
        sp = r["words"][-1]["t"] + r["words"][-1]["d"] - r["words"][0]["t"]
        print(f"{key}: speech {sp:5.2f}s  file {r['dur']:.2f}s  | {text}")
        res.append(r)
    with open(os.path.join(OUT, "words.json"), "w", encoding="utf-8") as f:
        json.dump({"voice": VOICE, "rate": RATE, "lines": res}, f, ensure_ascii=False, indent=1)
    tot = sum(r["words"][-1]["t"] + r["words"][-1]["d"] - r["words"][0]["t"] for r in res)
    print(f"total speech {tot:.2f}s")

asyncio.run(main())
