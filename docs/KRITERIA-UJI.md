# Kriteria uji NewPaceLab (dari Claude project, 10 Nov 2026)

Angka di bawah dihitung dari data asli (FIT Garmin, export MD NewPaceLab, dan folder `C:\NewPaceLab\data`). Setiap poin memakai nomor dari `docs/RENCANA.md` poin 19.

---

## Poin 1: penilaian lomba (dan tempo yang ambruk)

**Uji 1a: Taofik, lomba 10K, 7 Nov (sesi mulai 06:18)**

| Km | Pace | Jalan kaki |
|---|---|---|
| 1–4 | 6:08 / 6:06 / 6:06 / 6:09 | – |
| 5 | 6:52 | 0:28 |
| 6 | 6:55 | – |
| 7 | 7:06 | 0:08 |
| 8 | 7:40 | 0:56 |
| 9 | 8:09 | 1:05 |
| 10 | 7:33 | 0:30 |

Hasil yang diharapkan:
- Paruh 1 (km 1–5) = **31:21**, paruh 2 (km 6–10) = **37:23** → **positive split +6:02 (+19%)** → ditandai "pace ambruk" (§5b: >5%).
- Jalan kaki total **3:07** di km 5, 7, 8, 9, 10 → ditandai (§5b: ≥10 detik).
- HR km 4 = 174 = LTHR − 2 → **masih boleh**, tidak ditandai (§5b: hanya HR di atas batas yang ditandai).
- **Tidak boleh** tertulis "sesi bersih".

**Uji 1b: Reza, lomba 10K, 7 Nov**
- Jarak 5,00 / 10 km = 50% → "tidak selesai" (§5b: <90%).
- km 1 = **6:17**, rencana mode tempo 7:25 → **68 detik lebih cepat** → "start terlalu cepat" (§5b: >10 detik).
- HR maks 176 > LTHR 173.

**Uji 1c: tempo yang melambat, 27 Okt**
- Reza (lap 1 km per detik): 6:50 → **6:28** → 6:53. km terakhir 25 detik lebih lambat dari km tercepat → ditandai "melambat di akhir" (§5b: >15 detik).
- Taofik: 6:12 → 5:54 → 5:51 → **tidak** ditandai.

## Poin 2: `overrides.json`

- Isi: `{"date":"2026-11-01","athlete":"TAOFIK","session":"long_run","km":22}` (sama untuk REZA dengan km 21).
- Diharapkan: Taofik 21,02 / 22 = **95,5% ✓**, Reza 21,02 / 21 = **100% ✓**, dinilai dengan aturan long run (aturan B), bukan "pemulihan 6 km / 350%".
- Catatan: tebakan otomatis kemungkinan gagal karena Sabtu 31 Okt ada lari 8,5 km.
- File ini harus terbaca juga oleh export MD, supaya Claude project melihat rencana yang sama.

## Poin 3: gerbang pagi

**Uji 3a: hari yang dipakai.** Pada Senin 2 Nov, kartu tidak boleh menulis "Long run Sabtu: Potong 20%" dari data Senin. Tulis "dinilai Sabtu pagi", atau hitung dari data pagi di hari long run.

**Uji 3b: lampu merah (aturan §7b, sudah diputuskan 10 Nov).**
- Reza 1 Nov: tidur 6,8 j, Body Battery 65 (§7 lolos), tapi status HRV LOW.

**Aturan lampu:** ikuti tabel di RUMUS §7b (Hijau / Kuning / Oranye / Merah, termasuk RHR +5/+7 dan status HRV UNBALANCED vs LOW/POOR). Tabel tidak disalin ke sini supaya tidak ada dua versi.

- Reza 1 Nov: status HRV LOW sudah ≥3 hari (2 Nov tertulis "rendah 4 hari") → **Merah** → "lari santai ≤8 km atau istirahat".

## Poin 4: gerbang dilewati

- Taofik 1 Nov: tidur 5,6 j → §7 baris 2 → batas long run 22 × 0,8 = **17,6 km**. Aktual **21,02 km**.
- Tampil **dua baris** (§5b): "Jarak 21,02 / 22 = 95,5% ✓" **dan** "Gerbang dilewati (+3,4 km)". Uji 2 dan Uji 4 sama-sama benar.
- Reza 1 Nov: lampu merah (§7b) → ditandai "gerbang dilewati (21 km saat lampu merah)".

## Poin 5: strides dalam jarak rencana

**Aturan (RUMUS §5, FINAL):** kalau sel menyebut strides, tambahkan **0,15 km per stride** (termasuk jalan kakinya). Pendinginan yang tidak tertulis: +0.

