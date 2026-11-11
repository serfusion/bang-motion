"""Panel web mesin video: database konten, editor episode, kunci API ElevenLabs, antrean render.

  pip install -r requirements.txt
  python3 panel/app.py                        # buka http://127.0.0.1:5000
  python3 panel/app.py --port 8080
  PANEL_PASSWORD=rahasia python3 panel/app.py --host 0.0.0.0     # bila dibuka dari perangkat lain di jaringan

Dengan PANEL_PASSWORD, panel terkunci: pengunjung melihat halaman "Masukkan kunci" (/masuk) dan setelah kunci benar
mendapat sesi cookie 7 hari. Formulir kunci di portofolio (superfal-dev.com, tab Innovation) mengirim ke /studio/masuk.
Kunci tidak pernah ditulis di repo: hanya di lingkungan server (/etc/superfal/panel.env).

Data tersimpan di db/konten.db (tidak di-commit; dibuat dari db/data/*.json saat pertama kali dijalankan).
"Simpan ke JSON" menulis isi database kembali ke db/data/*.json untuk git; kunci API tidak pernah ikut.
Tombol render memasukkan tugas ke antrean; satu pekerja di latar belakang menjalankan tools/make_video.py.
"""
import argparse, contextlib, hashlib, hmac, io, json, os, re, secrets, signal, sqlite3, subprocess, sys, threading, time
from datetime import datetime, timedelta
from flask import Flask, Response, abort, flash, g, jsonify, redirect, render_template, request, send_file, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(PROJ, "tools"))
sys.path.insert(0, HERE)
import db as dbt                                                    # noqa: E402  tools/db.py
import elevenlabs                                                   # noqa: E402  tools/elevenlabs.py
from common import (DBFILE, ENGINE, EPISODES, FORMAT_SCENES, LANGS, SCENE_TYPES,  # noqa: E402
                    fluent_set, icon_svg)
import templat                                                      # noqa: E402  panel/templat.py

LOGDIR = os.path.join(HERE, "log")
MAKE = os.path.join(PROJ, "tools", "make_video.py")
STEPS = ["export", "voice", "layout", "page", "sfx", "mix", "render", "final"]
WEIGHT = {"export": 1, "voice": 6, "layout": 1, "page": 1, "sfx": 3, "mix": 4, "render": 70, "final": 14}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{1,60}$")
BAHASA = {"id": "Indonesia", "en": "English"}
STATUS_EP = ["draf", "siap", "dirender", "terbit"]
KEY_SLOTS = 4
POLICY_URL = "https://elevenlabs.io/docs/help-center/account/general/can-users-have-more-than-one-account"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 60 * 1024 * 1024
# di balik Nginx (mis. superfal-dev.com/studio/): alamat & awalan diambil dari header X-Forwarded-*
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)


def _secret():
    p = os.path.join(HERE, ".rahasia")
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(secrets.token_hex(32))
        os.chmod(p, 0o600)
    return open(p).read().strip()


app.secret_key = os.environ.get("PANEL_SECRET") or _secret()
app.config.update(SESSION_COOKIE_NAME="studio", SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=bool(os.environ.get("PANEL_PUBLIK")), PERMANENT_SESSION_LIFETIME=timedelta(days=7))


# ------------------------------------------------------------------ database
def con():
    if "con" not in g:
        g.con = dbt.connect()
    return g.con


@app.teardown_appcontext
def _close(_exc):
    c = g.pop("con", None)
    if c is not None:
        c.close()


def q(sql, *a):
    return con().execute(sql, a).fetchall()


def q1(sql, *a):
    return con().execute(sql, a).fetchone()


def episode_or_404(eid, full=True):
    if not q1("SELECT 1 FROM episode WHERE id=?", eid):
        abort(404)
    return dbt.load_episode(con(), eid, full)


# ------------------------------------------------------------------ keamanan: kunci (PANEL_PASSWORD) + token formulir
TERBUKA = {"masuk", "static"}               # boleh dibuka tanpa kunci
GAGAL, GAGAL_LOCK = {}, threading.Lock()    # ip -> waktu-waktu kunci salah (memori proses)
GAGAL_BATAS, GAGAL_JENDELA = 8, 15 * 60     # 8 kali salah dalam 15 menit -> IP itu ditahan sampai jendela lewat


def _kunci_cocok(k):
    pw = os.environ.get("PANEL_PASSWORD") or ""
    return bool(pw) and hmac.compare_digest((k or "").encode(), pw.encode())


def _tanda():
    """Penanda sesi yang terikat pada kunci saat ini: kunci diganti = semua sesi lama keluar."""
    sk = app.secret_key if isinstance(app.secret_key, bytes) else str(app.secret_key).encode()
    return hmac.new(sk, (os.environ.get("PANEL_PASSWORD") or "").encode(), hashlib.sha256).hexdigest()[:32]


def _sudah_masuk():
    return hmac.compare_digest(str(session.get("masuk", "")), _tanda())


def _mau_json():
    return "application/json" in request.headers.get("Accept", "")


def _gagal(ip, catat=False):
    now = time.time()
    with GAGAL_LOCK:
        if len(GAGAL) > 5000:
            GAGAL.clear()
        t = [x for x in GAGAL.get(ip, []) if now - x < GAGAL_JENDELA] + ([now] if catat else [])
        GAGAL[ip] = t
        return len(t)


def _aman(ke):
    """Tujuan setelah masuk: hanya path di dalam panel (tidak boleh melompat ke situs lain)."""
    ke = (ke or "").strip()
    return ke if ke.startswith("/") and not ke.startswith("//") and not re.search(r"[\\\s]", ke) else ""


@app.before_request
def _guard():
    pw = os.environ.get("PANEL_PASSWORD")
    if not pw and request.headers.get("X-Forwarded-For"):
        abort(403, description="Panel dibuka lewat internet tanpa PANEL_PASSWORD. Setel kunci dulu.")
    if pw and request.endpoint not in TERBUKA and not _sudah_masuk():
        a = request.authorization                 # Basic auth tetap diterima (skrip / curl -u)
        if not (a and _kunci_cocok(a.password)):
            if a:
                time.sleep(1.2)
            if _mau_json() or request.path.startswith("/api/"):
                return jsonify(ok=False, pesan="Butuh kunci."), 401
            ke = request.full_path.rstrip("?")
            return redirect(url_for("masuk", ke=ke if ke not in ("/", "") else None))
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    if request.method == "POST" and request.endpoint != "masuk":
        tok = request.form.get("_csrf") or request.headers.get("X-CSRF", "")
        if not hmac.compare_digest(tok.encode(), session["csrf"].encode()):
            abort(400, description="Formulir kedaluwarsa. Muat ulang halaman lalu coba lagi.")


