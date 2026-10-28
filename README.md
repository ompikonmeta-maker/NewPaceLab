# NewPaceLab

Dashboard marathon Taofik & Reza: satu file HTML offline dari data Garmin Personal API dan program latihan Excel.

## Pakai

Paling mudah: klik dua kali **`Update Dashboard.bat`**. Data ditarik, dashboard dibuat, lalu terbuka di browser.

**Versi portable** (Python sudah di dalamnya, tidak perlu install): unduh
`NewPaceLab-portable-win-amd64.zip` (Intel/AMD) atau `-win-arm64.zip` (Windows ARM) dari
halaman *Releases → portable*. Dibuat otomatis oleh GitHub Actions (`tools/make_portable.py`).

Lewat PowerShell:

```
python pacelab.py            # tarik data Garmin kedua atlet, lalu buat dist/dashboard.html
python pacelab.py build      # buat ulang dashboard dari data yang sudah ada
python pacelab.py check      # cek field Garmin yang terbaca (hanya jumlah & nama field)
python pacelab.py demo       # dashboard dari data rekaan, tanpa key/internet
python pacelab.py inspect    # struktur respons Garmin (nama field & tipe, tanpa nilai)
```

Opsi: `--who TAOFIK|REZA|ALL`, `--since 2026-03-23`.

Python 3.8+ saja, tanpa `pip install`.

## Siapkan sekali

1. **Key Garmin** (Garmin Connect → Account Settings → Personal API) disimpan sebagai file teks:
   `keys/TAOFIK.key`, `keys/REZA.key`. Bisa juga lewat env `GARMIN_KEY_TAOFIK`, `GARMIN_KEY_REZA`.
2. **Program latihan** ditaruh di `programs/`:
   `Program_Marathon_TAOFIK.xlsx`, `Program_Marathon_PRAMANA.xlsx` (nama file bisa diubah di `config.json`).

`keys/`, `programs/*.xlsx`, `data/`, `.token_cache/` dan `dist/` tidak pernah di-commit.

## Isi dashboard

Urutan dari atas: hitung mundur dan **lintasan program** (22 Jun → hari maraton, satu garis per minggu,
tanda lomba, kedua pelari berdiri di tanggal hari ini). Di bawahnya **batang target km mingguan** kedua pelari
dan **kurung fase** bertanggal (km & long run per fase, titik progres fase berjalan). Arahkan kursor ke batang
untuk ringkasan; klik batang untuk **jadwal harian** minggu itu (Senin–Minggu dari sheet Kalender, ✓ km aktual,
catatan coaching; ←/→ pindah minggu, Esc tutup). Saat halaman di-scroll, kedua pelari lepas dari lintasan dan
parkir di tepi kiri (Taofik) dan kanan (Reza); scroll ke atas mengembalikannya. Lalu **Ringkasan** head-to-head, **Latihan**,
**Pemulihan**, **Progres terbaik**, **Badge**. Tombol di kanan atas menyalakan/mematikan tiap pelari.

| Bagian | Sumber |
|---|---|
| Hitung mundur, minggu program, fase, tanda lomba | Excel: Kalender, Checkpoint |
| Ringkasan head-to-head | lampu hari ini, est. maraton, km & long run minggu ini, HRV, Body Battery, tidur, RHR, aturan Sabtu |
| Est. maraton | Riegel (eksponen 1.06): prediksi tercepat dari usaha terbaik 5K, 10K dan Half dalam 120 hari terakhir; ditampilkan juga + koreksi panas 5% |
| Menuju 42K | long run terpanjang sejak awal program |
| Skor minggu lalu | % target km, % target long run, rata tidur vs target minimum masing-masing, jumlah hari hijau |
| Latihan (filter 4 / 12 minggu / semua) | km, long run, decoupling, berat vs target per minggu yang sudah selesai; sumbu = tanggal awal minggu |
| Pemulihan (filter 7 / 14 / 30 / 60 hari) | lampu harian, tidur, HRV, Body Battery |
| 5K / 10K / Half | segmen tercepat di dalam lari mana pun (data per detik), hanya saat rekor membaik |
| Full | estimasi per akhir bulan, di atas pita target B |
| Badge | 21/25/30/35K, 100 km/bulan, streak 7 & 14 minggu ≥90% target km, PR 5K/10K selama program |

### Kesimpulan di tiap grafik

Rumus, batas angka, dan sumbernya ada di **[docs/RUMUS-BATAS-SUMBER.md](docs/RUMUS-BATAS-SUMBER.md)** (acuan tunggal).
Batas bertanda **[keputusan dashboard]** tidak diatur dokumen itu.