- Uji: Taofik 10 Nov, "6 km + 6 strides" → rencana 6,9 km. Aktual 6,89 km = **100% ✓**, tanpa alarm 110%.

## Poin 6: kecepatan jam dan suhu

- Simpan `enhanced_speed` (atau `directSpeed`) dan suhu per detik saat sync.
- **Uji strides**, Taofik 10 Nov (id 25025503260). Aturan: kecepatan jam >2,6 m/s minimal 6 detik, setelah km 6.
  - Hasil yang diharapkan: **6 strides**, durasi **16–23 detik**, pace puncak **4:40–5:49**.
  - Rinciannya: 19 dtk/5:49 · 16/5:21 · 20/4:40 · 17/5:15 · 21/4:47 · 23/4:43.
  - Dengan kecepatan dari selisih jarak, puncaknya terbaca terlalu cepat (sekitar 4:25).
- **Validasi data** (sudah dicek dari FIT asli): jarak per detik selisih 0,02 m, HR/cadence/elevasi selisih 0. JSON tidak punya 156 detik saat berhenti (km 3,7) karena jam di-pause.

## Poin 7: detik saat jam di-pause

Tidak perlu disimpan dan tidak dinilai (§5b). Cukup tampil "berhenti x:xx" = waktu total − waktu bergerak.
- Uji: Taofik 10 Nov → **"berhenti 5:07"** (59:47 − 54:40).

## Poin 8: decoupling

| Sesi | Claude project (FIT, `enhanced_speed`) | Dashboard sekarang | Toleransi |
|---|---|---|---|
| Taofik 1 Nov | 4,9% (tanpa 3 km) · 8,4% (penuh) | 4,9 · 8,4 | ✓ sudah sama |
| Reza 1 Nov | **2,8%** · **4,3%** | 3,6 · 5,3 | harus ±0,3 setelah poin 6 |

## Poin 9: decoupling "tidak berlaku"

Harus tertulis "tidak berlaku" (bukan angka) di kartu linimasa dan tabel detail untuk:
- Taofik 27 Okt (tempo). Dulu terbaca 22,9%.
- Taofik 7 Nov (lomba). Sekarang 12,7%.
- Semua sesi interval, tempo, lomba, dan lari santai dengan strides.

## Poin 10: kalkulator target lomba

Rumus ada di `RUMUS-BATAS-SUMBER.md` §3b (pakai versi 10 Nov 2026).

Uji, Taofik 10K 7 Nov:
- Dasar: 5K 31:29 → Riegel 31:29 × 2^1,06 = **65:38**.
- Koreksi panas (start 06:18, 29–34°C → 30–32°C) **+5%** → 68:55.
- Kelelahan (long run 21 km 6 hari sebelumnya) **+2%** → **70:18**.
- Output: rentang **69–71 menit**, plus batas HR per km: km 1 ≤161, km 2 ≤170, km 3–5 ≤174.
- Cek silang: hasil aktual 68:49 jatuh di sekitar rentang ini.

## Poin 11: aturan 110% sebelum sesi

- Long run Sabtu 14 Nov. Jendela 30 hari: 15 Okt–13 Nov.
- Taofik: terpanjang **21,02 km** (1 Nov) → batas **23,1 km**. Rencana 16 km ✓
- Reza: terpanjang **21,02 km** (1 Nov) → batas **23,1 km** ✓

## Poin 12: HRV

Perlu unduh ulang sekali dari Garmin. Data HRV Garmin kemungkinan sudah memuat rata-rata 7 hari dan batas atas/bawah normal pribadi.

Kartu 2 Nov harus menampilkan tiga angka:
- Taofik: semalam **37**, rata-rata 7 hari, rentang pribadi → status **Balanced**.
- Reza: semalam **43**, rata-rata 7 hari, rentang pribadi → status **Low**.

Tambahkan satu baris penjelasan: "status = rata-rata 7 hari dibanding rentang pribadi, bukan angka semalam".

## Poin 14: cek pacing berdua

**Aturan (§5b, berlaku untuk pelari mana pun):** tandai "kemungkinan terbawa" kalau ketiganya terpenuhi:
1. Jam mulai keduanya berbeda kurang dari 2 menit.
2. Selisih pace km 1 kurang dari 15 detik.
3. km 1 salah satu pelari lebih cepat lebih dari 30 detik dari rencananya sendiri.

Uji:
- 7 Nov: start keduanya 06:18; km 1 Taofik 6:08, Reza 6:17 (selisih 9 detik); Reza 68 detik lebih cepat dari rencana → **ditandai**.
- 27 Okt: start 05:50 vs 05:44 (selisih 6 menit) → **tidak** ditandai.