@app.after_request
def _header(r):
    r.headers.setdefault("X-Content-Type-Options", "nosniff")
    r.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    r.headers.setdefault("Referrer-Policy", "same-origin")
    r.headers.setdefault("X-Robots-Tag", "noindex, nofollow")
    if request.endpoint == "ikon":               # SVG unggahan dibuka langsung: tanpa skrip
        r.headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'; img-src data:; sandbox"
    return r


@app.route("/masuk", methods=["GET", "POST"])
def masuk():
    ke = _aman(request.values.get("ke"))
    tujuan = (request.script_root + ke) if ke else url_for("dasbor")
    if not os.environ.get("PANEL_PASSWORD") or (request.method == "GET" and _sudah_masuk()):
        return redirect(tujuan)
    if request.method == "GET":
        return render_template("masuk.html", galat=None, ke=ke)
    ip = request.remote_addr or "?"
    if _gagal(ip) >= GAGAL_BATAS:
        msg = "Terlalu banyak percobaan. Coba lagi 15 menit lagi."
        if _mau_json():
            return jsonify(ok=False, kode="batas", pesan=msg), 429
        return render_template("masuk.html", galat=msg, ke=ke), 429
    if _kunci_cocok(request.form.get("kunci", "")):
        with GAGAL_LOCK:
            GAGAL.pop(ip, None)
        session.clear()
        session.permanent = True
        session["masuk"], session["csrf"] = _tanda(), secrets.token_hex(16)
        return jsonify(ok=True, ke=tujuan) if _mau_json() else redirect(tujuan)
    _gagal(ip, catat=True)
    time.sleep(1.2)                               # memperlambat tebak-tebakan
    if _mau_json():
        return jsonify(ok=False, kode="salah", pesan="Kunci salah."), 401
    return render_template("masuk.html", galat="Kunci salah.", ke=ke), 401


@app.route("/keluar", methods=["POST"])
def keluar():
    session.clear()
    return redirect(url_for("masuk"))


@app.context_processor
def _ctx():
    n = q1("SELECT COUNT(*) n FROM tugas WHERE status IN ('antre','jalan')")["n"]
    return {"csrf": session.get("csrf", ""), "antre_n": n, "BAHASA": BAHASA, "FORMATS": templat.FORMATS,
            "nav": g.get("nav", ""), "mask": mask, "berkunci": bool(os.environ.get("PANEL_PASSWORD"))}


@app.template_filter("angka")
def _angka(n):
    return f"{n:,}".replace(",", ".") if isinstance(n, (int, float)) else (n or "")


@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(413)
def _err(e):
    return render_template("pesan.html", judul=f"{e.code}", pesan=e.description), e.code


def mask(k):
    return f"{k[:4]}…{k[-4:]}" if k and len(k) > 12 else ("…" if k else "")


# ------------------------------------------------------------------ bantu
def hasil(eid):
    """Berkas keluaran per bahasa yang sudah ada di disk (path relatif terhadap episodes/)."""
    out = {}
    for lang in LANGS:
        base = os.path.join(EPISODES, eid, lang)
        names = {"mp4": f"out/{eid}-{lang}.mp4", "nobgm": f"out/{eid}-{lang}-tanpa-musik.mp4", "srt": f"out/{eid}-{lang}.srt",
                 "html": "index.html", "mix": "mix.m4a"}
        r = {k: f"{eid}/{lang}/{v}" for k, v in names.items() if os.path.exists(os.path.join(base, v))}
        if "mp4" in r:
            r["waktu"] = datetime.fromtimestamp(os.path.getmtime(os.path.join(base, names["mp4"]))).strftime("%d-%m-%Y %H:%M")
        tlp = os.path.join(base, "timeline.json")
        if os.path.exists(tlp):
            try:
                r["durasi"] = json.load(open(tlp)).get("duration")
            except ValueError:
                pass
        out[lang] = r
    return out


def has_en(ep):
    return any((sc.get("vo_en") or "").strip() for sc in ep["adegan"])


def rencana_tts(ep):
    """Karakter yang akan dikirim ke ElevenLabs per bahasa (adegan yang teksnya tidak berubah memakai cache)."""
    import voice
    out = {}
    for lang in LANGS:
        if lang == "en" and not has_en(ep):
            continue
        if not voice.voice_for(ep, lang):
            out[lang] = {"galat": "suara belum dipilih"}
            continue
        try:
            rows = voice.plan(ep, lang)
        except Exception as e:                       # naskah salah format: ditampilkan, bukan error 500
            out[lang] = {"galat": str(e)}
            continue
        out[lang] = {"total": sum(len(r[2]) for r in rows), "baru": sum(len(r[2]) for r in rows if not r[5]),
                     "adegan_baru": sum(1 for r in rows if not r[5]), "n": len(rows)}
    return out


def kirim_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# ------------------------------------------------------------------ dasbor
@app.route("/")
def dasbor():
    g.nav = "dasbor"
    kat = q("""SELECT k.id, k.nama, k.nama_en, k.deskripsi,
                 (SELECT COUNT(*) FROM episode e WHERE e.kategori_id=k.id AND e.format='tebakan') teb,
                 (SELECT COUNT(*) FROM episode e WHERE e.kategori_id=k.id AND e.format='fakta') fak,
                 (SELECT COUNT(*) FROM fakta f WHERE f.kategori_id=k.id) nf
               FROM kategori k ORDER BY k.nama""")
    hit = {t: q1(f"SELECT COUNT(*) n FROM {t}")["n"] for t in ("episode", "fakta", "sumber", "kategori", "aset", "musik", "suara")}
    per_format = {r["format"]: r["n"] for r in q("SELECT format, COUNT(*) n FROM episode GROUP BY format")}
    per_status = {r["status"]: r["n"] for r in q("SELECT status, COUNT(*) n FROM episode GROUP BY status")}
    tugas = [dict(r, **kemajuan(r)) for r in q("SELECT t.*, e.judul FROM tugas t LEFT JOIN episode e ON e.id=t.episode_id ORDER BY t.id DESC LIMIT 6")]
    kunci = q("SELECT * FROM kunci_api WHERE penyedia='elevenlabs' ORDER BY urutan, id")
    renders = q("""SELECT r.*, e.judul FROM render r JOIN episode e ON e.id=r.episode_id
                   WHERE r.bahasa NOT LIKE '%tanpa-musik' ORDER BY r.dibuat DESC LIMIT 8""")
    return render_template("dasbor.html", kat=kat, hit=hit, per_format=per_format, per_status=per_status, tugas=tugas,
                           kunci=kunci, renders=renders, env_key=bool(os.environ.get("XI_API_KEY")))


