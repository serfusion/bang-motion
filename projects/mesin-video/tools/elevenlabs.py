"""ElevenLabs client with key failover.

Keys come from the `kunci_api` table (panel: Kunci API), in order; XI_API_KEY from the environment is tried last.
When a key is refused because its quota is used up, it is invalid, or it is rate limited, the next key is tried and
the refused key is marked in the database. With no key configured at all the request is sent without a key header
(in this development environment a network proxy adds one).

Note: ElevenLabs allows one free account per person; several keys are meant for paid or team accounts and as a
backup, not for stacking free accounts (their abuse system disables free usage on such accounts).
"""
import json, os, sqlite3, time, urllib.error, urllib.request

API = "https://api.elevenlabs.io"
DBFILE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "konten.db"))
SWITCH = {401, 402, 403, 429}          # refusals that move on to the next key


def _db():
    if not os.path.exists(DBFILE):
        return None
    con = sqlite3.connect(DBFILE)
    con.row_factory = sqlite3.Row
    return con


def keys():
    """[(id, label, key)] in failover order; (None, 'env'/'proxy', key|None) last."""
    out = []
    con = _db()
    if con:
        try:
            out = [(r["id"], r["label"] or f"kunci {r['id']}", r["kunci"]) for r in
                   con.execute("SELECT id, label, kunci FROM kunci_api WHERE aktif=1 AND penyedia='elevenlabs' ORDER BY urutan, id")]
        except sqlite3.OperationalError:
            out = []
    if os.environ.get("XI_API_KEY"):
        out.append((None, "XI_API_KEY", os.environ["XI_API_KEY"]))
    return out or [(None, "proxy", None)]


def mark(kid, status, note=None, left=None):
    con = _db()
    if not con or kid is None:
        return
    con.execute("UPDATE kunci_api SET status=?, catatan=?, sisa=COALESCE(?, sisa), terakhir=datetime('now') WHERE id=?",
                (status, (note or "")[:300], left, kid))
    con.commit()


def _request(path, key, body=None, method=None, timeout=300):
    req = urllib.request.Request(API + path, data=json.dumps(body).encode() if body is not None else None,
                                 method=method or ("POST" if body is not None else "GET"),
                                 headers={"Content-Type": "application/json"})
    if key:
        req.add_header("xi-api-key", key)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _reason(e):
    try:
        d = json.loads(e.read().decode(errors="replace"))
        det = d.get("detail", d)
        if isinstance(det, dict):
            return det.get("status") or det.get("code") or "", det.get("message") or str(det)
        return "", str(det)
    except Exception:
        return "", str(e)


def tts_with_timestamps(voice, text, seed):
    st = voice.get("pengaturan") or {}
    body = {"text": text, "model_id": voice["model"], "language_code": st.get("language_code", "id"), "seed": seed,
            "voice_settings": {k: st[k] for k in ("stability", "similarity_boost", "style") if k in st}}
    path = f"/v1/text-to-speech/{voice['voice_id']}/with-timestamps?output_format=mp3_44100_128"
    tried = []
    for kid, label, key in keys():
        try:
            d = _request(path, key, body)
            mark(kid, "ok")
            return d
        except urllib.error.HTTPError as e:
            code, msg = _reason(e)
            tried.append(f"{label}: {e.code} {code} {msg[:120]}")
            if e.code in SWITCH:
                mark(kid, "habis" if "quota" in (code + msg).lower() else "ditolak" if e.code in (401, 403) else "dibatasi", msg)
                time.sleep(0.5)
                continue
            raise
    raise RuntimeError("Semua kunci ElevenLabs ditolak:\n  " + "\n  ".join(tried))


def check(kid=None, key=None):
    """Validate one key: remaining characters when the key may read its subscription, else just validity."""
    try:
        s = _request("/v1/user/subscription", key)
        left = int(s.get("character_limit", 0)) - int(s.get("character_count", 0))
        mark(kid, "ok", f"{s.get('tier', '')}: sisa {left} karakter", left)
        return "ok", left
    except urllib.error.HTTPError as e:
        code, msg = _reason(e)
        if e.code == 401 and "permission" in (code + msg).lower():
            try:
                _request("/v1/models", key)
                mark(kid, "ok", "valid (kunci tanpa izin baca kuota)")
                return "ok", None
            except urllib.error.HTTPError as e2:
                code, msg = _reason(e2)
        status = "habis" if "quota" in (code + msg).lower() else "ditolak"
        mark(kid, status, msg)
        return status, None
