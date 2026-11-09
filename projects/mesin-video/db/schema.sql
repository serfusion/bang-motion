-- Skema database konten video edukasi pendek (SQLite).
-- Satu baris `episode` + baris-baris `adegan`-nya = satu video. Semua teks yang tampil di video berasal dari sini;
-- angka & klaim ditautkan ke `fakta` -> `sumber` supaya bisa diaudit. Tidak ada langkah yang butuh model AI
-- (suara memakai layanan TTS).
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS kategori (
  id        TEXT PRIMARY KEY,            -- mis. 'mitos-fakta', 'gizi', 'sains'
  nama      TEXT NOT NULL,
  nama_en   TEXT,
  deskripsi TEXT
);

CREATE TABLE IF NOT EXISTS sumber (
  id       TEXT PRIMARY KEY,
  judul    TEXT NOT NULL,                -- judul dokumen / tabel / artikel
  penerbit TEXT,
  url      TEXT,
  diakses  TEXT,                         -- tanggal cek (YYYY-MM-DD)
  catatan  TEXT
);

CREATE TABLE IF NOT EXISTS fakta (
  id          TEXT PRIMARY KEY,
  kategori_id TEXT REFERENCES kategori(id),
  klaim       TEXT NOT NULL,             -- kalimat fakta (bahasa Indonesia)
  klaim_en    TEXT,
  nilai       REAL,                      -- angka utama bila ada
  satuan      TEXT,                      -- 'g', 'kkal', '°C', ...
  basis       TEXT,                      -- 'per 100 g', 'per 500 ml', ...
  status      TEXT CHECK (status IN ('fakta','mitos','sebagian','perkiraan')),
  sumber_id   TEXT REFERENCES sumber(id),
  catatan     TEXT                       -- cara hitung / batasan klaim
);

CREATE TABLE IF NOT EXISTS aset (
  id      TEXT PRIMARY KEY,              -- nama yang dipakai di param adegan, mis. 'tempe'
  jenis   TEXT CHECK (jenis IN ('ikon','svg','foto')),
  berkas  TEXT NOT NULL,                 -- 'fluent:onion' (Fluent Emoji Flat) atau path SVG/foto di engine/icons
  lisensi TEXT,
  kredit  TEXT
);

CREATE TABLE IF NOT EXISTS suara (
  id              TEXT PRIMARY KEY,
  penyedia        TEXT,                  -- 'elevenlabs'
  model           TEXT,                  -- 'eleven_v3'
  voice_id        TEXT,
  nama            TEXT,
  pengaturan      TEXT,                  -- JSON: stability, similarity_boost, language_code
  tempo           REAL DEFAULT 1.12,     -- percepatan setelah TTS (rubberband)
  catatan_lisensi TEXT
);

CREATE TABLE IF NOT EXISTS musik (
  id      TEXT PRIMARY KEY,
  berkas  TEXT NOT NULL,                 -- path relatif di engine/audio/bgm
  judul   TEXT, artis TEXT, lisensi TEXT, url TEXT,
  bpm     REAL,                          -- diisi tools/db.py musik (analisis ketukan)
  mulai   REAL,                          -- detik lagu yang jatuh di detik 0 video (ketukan pertama yang sudah ramai)
  catatan TEXT
);

CREATE TABLE IF NOT EXISTS episode (
  id          TEXT PRIMARY KEY,          -- slug, juga nama folder keluaran
  kategori_id TEXT REFERENCES kategori(id),
  judul       TEXT NOT NULL,
  judul_en    TEXT,
  suara_id    TEXT REFERENCES suara(id),
  musik_id    TEXT REFERENCES musik(id),
  status      TEXT DEFAULT 'draf' CHECK (status IN ('draf','siap','dirender','terbit')),
  catatan     TEXT,
  dibuat      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Jenis adegan (templat di engine/scenes.js): kuis, jawaban, langkah, banding, twist, cta.
-- vo   : naskah suara. '[tag]' = arahan intonasi ElevenLabs v3, '|' = batas halaman subtitle,
--        '{nama}' sebelum sebuah kata = isyarat waktu untuk visual (mis. {p0} pilihan A disebut, {jawab} jawaban).
-- vo_en: subtitle Inggris, jumlah '|' sama dengan vo.
-- param: JSON khusus per jenis adegan (lihat README).
CREATE TABLE IF NOT EXISTS adegan (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  urutan     INTEGER NOT NULL,
  jenis      TEXT NOT NULL CHECK (jenis IN ('kuis','jawaban','langkah','banding','twist','cta')),
  vo         TEXT NOT NULL,
  vo_en      TEXT NOT NULL,
  param      TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (episode_id, urutan)
);

CREATE TABLE IF NOT EXISTS episode_fakta (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  fakta_id   TEXT REFERENCES fakta(id),
  PRIMARY KEY (episode_id, fakta_id)
);

CREATE TABLE IF NOT EXISTS render (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  bahasa     TEXT,                       -- 'id', 'en', 'id-tanpa-musik'
  berkas     TEXT,
  durasi     REAL,
  dibuat     TEXT DEFAULT CURRENT_TIMESTAMP
);