@app.route("/json/simpan", methods=["POST"])
def json_simpan():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        dbt.cmd_dump()
    flash("Database ditulis ke db/data/*.json (siap di-commit). " + buf.getvalue().strip(), "ok")
    return redirect(request.referrer or url_for("dasbor"))


@app.route("/json/muat", methods=["POST"])
def json_muat():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        dbt.cmd_import()
    flash("Isi db/data/*.json dimuat ke database. " + buf.getvalue().strip(), "ok")
    return redirect(request.referrer or url_for("dasbor"))


# ------------------------------------------------------------------ episode
@app.route("/episode")
def episode_daftar():
    g.nav = "episode"
    f = {k: request.args.get(k, "").strip() for k in ("q", "kategori", "format", "status")}
    sql = ("SELECT e.*, k.nama kat, (SELECT COUNT(*) FROM adegan a WHERE a.episode_id=e.id) n, "
           "(SELECT COUNT(*) FROM adegan a WHERE a.episode_id=e.id AND TRIM(a.vo_en)!='') n_en "
           "FROM episode e LEFT JOIN kategori k ON k.id=e.kategori_id WHERE 1=1")
    args = []
    if f["q"]:
        sql += " AND (e.judul LIKE ? OR e.judul_en LIKE ? OR e.id LIKE ?)"
        args += [f"%{f['q']}%"] * 3
    for k, col in (("kategori", "e.kategori_id"), ("format", "e.format"), ("status", "e.status")):
        if f[k]:
            sql += f" AND {col}=?"
            args.append(f[k])
    rows = q(sql + " ORDER BY e.dibuat DESC, e.id", *args)
    return render_template("episode_daftar.html", rows=rows, f=f, hs={r["id"]: hasil(r["id"]) for r in rows},
                           kategori=q("SELECT id, nama FROM kategori ORDER BY nama"), statuses=STATUS_EP)


def _default(table, prefer):
    for p in prefer:
        if p and q1(f"SELECT 1 FROM {table} WHERE id=?", p):
            return p
    r = q1(f"SELECT id FROM {table} ORDER BY rowid LIMIT 1")
    return r["id"] if r else None


@app.route("/episode/baru", methods=["POST"])
def episode_baru():
    F = request.form
    eid, fmt = F.get("id", "").strip().lower(), F.get("format", "tebakan")
    if not SLUG.match(eid):
        flash("ID episode: huruf kecil, angka dan tanda hubung saja, mis. 'sains-petir'.", "galat")
        return redirect(url_for("episode_daftar"))
    if q1("SELECT 1 FROM episode WHERE id=?", eid):
        flash(f"Episode '{eid}' sudah ada.", "galat")
        return redirect(url_for("episode_edit", eid=eid))
    if fmt not in templat.FORMATS:
        abort(400)
    T = templat.FORMATS[fmt]
    ep = {"id": eid, "judul": F.get("judul", "").strip() or eid, "judul_en": F.get("judul_en", "").strip() or None,
          "kategori_id": F.get("kategori_id") or None, "format": fmt, "status": "draf",
          "suara_id": _default("suara", ["liam-v3"]), "suara_en_id": _default("suara", ["liam-v3-en"]),
          "musik_id": _default("musik", [T["musik"]]),
          "adegan": [{"jenis": j, "vo": S["vo"], "vo_en": S["vo_en"], "param": S["contoh"], "param_en": S["contoh_en"]}
                     for j in T["kerangka"] for S in [templat.SCENES[j]]], "fakta": []}
    dbt.save_episode(con(), ep)
    con().commit()
    flash(f"Episode dibuat dari kerangka format {T['nama']}. Ganti naskah, angka dan ikonnya, lalu Simpan.", "ok")
    return redirect(url_for("episode_edit", eid=eid))


@app.route("/episode/<eid>")
def episode_edit(eid):
    g.nav = "episode"
    ep = episode_or_404(eid, full=False)
    full = dbt.load_episode(con(), eid)
    errs, warns = dbt.validate(full)
    fakta = q("""SELECT f.*, s.singkat FROM fakta f LEFT JOIN sumber s ON s.id=f.sumber_id
                 ORDER BY (f.kategori_id = ?) DESC, f.kategori_id, f.id""", ep.get("kategori_id") or "")
    tugas = [dict(r, **kemajuan(r)) for r in q("SELECT * FROM tugas WHERE episode_id=? ORDER BY id DESC LIMIT 6", eid)]
    return render_template(
        "episode_edit.html", ep=ep, errs=errs, warns=warns, fakta=fakta, tugas=tugas, hs=hasil(eid), tts=rencana_tts(full),
        kategori=q("SELECT id, nama FROM kategori ORDER BY nama"), suara=q("SELECT id, nama, model FROM suara ORDER BY id"),
        musik=q("SELECT id, judul, artis, bpm FROM musik ORDER BY id"), statuses=STATUS_EP, has_en=has_en(ep),
        data_adegan=kirim_json(ep["adegan"]), data_templat=kirim_json(templat.SCENES),
        data_format=kirim_json({k: list(v) for k, v in FORMAT_SCENES.items()}), syntax=templat.SYNTAX,
        wm=dbt.pengaturan(con()))