| Metrik | Baik | Perlu perhatian | Buruk | Dasar |
|---|---|---|---|---|
| km / long run vs target | ≥ 90% | 75–90% | < 75% | [keputusan dashboard] |
| Decoupling (tanpa 3 km pertama, long run ≥ 20 km, bukan minggu lomba) | < 5% bagus, 5–8% sesuai target | ≥ 8% | – | dokumen §6 |
| Berat | turun ≤ 0,5 kg/minggu, rata 4 minggu di atas batas bawah | turun > 0,5 kg/minggu | rata 4 minggu < batas bawah (65 / 73 kg, `config.json`) | dokumen §9 |
| Tidur (rata-rata periode) | ≥ target minimum | sampai 30 mnt kurang | lebih dari 30 mnt kurang | target dari Excel; 30 mnt [keputusan dashboard] |
| HRV | status terakhir Balanced, ≤ 1 hari rendah | lainnya | ≥ 3 hari rendah | status Garmin; 3 hari [keputusan dashboard] |
| Body Battery (rata-rata) | ≥ 50 | 40–49 | < 40 | dokumen §7 (gerbang pagi) |
| Est. maraton | masuk target A atau B | masuk target C | di luar target C | zona target A/B/C di Excel; dinilai dari estimasi tanpa koreksi panas |

Status selalu ditampilkan sebagai warna + ikon + kata. Animasi mati otomatis bila perangkat diatur "kurangi gerakan".

### Tafsiran aturan Excel

Tabel di Excel ditulis untuk manusia; ini cara program membacanya.

- **HRV normal** = status Garmin `BALANCED`. **Di bawah normal** = `LOW` atau `POOR`. Status `NONE` = tidak ada data malam itu (lampu dinilai dari BB dan tidur saja).
- **Detak istirahat naik** = dibanding median 28 hari sebelumnya (minimal 7 hari data). RHR diambil dari ringkasan harian; kalau kosong, dari data tidur.
- **Lampu**: MERAH (HRV di bawah normal 3 hari, atau RHR +7) → ORANYE (HRV di bawah normal 2 hari, BB < 40, atau RHR +5) → HIJAU (HRV balanced, BB ≥ 50, tidur ≥ 6 jam; BB ≥ 50 dari gerbang pagi dokumen §7) → selain itu KUNING.
- **Kenapa lampu tidak hijau**: di bawah kalimat ringkasan tertulis syarat yang kurang; klik lampunya untuk rincian
  empat syarat (HRV, Body Battery, tidur, detak istirahat) beserta nilai hari itu dan batasnya.
- **Body Battery harian** = nilai tertinggi hari itu (setelah tidur).
- **Aturan Sabtu**: tidur < 5 jam + BB < 30 + HRV di bawah normal → *Ganti easy 8 km*; tidur < 5 jam + BB < 40 → *Potong 40%*; tidur ≥ 6 jam + BB ≥ 50 → *Jalankan*; selain itu → *Potong 20%*.
- **Decoupling** (dokumen §6) = record dengan HR > 80 dan kecepatan > 0,6 m/s, dibagi dua menurut jumlah record;
  rasio tiap paruh = kecepatan rata-rata ÷ HR rata-rata; (rasio 1 − rasio 2) ÷ rasio 1. Dua versi: data penuh dan
  tanpa 3 km pertama (yang dinilai). Dihitung pada lari terpanjang tiap minggu (≥ 10 km); dinilai hanya bila ≥ 20 km
  dan bukan minggu lomba. Tombol ⓘ di kartu Decoupling menampilkan hitungan lengkap kedua versi dan cara memperbaikinya.
- **Saran**: setiap status kuning/merah diberi satu saran singkat dari dokumen (juga di rincian lampu).
- **Minggu ringan/lomba** dibaca dari warna baris Kalender (abu-abu / oranye muda).

## Struktur

```
pacelab.py            CLI
pacelab/garmin.py     client Personal API (token 24 jam, retry, key tidak pernah dicetak)
pacelab/sync.py       sync inkremental → data/<ATLET>/
pacelab/program.py    pembaca Excel program (xlsx.py: pembaca .xlsx tanpa library)
pacelab/metrics.py    semua perhitungan
pacelab/build.py      data → dist/dashboard.html (web/template.html)
tools/mock_garmin.py  server Garmin tiruan untuk tes & demo
tests/                python -m unittest discover -s tests
```
