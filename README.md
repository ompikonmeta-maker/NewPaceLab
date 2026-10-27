# NewPaceLab

Dashboard marathon Taofik & Reza: satu file HTML offline dari data Garmin Personal API dan program latihan Excel.

## Pakai

```
python pacelab.py            # tarik data Garmin kedua atlet, lalu buat dist/dashboard.html
python pacelab.py build      # buat ulang dashboard dari data yang sudah ada
python pacelab.py check      # cek field Garmin yang terbaca (hanya jumlah & nama field)
python pacelab.py demo       # dashboard dari data rekaan, tanpa key/internet
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

| Bagian | Sumber |
|---|---|
| Hitung mundur, MS, fase, minggu ringan/lomba | Excel: Kalender, Checkpoint |
| Menuju 42K | long run terpanjang sejak MS1 |
| Est. finish | Riegel (eksponen 1.06) dari usaha terbaik 120 hari terakhir: Half → 10K → 5K |
| MS berjalan, km & long run vs target | Garmin + Kalender |
| Skor minggu lalu | % target km, % target long run, rata tidur vs target minimum masing-masing, jumlah hari hijau |
| Lampu hari ini & aturan Sabtu | tabel "Tidur dan Pemulihan" di Excel (lihat di bawah) |
| km / minggu, long run, decoupling, berat vs target | minggu yang sudah selesai |
| Tidur, HRV, Body Battery | 14 hari terakhir |
| 5K / 10K / Half | segmen tercepat di dalam lari mana pun (data per detik), hanya saat rekor membaik |
| Full | estimasi per akhir bulan, di atas pita target B |
| Badge | 21/25/30/35K, 100 km/bulan, streak 7 & 14 minggu ≥90% target km, PR 5K/10K selama program |

### Tafsiran aturan Excel

Tabel di Excel ditulis untuk manusia; ini cara program membacanya.

- **HRV normal** = status Garmin `BALANCED`. **Di bawah normal** = `LOW` atau `POOR`.
- **Detak istirahat naik** = dibanding median 28 hari sebelumnya (minimal 7 hari data).
- **Lampu**: MERAH (HRV di bawah normal 3 hari, atau RHR +7) → ORANYE (HRV di bawah normal 2 hari, BB < 40, atau RHR +5) → HIJAU (HRV balanced, BB > 60, tidur ≥ 6 jam) → selain itu KUNING.
- **Body Battery harian** = nilai tertinggi hari itu (setelah tidur).
- **Aturan Sabtu**: tidur < 5 jam + BB < 30 + HRV di bawah normal → *Ganti easy 8 km*; tidur < 5 jam + BB < 40 → *Potong 40%*; tidur ≥ 6 jam + BB ≥ 50 → *Jalankan*; selain itu → *Potong 20%*.
- **Decoupling** = efisiensi (kecepatan ÷ HR) separuh pertama vs kedua waktu bergerak, pada lari terpanjang minggu itu (≥ 10 km).
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