@app.route("/episode/<eid>/simpan", methods=["POST"])
def episode_simpan(eid):
    old = episode_or_404(eid, full=False)
    F = request.form
    try:
        if not F.get("adegan"):
            raise ValueError("data adegan tidak terkirim (muat ulang halaman; JavaScript harus aktif)")
        adegan = json.loads(F["adegan"])
        if not isinstance(adegan, list):
            raise ValueError("data adegan rusak")
        for i, sc in enumerate(adegan):
            if sc.get("jenis") not in SCENE_TYPES:
                raise ValueError(f"adegan {i + 1}: jenis tidak dikenal")
            for k in ("param", "param_en"):
                v = sc.get(k)
                if isinstance(v, str):
                    try:
                        v = json.loads(v.strip() or "{}")
                    except json.JSONDecodeError as e:
                        raise ValueError(f"adegan {i + 1}: {k} bukan JSON yang sah ({e.msg}, baris {e.lineno})")
                if not isinstance(v, dict):
                    raise ValueError(f"adegan {i + 1}: {k} harus objek JSON {{ ... }}")
                sc[k] = v
            sc["vo"], sc["vo_en"] = (sc.get("vo") or "").strip(), (sc.get("vo_en") or "").strip()
        tempo = F.get("tempo", "").strip().replace(",", ".")
        tempo = float(tempo) if tempo else None
        if tempo is not None and not 0.7 <= tempo <= 1.5:
            raise ValueError("tempo harus 0,7 – 1,5 (kosongkan untuk bawaan format)")
    except ValueError as e:
        flash(f"Belum disimpan: {e}", "galat")
        return redirect(url_for("episode_edit", eid=eid))
    ep = {"id": eid, "judul": F.get("judul", "").strip() or eid, "judul_en": F.get("judul_en", "").strip() or None,
          "kategori_id": F.get("kategori_id") or None,
          "format": F.get("format") if F.get("format") in templat.FORMATS else old["format"],
          "suara_id": F.get("suara_id") or None, "suara_en_id": F.get("suara_en_id") or None, "musik_id": F.get("musik_id") or None,
          "tempo": tempo, "status": F.get("status") if F.get("status") in STATUS_EP else old.get("status", "draf"),
          "catatan": F.get("catatan", "").strip() or None, "adegan": adegan, "fakta": F.getlist("fakta"),
          "watermark": 1 if F.get("watermark") else 0}
    dbt.save_episode(con(), ep)
    con().commit()
    errs, warns = dbt.validate(dbt.load_episode(con(), eid))
    if errs:
        flash(f"Tersimpan, tapi ada {len(errs)} galat yang harus dibetulkan sebelum render (lihat Validasi).", "galat")
    else:
        flash("Tersimpan. Validasi lolos" + (f" dengan {len(warns)} peringatan." if warns else "."), "ok")
    return redirect(url_for("episode_edit", eid=eid))


@app.route("/episode/<eid>/duplikat", methods=["POST"])
def episode_duplikat(eid):
    ep = episode_or_404(eid, full=False)
    new = request.form.get("id_baru", "").strip().lower() or f"{eid}-salinan"
    if not SLUG.match(new) or q1("SELECT 1 FROM episode WHERE id=?", new):
        flash(f"ID '{new}' tidak sah atau sudah dipakai.", "galat")
        return redirect(url_for("episode_edit", eid=eid))
    ep.update(id=new, status="draf", judul=ep["judul"] + " (salinan)")
    dbt.save_episode(con(), ep)
    con().commit()
    flash(f"Disalin menjadi '{new}'.", "ok")
    return redirect(url_for("episode_edit", eid=new))


@app.route("/episode/<eid>/hapus", methods=["POST"])
def episode_hapus(eid):
    episode_or_404(eid, full=False)
    if q1("SELECT 1 FROM tugas WHERE episode_id=? AND status='jalan'", eid):
        flash("Episode sedang dirender; batalkan tugasnya dulu.", "galat")
        return redirect(url_for("episode_edit", eid=eid))
    con().execute("DELETE FROM episode WHERE id=?", (eid,))
    con().commit()
    flash(f"Episode '{eid}' dihapus dari database (berkas video di episodes/{eid}/ tidak ikut dihapus).", "ok")
    return redirect(url_for("episode_daftar"))


@app.route("/episode/<eid>/render", methods=["POST"])
def episode_render(eid):
    ep = episode_or_404(eid)
    langs = [x for x in request.form.get("bahasa", "id").split(",") if x in LANGS]
    sampai = "mix" if request.form.get("mode") == "pratinjau" else None
    errs, _ = dbt.validate(ep, langs)
    if "en" in langs and not has_en(ep):
        errs.append("naskah English (vo_en) masih kosong")
    if errs:
        flash("Belum bisa dirender: " + " · ".join(errs[:6]) + (" …" if len(errs) > 6 else ""), "galat")
        return redirect(url_for("episode_edit", eid=eid))
    n = 0
    for lang in langs:
        if q1("SELECT 1 FROM tugas WHERE episode_id=? AND bahasa=? AND status IN ('antre','jalan')", eid, lang):
            flash(f"{BAHASA[lang]}: sudah ada di antrean.", "info")
            continue
        con().execute("INSERT INTO tugas (episode_id, bahasa, sampai) VALUES (?,?,?)", (eid, lang, sampai))
        n += 1
    con().commit()
    if n:
        flash(("Pratinjau" if sampai else "Render") + f" masuk antrean ({n} tugas).", "ok")
    return redirect(url_for("antrean"))


