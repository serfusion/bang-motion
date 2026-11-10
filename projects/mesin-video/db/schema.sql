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
  singkat  TEXT,                         -- nama pendek untuk kredit di layar
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
  format      TEXT NOT NULL DEFAULT 'tebakan' CHECK (format IN ('tebakan','fakta')),
                                         -- tebakan: kuis cepat (hook, hitung mundur, jawaban)
                                         -- fakta: penjelasan santai bergaya catatan (kartu angka, analogi, pertanyaan penutup)
  judul       TEXT NOT NULL,
  judul_en    TEXT,
  suara_id    TEXT REFERENCES suara(id), -- suara untuk naskah Indonesia
  suara_en_id TEXT REFERENCES suara(id), -- suara untuk naskah Inggris
  musik_id    TEXT REFERENCES musik(id),
  tempo       REAL,                      -- kosong = bawaan format (tebakan 1.12, fakta 1.0)
  status      TEXT DEFAULT 'draf' CHECK (status IN ('draf','siap','dirender','terbit')),
  catatan     TEXT,
  dibuat      TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Jenis adegan (templat di engine/js/scenes.js dan fakta.js):
--   format tebakan: kuis, jawaban, langkah, banding, twist, cta
--   format fakta  : pembuka, catatan, ibarat, tanya (+ langkah, banding)
-- vo      : naskah suara Indonesia. '[tag]' = arahan intonasi ElevenLabs v3, '|' = batas halaman subtitle,
--           '{nama}' sebelum sebuah kata = isyarat waktu untuk visual (mis. {p0} pilihan A disebut, {k0} kartu pertama).
-- vo_en   : naskah suara Inggris (format sama, isyaratnya sama) — dipakai untuk video berbahasa Inggris.
-- param   : JSON khusus per jenis adegan (lihat README).
-- param_en: JSON yang menimpa teks layar di param untuk video berbahasa Inggris (hanya kunci yang berbeda).
CREATE TABLE IF NOT EXISTS adegan (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  urutan     INTEGER NOT NULL,
  jenis      TEXT NOT NULL CHECK (jenis IN ('kuis','jawaban','langkah','banding','twist','cta','pembuka','catatan','ibarat','tanya')),
  vo         TEXT NOT NULL,
  vo_en      TEXT NOT NULL DEFAULT '',
  param      TEXT NOT NULL DEFAULT '{}',
  param_en   TEXT NOT NULL DEFAULT '{}',
  PRIMARY KEY (episode_id, urutan)
);

CREATE TABLE IF NOT EXISTS episode_fakta (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  fakta_id   TEXT REFERENCES fakta(id),
  PRIMARY KEY (episode_id, fakta_id)
);

CREATE TABLE IF NOT EXISTS render (
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  bahasa     TEXT,                       -- 'id', 'id-tanpa-musik', 'en', 'en-tanpa-musik'
  berkas     TEXT,
  durasi     REAL,
  dibuat     TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Kunci API TTS. Dicoba berurutan; bila satu ditolak (kuota habis / tidak valid / batas laju), pindah ke berikutnya.
-- Berkas db/konten.db tidak pernah di-commit, dan kunci tidak ikut diekspor ke JSON.
CREATE TABLE IF NOT EXISTS kunci_api (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  penyedia    TEXT NOT NULL DEFAULT 'elevenlabs',
  label       TEXT,
  kunci       TEXT NOT NULL,
  urutan      INTEGER NOT NULL DEFAULT 1,
  aktif       INTEGER NOT NULL DEFAULT 1,
  status      TEXT DEFAULT 'belum dites',  -- ok / habis / ditolak / galat
  sisa        INTEGER,                     -- sisa karakter bila API mengizinkan cek langganan
  terakhir    TEXT,                        -- waktu terakhir dipakai
  catatan     TEXT
);

-- Antrean render dari panel web.
CREATE TABLE IF NOT EXISTS tugas (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  episode_id TEXT REFERENCES episode(id) ON DELETE CASCADE,
  bahasa     TEXT NOT NULL,                -- 'id' atau 'en'
  status     TEXT NOT NULL DEFAULT 'antre' CHECK (status IN ('antre','jalan','selesai','gagal','batal')),
  langkah    TEXT,                         -- langkah pipeline yang sedang berjalan
  log        TEXT,                         -- path log
  dibuat     TEXT DEFAULT CURRENT_TIMESTAMP,
  mulai      TEXT,
  selesai    TEXT
);
