"""ElevenLabs client with key failover.

Keys come from the `kunci_api` table (panel: Kunci API), in order; XI_API_KEY from the environment is tried last.
When a key is refused because its quota is used up, it is invalid, or it is rate limited, the next key is tried and
the refused key is marked in the database. With no key configured at all the request is sent without a key header
(in this development environment a network proxy adds one).

Commercial mode (pengaturan.komersial = 1 or env MESIN_KOMERSIAL=1): only keys marked paket='berbayar' are used,
still in failover order, so videos meant for monetization never use a free-plan key (free plan = non-commercial,
attribution required). Each TTS result records the plan of the key that made it (paket).

Note: ElevenLabs allows one free account per person; several keys are meant for paid or team accounts and as a
backup, not for stacking free accounts (their abuse system disables free usage on such accounts).
"""
import json, os, sqlite3, time, urllib.error, urllib.request

API = "https://api.elevenlabs.io"
DBFILE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "db", "konten.db"))
SWITCH = {401, 402, 403, 429}          # refusals that move on to the next key
_SKIP = set()                          # keys refused earlier in this process (one render = one process): not retried


def _db():
    if not os.path.exists(DBFILE):
        return None
    con = sqlite3.connect(DBFILE)
    con.row_factory = sqlite3.Row
    return con


def setting(name, default=None):
    con = _db()
    if not con:
        return default
    try:
        r = con.execute("SELECT nilai FROM pengaturan WHERE kunci=?", (name,)).fetchone()
        return r["nilai"] if r else default
    except sqlite3.OperationalError:
        return default


def komersial():
    """True when voices must come from paid-plan keys only (videos to be monetized)."""
    env = os.environ.get("MESIN_KOMERSIAL")
    return env == "1" if env is not None else setting("komersial", "0") == "1"


def keys(commercial=None):
    """[(id, label, key, paket)] in failover order; (None, 'XI_API_KEY'/'proxy', key|None, paket) last.
    In commercial mode only keys with paket 'berbayar' are returned (possibly none)."""
    km = komersial() if commercial is None else commercial
    out = []
    con = _db()
    if con:
        try:
            out = [(r["id"], r["label"] or f"kunci {r['id']}", r["kunci"], r["paket"] or "") for r in
                   con.execute("SELECT id, label, kunci, paket FROM kunci_api WHERE aktif=1 AND penyedia='elevenlabs' ORDER BY urutan, id")]
        except sqlite3.OperationalError:
            try:
                out = [(r["id"], r["label"] or f"kunci {r['id']}", r["kunci"], "") for r in
                       con.execute("SELECT id, label, kunci FROM kunci_api WHERE aktif=1 AND penyedia='elevenlabs' ORDER BY urutan, id")]
            except sqlite3.OperationalError:
                out = []
    if os.environ.get("XI_API_KEY"):
        out.append((None, "XI_API_KEY", os.environ["XI_API_KEY"], os.environ.get("XI_API_PAKET", "")))
    if km:
        return [k for k in out if k[3] == "berbayar"]
    return out or [(None, "proxy", None, "")]


def mark(kid, status, note=None, left=None, paket=None):
    con = _db()
    if not con or kid is None:
        return
    try:
        con.execute("UPDATE kunci_api SET status=?, catatan=?, sisa=COALESCE(?, sisa), paket=COALESCE(?, paket), "
                    "terakhir=datetime('now') WHERE id=?", (status, (note or "")[:300], left, paket, kid))
    except sqlite3.OperationalError:          # database lama tanpa kolom paket
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
    tried, ks = [], keys()
    if not ks:
        raise RuntimeError("Mode komersial aktif, tetapi belum ada kunci aktif berpaket berbayar. "
                           "Tandai kunci berbayar di panel (Kunci API) atau matikan mode komersial.")
    for kid, label, key, paket in ks:
        if (kid, key) in _SKIP:
            continue
        for attempt in range(3):
            try:
                d = _request(path, key, body)
                mark(kid, "ok")
                d["paket"] = paket or "tidak diketahui"
                return d
            except urllib.error.HTTPError as e:
                code, msg = _reason(e)
                if e.code == 429 and "quota" not in (code + msg).lower() and attempt < 2:
                    time.sleep(2 + 3 * attempt)          # rate limited: wait a moment, same key
                    continue
                tried.append(f"{label}: {e.code} {code} {msg[:120]}")
                if e.code in SWITCH:
                    mark(kid, "habis" if "quota" in (code + msg).lower() else "ditolak" if e.code in (401, 403) else "dibatasi", msg)
                    _SKIP.add((kid, key))
                    break
                raise
    raise RuntimeError("Semua kunci ElevenLabs ditolak:\n  " + "\n  ".join(tried))


def check(kid=None, key=None):
    """Validate one key: remaining characters when the key may read its subscription, else just validity."""
    try:
        s = _request("/v1/user/subscription", key)
        left = int(s.get("character_limit", 0)) - int(s.get("character_count", 0))
        tier = (s.get("tier") or "").lower()
        mark(kid, "ok", f"{tier}: sisa {left} karakter", left, ("gratis" if tier == "free" else "berbayar") if tier else None)
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