# ------------------------------------------------------------------ tabel database (kategori, fakta, sumber, aset, musik, suara)
TABEL = {
    "kategori": {"judul": "Kategori", "daftar": ["id", "nama", "nama_en", "deskripsi"], "kolom": [
        ("id", "ID (slug)", "slug"), ("nama", "Nama", "text"), ("nama_en", "Nama (English)", "text"),
        ("deskripsi", "Deskripsi", "textarea")]},
    "fakta": {"judul": "Fakta", "daftar": ["id", "klaim", "status", "kategori_id", "sumber_id"], "kolom": [
        ("id", "ID (slug)", "slug"), ("kategori_id", "Kategori", "ref:kategori"), ("klaim", "Klaim (Indonesia)", "textarea"),
        ("klaim_en", "Klaim (English)", "textarea"), ("nilai", "Nilai angka", "number"), ("satuan", "Satuan", "text"),
        ("basis", "Basis (mis. per 100 g)", "text"), ("status", "Status", "pilih:fakta,mitos,sebagian,perkiraan"),
        ("sumber_id", "Sumber", "ref:sumber"), ("catatan", "Catatan / cara hitung", "textarea")]},
    "sumber": {"judul": "Sumber", "daftar": ["id", "singkat", "judul", "penerbit"], "kolom": [
        ("id", "ID (slug)", "slug"), ("judul", "Judul dokumen", "text"), ("singkat", "Nama pendek (kredit di video)", "text"),
        ("penerbit", "Penerbit", "text"), ("url", "URL", "url"), ("diakses", "Tanggal dicek", "date"),
        ("catatan", "Catatan", "textarea")]},
    "aset": {"judul": "Aset gambar", "daftar": ["id", "jenis", "berkas", "lisensi"], "kolom": [
        ("id", "ID (dipakai di param: ikon / gambar)", "slug"), ("berkas", "Berkas (SVG untuk ikon, PNG/JPG/WEBP untuk foto)", "file:aset"),
        ("lisensi", "Lisensi", "text"), ("kredit", "Kredit", "text")]},
    "musik": {"judul": "Musik", "daftar": ["id", "judul", "artis", "bpm", "mulai"], "kolom": [
        ("id", "ID (slug)", "slug"), ("berkas", "Berkas lagu (MP3/M4A/WAV)", "file:musik"), ("judul", "Judul", "text"),
        ("artis", "Artis", "text"), ("lisensi", "Lisensi", "text"), ("url", "URL", "url"),
        ("bpm", "BPM (kosongkan = dianalisis otomatis)", "number"), ("mulai", "Detik mulai (ketukan pertama yang sudah ramai)", "number"),
        ("catatan", "Catatan", "textarea")]},
    "suara": {"judul": "Suara", "daftar": ["id", "nama", "model", "voice_id"], "kolom": [
        ("id", "ID (slug)", "slug"), ("penyedia", "Penyedia", "pilih:elevenlabs"), ("model", "Model (mis. eleven_v3)", "text"),
        ("voice_id", "Voice ID ElevenLabs", "text"), ("nama", "Nama", "text"),
        ("pengaturan", 'Pengaturan JSON, mis. {"stability": 0.5, "similarity_boost": 0.75, "language_code": "id"}', "json"),
        ("tempo", "Tempo setelah TTS (format tebakan; 1 = asli)", "number"), ("catatan_lisensi", "Catatan lisensi", "textarea")]},
}
ASET_DIR = os.path.join(ENGINE, "icons")
BGM_DIR = os.path.join(ENGINE, "audio", "bgm")


def _tabel(t):
    if t not in TABEL:
        abort(404)
    return TABEL[t]


@app.route("/data/<t>")
def tabel_daftar(t):
    T = _tabel(t)
    g.nav = t
    qq, kat = request.args.get("q", "").strip(), request.args.get("kategori", "")
    sql, args = f"SELECT * FROM {t} WHERE 1=1", []
    if qq:
        text_cols = [c for c, _l, typ in T["kolom"] if typ in ("text", "textarea", "slug", "url")]
        sql += " AND (" + " OR ".join(f"{c} LIKE ?" for c in text_cols) + ")"
        args += [f"%{qq}%"] * len(text_cols)
    if kat and t == "fakta":
        sql += " AND kategori_id=?"
        args.append(kat)
    rows = q(sql + " ORDER BY rowid DESC", *args)
    pakai = {}
    if t == "fakta":
        pakai = {r["fakta_id"]: r["n"] for r in q("SELECT fakta_id, COUNT(*) n FROM episode_fakta GROUP BY fakta_id")}
    elif t in ("kategori", "musik", "suara"):
        col = {"kategori": "kategori_id", "musik": "musik_id", "suara": "suara_id"}[t]
        pakai = {r["k"]: r["n"] for r in q(f"SELECT {col} k, COUNT(*) n FROM episode GROUP BY {col}")}
    return render_template("tabel_daftar.html", t=t, T=T, rows=rows, qq=qq, kat=kat, pakai=pakai,
                           kategori=q("SELECT id, nama FROM kategori ORDER BY nama") if t == "fakta" else [])


@app.route("/data/<t>/baru")
@app.route("/data/<t>/ubah/<path:rid>")
def tabel_edit(t, rid=None):
    T = _tabel(t)
    g.nav = t
    row = None
    if rid is not None:
        row = q1(f"SELECT * FROM {t} WHERE id=?", rid)
        if not row:
            abort(404)
        row = dict(row)
        if t == "suara" and row.get("pengaturan"):
            row["pengaturan"] = json.dumps(json.loads(row["pengaturan"]), ensure_ascii=False, indent=1)
    refs = {"kategori": q("SELECT id, nama label FROM kategori ORDER BY nama"),
            "sumber": q("SELECT id, COALESCE(singkat, judul) label FROM sumber ORDER BY id")}
    return render_template("tabel_edit.html", t=t, T=T, row=row, refs=refs)


def _simpan_berkas(t, rid, fs):
    """Unggahan aset/musik -> engine/icons atau engine/audio/bgm. Mengembalikan (berkas relatif, jenis aset)."""
    ext = os.path.splitext(fs.filename or "")[1].lower()
    if t == "aset":
        if ext == ".svg":
            data = fs.read()
            if re.search(rb"<script|\son\w+\s*=|javascript:", data, re.I):
                raise ValueError("SVG berisi skrip; simpan ulang sebagai SVG biasa")
            path, rel, jenis = os.path.join(ASET_DIR, rid + ".svg"), rid + ".svg", "svg"
            with open(path, "wb") as f:
                f.write(data)
            return rel, jenis
        if ext in (".png", ".jpg", ".jpeg", ".webp"):
            os.makedirs(os.path.join(ASET_DIR, "foto"), exist_ok=True)
            rel = f"foto/{rid}{ext}"
            fs.save(os.path.join(ASET_DIR, rel))
            return rel, "foto"
        raise ValueError("format gambar harus SVG, PNG, JPG atau WEBP")
    if ext not in (".mp3", ".m4a", ".wav", ".ogg"):
        raise ValueError("format lagu harus MP3, M4A, WAV atau OGG")
    os.makedirs(BGM_DIR, exist_ok=True)
    fs.save(os.path.join(BGM_DIR, rid + ext))
    return rid + ext, None


