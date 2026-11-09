"""Voice-over script, one line per scene (numbers spelled out for the TTS).

Facts: Data Komposisi Pangan Indonesia (Kemenkes RI, panganku.org), per 100 g:
daun katuk segar vit C 164 mg, kalsium 233 mg, karotenoid total 10.020 mcg, besi 3,0 mg;
jeruk manis vit C 49 mg; susu sapi segar kalsium 143 mg; wortel segar karotenoid 11.046 mcg;
bayam segar besi 3,0 mg; daun katuk rebus vit C 66 mg.
"""
# "|" marks a subtitle page break (removed before TTS).
LINES = [
    ("s1", "Daun ini, | vitamin C-nya | tiga kali lipat jeruk!"),
    ("s2", "Ini daun katuk. | Murah, gampang ditanam, | gizinya luar biasa. | Apa saja manfaatnya?"),
    ("s3", "Pertama, pelancar ASI. | Turun-temurun dipakai | ibu menyusui, | dan beberapa penelitian | hasilnya menjanjikan."),
    ("s4", "Kedua, daya tahan tubuh. | Vitamin C-nya seratus enam puluh empat miligram, | jeruk manis cuma empat puluh sembilan."),
    ("s5", "Ketiga, tulang dan gigi. | Kalsiumnya dua ratus tiga puluh tiga miligram, | lebih tinggi dari | susu sapi segar."),
    ("s6", "Keempat, kesehatan mata. | Kandungan karotenoidnya | hampir menyamai wortel."),
    ("s7", "Kelima, zat besinya | setara bayam, | penting untuk membentuk | sel darah merah."),
    ("s8", "Tapi ingat, | masak dulu, | jangan terlalu lama | supaya vitaminnya | tidak banyak hilang. | Hindari jus daun katuk | mentah berlebihan."),
    ("s9", "Murah, mudah ditanam, | kaya manfaat. | Simpan video ini, | dan bagikan ke orang tersayang!"),
]
speech = lambda text: " ".join(text.replace("|", " ").split())