@app.route("/data/<t>/simpan", methods=["POST"])
def tabel_simpan(t):
    T = _tabel(t)
    F = request.form
    lama = F.get("_lama", "")
    rid = lama or F.get("id", "").strip().lower()
    back = url_for("tabel_edit", t=t, rid=lama) if lama else url_for("tabel_edit", t=t)
    if not SLUG.match(rid):
        flash("ID: huruf kecil, angka dan tanda hubung saja.", "galat")
        return redirect(back)
    if not lama and q1(f"SELECT 1 FROM {t} WHERE id=?", rid):
        flash(f"ID '{rid}' sudah dipakai.", "galat")
        return redirect(back)
    old = dict(q1(f"SELECT * FROM {t} WHERE id=?", rid) or {})
    row = {"id": rid}
    try:
        for c, label, typ in T["kolom"]:
            if c == "id":
                continue
            if typ.startswith("file:"):
                fs = request.files.get(c)
                if fs and fs.filename:
                    row[c], jenis = _simpan_berkas(t, rid, fs)
                    if jenis:
                        row["jenis"] = jenis
                elif old.get(c):
                    row[c] = old[c]
                else:
                    raise ValueError(f"{label}: pilih berkas untuk diunggah")
                continue
            v = F.get(c, "").strip()
            if typ == "number":
                v = float(v.replace(",", ".")) if v else None
            elif typ == "json":
                v = json.dumps(json.loads(v or "{}"), ensure_ascii=False)
            row[c] = v if v != "" else None
        need = {"kategori": ["nama"], "fakta": ["klaim"], "sumber": ["judul"], "suara": ["voice_id", "model"]}.get(t, [])
        miss = [c for c in need if not row.get(c)]
        if miss:
            raise ValueError("wajib diisi: " + ", ".join(miss))
    except json.JSONDecodeError as e:
        flash(f"Belum disimpan: pengaturan bukan JSON yang sah ({e.msg}).", "galat")
        return redirect(back)
    except ValueError as e:
        flash(f"Belum disimpan: {e}", "galat")
        return redirect(back)
    dbt.upsert(con(), t, row)
    con().commit()
    msg = f"{T['judul']} '{rid}' disimpan."
    if t == "musik" and (row.get("bpm") is None or row.get("mulai") is None):
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                dbt.cmd_musik()
            msg += " Analisis ketukan: " + (buf.getvalue().strip() or "selesai")
        except ImportError:
            msg += " (librosa belum terpasang: isi BPM dan detik mulai secara manual, atau pip install librosa)"
        except Exception as e:
            msg += f" (analisis ketukan gagal: {e})"
    flash(msg, "ok")
    return redirect(url_for("tabel_daftar", t=t))


@app.route("/data/<t>/hapus/<path:rid>", methods=["POST"])
def tabel_hapus(t, rid):
    _tabel(t)
    try:
        con().execute(f"DELETE FROM {t} WHERE id=?", (rid,))
        con().commit()
        flash(f"'{rid}' dihapus.", "ok")
    except sqlite3.IntegrityError:
        con().rollback()
        flash(f"'{rid}' masih dipakai episode atau fakta lain; ganti dulu di sana.", "galat")
    return redirect(url_for("tabel_daftar", t=t))


# ------------------------------------------------------------------ ikon & aset
@app.route("/ikon/<name>.svg")
def ikon(name):
    assets = {r["id"]: dict(r) for r in q("SELECT * FROM aset")}
    if assets.get(name, {}).get("jenis") == "foto":
        return send_file(os.path.join(ASET_DIR, assets[name]["berkas"]))
    svg = icon_svg(name, assets)
    if not svg:
        abort(404)
    return Response(svg, mimetype="image/svg+xml", headers={"Cache-Control": "max-age=3600"})


@app.route("/api/ikon")
def api_ikon():
    s = request.args.get("q", "").strip().lower()
    fs = fluent_set()
    names = [r["id"] for r in q("SELECT id FROM aset ORDER BY id")] + sorted(fs["icons"]) + sorted(fs.get("aliases", {}))
    hits = [n for n in names if s in n] if s else names[:0]
    hits.sort(key=lambda n: (not n.startswith(s), len(n)))
    return jsonify(hits[:72])


@app.route("/berkas/<path:p>")
def berkas(p):
    root = os.path.realpath(EPISODES)
    full = os.path.realpath(os.path.join(root, p))
    if not full.startswith(root + os.sep) or not os.path.isfile(full):
        abort(404)
    return send_file(full, conditional=True, as_attachment=request.args.get("unduh") == "1",
                     download_name=os.path.basename(full))


# ------------------------------------------------------------------ watermark (nama channel + maskot di video)
@app.route("/watermark", methods=["GET", "POST"])
def watermark():
    g.nav = "watermark"
    if request.method == "POST":
        F = request.form
        try:
            atas = float(F.get("watermark_atas_cm", "0.75").replace(",", ".") or 0.75)
            op = float(F.get("watermark_opacity", "60").replace(",", ".") or 60)
            if not (0 <= atas <= 12 and 15 <= op <= 100):
                raise ValueError
        except ValueError:
            flash("Belum disimpan: jarak 0–12 cm dan kepekatan 15–100%.", "galat")
            return redirect(url_for("watermark"))
        gambar = F.get("watermark_gambar", "")
        if gambar not in ("", "tanpa") and not q1("SELECT 1 FROM aset WHERE id=?", gambar):
            gambar = ""
        nilai = {"watermark_nama": F.get("watermark_nama", "").strip()[:40], "watermark_gambar": gambar,
                 "watermark_atas_cm": f"{atas:g}", "watermark_opacity": f"{op:g}",
                 "watermark_bawaan": "1" if F.get("watermark_bawaan") else "0"}
        for k, v in nilai.items():
            con().execute("INSERT INTO pengaturan (kunci, nilai) VALUES (?,?) ON CONFLICT(kunci) DO UPDATE SET nilai=excluded.nilai", (k, v))
        con().commit()
        flash("Watermark disimpan. Berlaku untuk render berikutnya (video lama tidak berubah sampai dirender ulang).", "ok")
        return redirect(url_for("watermark"))
    s = dbt.pengaturan(con())
    n = q1("SELECT SUM(watermark=1) ya, SUM(watermark=0) tidak, SUM(watermark IS NULL) ikut FROM episode")
    return render_template("watermark.html", s=s, px_cm=dbt.WM_PX_CM, n=n,
                           aset=q("SELECT id, jenis FROM aset ORDER BY id"))


@app.route("/watermark/maskot.svg")
def watermark_maskot():
    return send_file(os.path.join(ENGINE, "icons", "maskot-si-katuk.svg"), mimetype="image/svg+xml", max_age=3600)


# ------------------------------------------------------------------ kunci API
@app.route("/kunci")
def kunci():
    g.nav = "kunci"
    rows = q("SELECT * FROM kunci_api WHERE penyedia='elevenlabs' ORDER BY urutan, id")
    by = {r["urutan"]: r for r in rows if 1 <= r["urutan"] <= KEY_SLOTS}
    lain = [r for r in rows if r not in by.values()]
    r = q1("SELECT nilai FROM pengaturan WHERE kunci='komersial'")
    return render_template("kunci.html", slots=[(i, by.get(i)) for i in range(1, KEY_SLOTS + 1)], lain=lain,
                           env_key=bool(os.environ.get("XI_API_KEY")), policy=POLICY_URL, komersial=bool(r and r["nilai"] == "1"),
                           n_bayar=sum(1 for x in rows if x["aktif"] and x["paket"] == "berbayar"))


@app.route("/kunci/simpan", methods=["POST"])
def kunci_simpan():
    if _simpan_kunci(request.form):
        flash("Kunci disimpan. Tekan Tes untuk memeriksa apakah kunci valid dan sisa kuotanya.", "ok")
    return redirect(url_for("kunci"))


def _simpan_kunci(F):
    n = 0
    for i in range(1, KEY_SLOTS + 1):
        label, key, aktif = F.get(f"label{i}", "").strip(), F.get(f"kunci{i}", "").strip(), 1 if F.get(f"aktif{i}") else 0
        paket = F.get(f"paket{i}", "") if F.get(f"paket{i}", "") in ("gratis", "berbayar") else None
        row = q1("SELECT id FROM kunci_api WHERE penyedia='elevenlabs' AND urutan=?", i)
        if key and not re.fullmatch(r"[A-Za-z0-9_\-]{16,200}", key):
            flash(f"Kunci {i}: format tidak dikenali (salin ulang dari ElevenLabs → Profile → API Keys).", "galat")
            continue
        if row:
            if key:
                con().execute("UPDATE kunci_api SET label=?, aktif=?, kunci=?, paket=?, status='belum dites', sisa=NULL, catatan=NULL "
                              "WHERE id=?", (label or f"Kunci {i}", aktif, key, paket, row["id"]))
            else:
                con().execute("UPDATE kunci_api SET label=?, aktif=?, paket=? WHERE id=?", (label or f"Kunci {i}", aktif, paket, row["id"]))
            n += 1
        elif key:
            con().execute("INSERT INTO kunci_api (penyedia, label, kunci, urutan, aktif, paket) VALUES ('elevenlabs',?,?,?,?,?)",
                          (label or f"Kunci {i}", key, i, aktif, paket))
            n += 1
    if "_ada_komersial" in F:
        con().execute("INSERT INTO pengaturan (kunci, nilai) VALUES ('komersial', ?) ON CONFLICT(kunci) DO UPDATE SET nilai=excluded.nilai",
                      ("1" if F.get("komersial") else "0",))
        n += 1
    con().commit()
    return n


def _tes(row):
    try:
        st, left = elevenlabs.check(row["id"], row["kunci"])
    except Exception as e:                            # jaringan putus, DNS, dsb.
        elevenlabs.mark(row["id"], "galat", str(e))
        return f"{row['label']}: galat jaringan ({e})", "galat"
    if st == "ok":
        sisa = f"{left:,}".replace(",", ".") if left is not None else None
        return f"{row['label']}: valid" + (f", sisa {sisa} karakter" if sisa else " (kunci tidak diberi izin membaca kuota)"), "ok"
    return f"{row['label']}: {st}", "galat"


@app.route("/kunci/<int:slot>/tes", methods=["POST"])
def kunci_tes(slot):
    _simpan_kunci(request.form)                      # kunci yang baru diketik ikut dites
    rows = q("SELECT * FROM kunci_api WHERE penyedia='elevenlabs' AND aktif=1 ORDER BY urutan, id") if slot == 0 else \
        q("SELECT * FROM kunci_api WHERE penyedia='elevenlabs' AND urutan=?", slot)
    if not rows:
        flash("Belum ada kunci di kotak ini." if slot else "Belum ada kunci aktif.", "info")
    for r in rows:
        flash(*_tes(r))
    return redirect(url_for("kunci"))


@app.route("/kunci/<int:slot>/hapus", methods=["POST"])
def kunci_hapus(slot):
    con().execute("DELETE FROM kunci_api WHERE penyedia='elevenlabs' AND urutan=?", (slot,))
    con().commit()
    flash(f"Kunci {slot} dihapus.", "ok")
    return redirect(url_for("kunci"))


# ------------------------------------------------------------------ antrean render + pekerja
def kemajuan(r):
    r = dict(r)
    seq = STEPS[:STEPS.index(r["sampai"]) + 1] if r.get("sampai") in STEPS else STEPS
    tot = sum(WEIGHT[s] for s in seq)
    if r["status"] == "selesai":
        return {"pct": 100, "seq": seq}
    if r["status"] == "antre" or not r.get("langkah"):
        return {"pct": 0, "seq": seq}
    cur = r["langkah"].split(": ")[-1].split()[0]
    if cur not in seq:
        return {"pct": 0, "seq": seq}
    done = sum(WEIGHT[s] for s in seq[:seq.index(cur)])
    frac = PEKERJA.frac() if r["status"] == "jalan" and cur == "render" and PEKERJA.tid == r["id"] else 0
    return {"pct": min(99, round(100 * (done + WEIGHT[cur] * frac) / tot)), "seq": seq}


@app.route("/antrean")
def antrean():
    g.nav = "antrean"
    rows = [dict(r, **kemajuan(r)) for r in q("SELECT t.*, e.judul FROM tugas t LEFT JOIN episode e ON e.id=t.episode_id "
                                               "ORDER BY t.id DESC LIMIT 100")]
    return render_template("antrean.html", rows=rows, refresh=any(r["status"] in ("antre", "jalan") for r in rows))


@app.route("/api/antrean")
def api_antrean():
    rows = q("SELECT t.*, e.judul FROM tugas t LEFT JOIN episode e ON e.id=t.episode_id ORDER BY t.id DESC LIMIT 20")
    return jsonify([{k: r[k] for k in ("id", "episode_id", "bahasa", "status", "langkah")} | {"pct": kemajuan(r)["pct"]} for r in rows])


@app.route("/antrean/<int:tid>/log")
def antrean_log(tid):
    g.nav = "antrean"
    r = q1("SELECT t.*, e.judul FROM tugas t LEFT JOIN episode e ON e.id=t.episode_id WHERE t.id=?", tid)
    if not r:
        abort(404)
    text = ""
    if r["log"] and os.path.exists(os.path.join(PROJ, r["log"])):
        with open(os.path.join(PROJ, r["log"]), encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        # baris progres render ([k] frame a/b) cukup yang terakhir per shard
        last, keep = {}, []
        for ln in lines:
            m = re.match(r"\[(\d+)\] frame", ln)
            if m:
                last[m.group(1)] = ln
                continue
            keep.append(ln)
        text = "".join(keep[-400:] + sorted(last.values()))
    return render_template("log.html", r=dict(r, **kemajuan(r)), text=text, refresh=r["status"] in ("antre", "jalan"))


@app.route("/antrean/<int:tid>/batal", methods=["POST"])
def antrean_batal(tid):
    r = q1("SELECT * FROM tugas WHERE id=?", tid)
    if r and r["status"] == "antre":
        con().execute("UPDATE tugas SET status='batal', selesai=datetime('now','localtime') WHERE id=?", (tid,))
        con().commit()
    elif r and r["status"] == "jalan":
        PEKERJA.cancel(tid)
    flash(f"Tugas #{tid} dibatalkan.", "ok")
    return redirect(request.referrer or url_for("antrean"))


@app.route("/antrean/<int:tid>/ulangi", methods=["POST"])
def antrean_ulangi(tid):
    r = q1("SELECT * FROM tugas WHERE id=?", tid)
    if r:
        con().execute("INSERT INTO tugas (episode_id, bahasa, sampai) VALUES (?,?,?)", (r["episode_id"], r["bahasa"], r["sampai"]))
        con().commit()
        flash("Tugas dimasukkan lagi ke antrean.", "ok")
    return redirect(url_for("antrean"))


class Pekerja(threading.Thread):
    """Menjalankan tugas antrean satu per satu: python3 tools/make_video.py ID --bahasa LANG [--sampai mix]."""

    def __init__(self):
        super().__init__(daemon=True, name="pekerja-render")
        self.lock, self.proc, self.tid, self.batal, self.shards = threading.Lock(), None, None, set(), {}

    def frac(self):
        s = list(self.shards.values())
        return sum(a for a, _ in s) / max(1, sum(b for _, b in s)) if s else 0.0

    def run(self):
        c = dbt.connect()
        c.execute("UPDATE tugas SET status='gagal', langkah=COALESCE(langkah,'') || ' (panel dimulai ulang)', "
                  "selesai=datetime('now','localtime') WHERE status='jalan'")
        c.commit()
        c.close()
        while True:
            try:
                if not self.step():
                    time.sleep(1.5)
            except Exception as e:                   # pekerja tidak boleh mati karena satu tugas
                print("pekerja:", repr(e), file=sys.stderr)
                time.sleep(3)

    def _set(self, tid, **kv):
        c = dbt.connect()
        c.execute(f"UPDATE tugas SET {', '.join(k + '=?' for k in kv)} WHERE id=?", (*kv.values(), tid))
        c.commit()
        c.close()

    def step(self):
        c = dbt.connect()
        r = c.execute("SELECT * FROM tugas WHERE status='antre' ORDER BY id LIMIT 1").fetchone()
        c.close()
        if not r:
            return False
        tid = r["id"]
        os.makedirs(LOGDIR, exist_ok=True)
        log = os.path.join(LOGDIR, f"tugas-{tid}.log")
        self._set(tid, status="jalan", langkah="mulai", log=os.path.relpath(log, PROJ), mulai=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        try:
            rc = self._run(tid, r, log)
        except Exception as e:
            with open(log, "a", encoding="utf-8") as f:
                f.write(f"\npanel: {e!r}\n")
            rc = -1
        with self.lock:
            cancelled = tid in self.batal
            self.proc, self.tid = None, None
        status = "batal" if cancelled else "selesai" if rc == 0 else "gagal"
        self._set(tid, status=status, selesai=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  **({"langkah": "selesai"} if status == "selesai" else {}))
        return True

    def _run(self, tid, r, log):
        cmd = [sys.executable, "-u", MAKE, r["episode_id"], "--bahasa", r["bahasa"]] + (["--sampai", r["sampai"]] if r["sampai"] else [])
        with open(log, "w", encoding="utf-8") as f:
            f.write("$ " + " ".join(os.path.relpath(x, PROJ) if x.startswith(PROJ) else x for x in cmd[1:]) + "\n")
            p = subprocess.Popen(cmd, cwd=PROJ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                 start_new_session=True, env={**os.environ, "PYTHONUNBUFFERED": "1"})
            with self.lock:
                self.proc, self.tid, self.shards = p, tid, {}
            for line in p.stdout:
                f.write(line)
                f.flush()
                m = re.match(r"== \S+(?: \[(\w+)\])?: (\w+)", line)
                if m and m.group(2) in STEPS:
                    self._set(tid, langkah=(m.group(1) + ": " if m.group(1) else "") + m.group(2))
                    self.shards = {}
                m = re.match(r"\[(\d+)\] frame (\d+)/(\d+)", line)
                if m:
                    self.shards[m.group(1)] = (int(m.group(2)), int(m.group(3)))
            return p.wait()

    def cancel(self, tid):
        with self.lock:
            if self.tid == tid and self.proc:
                self.batal.add(tid)
                try:
                    os.killpg(self.proc.pid, signal.SIGTERM)    # make_video + node/ffmpeg anaknya
                except ProcessLookupError:
                    pass
                return True
        return False


PEKERJA = Pekerja()


def siapkan_db():
    if not os.path.exists(DBFILE):
        print("database belum ada: membuat db/konten.db dari db/data/*.json")
        dbt.init_schema()
        dbt.cmd_import()
    else:
        dbt.init_schema()                         # tabel baru (kunci_api, tugas) pada berkas lama
        dbt.connect().close()                     # kolom baru (migrasi kecil)


def main():
    ap = argparse.ArgumentParser(description="Panel web mesin video")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5000)
    ap.add_argument("--tanpa-pekerja", action="store_true", help="jangan jalankan render di proses ini")
    a = ap.parse_args()
    if os.environ.get("PANEL_PUBLIK") and not os.environ.get("PANEL_PASSWORD"):
        sys.exit("PANEL_PUBLIK=1 tetapi PANEL_PASSWORD kosong: panel tidak dijalankan.")
    if a.host not in ("127.0.0.1", "localhost") and not os.environ.get("PANEL_PASSWORD"):
        sys.exit("Panel berisi kunci API: set PANEL_PASSWORD bila dibuka di luar komputer ini (--host 0.0.0.0).")
    siapkan_db()
    if not a.tanpa_pekerja:
        PEKERJA.start()
    print(f"Panel: http://{a.host}:{a.port}")
    app.run(host=a.host, port=a.port, threaded=True, use_reloader=False)


if __name__ == "__main__":
    main()
