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
python pacelab.py check      # cek field Garmin yang terbaca (hanya jumlah & nama field) + daftar lari tanpa data per detik
python pacelab.py demo       # dashboard dari data rekaan, tanpa key/internet
python pacelab.py inspect    # struktur respons Garmin (nama field & tipe, tanpa nilai); untuk lari terakhir: kepadatan data per detik, boleh/tidaknya unduh file FIT (jumlah lap)
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
catatan coaching; ←/→ pindah minggu, Esc tutup). Saat lintasan ter-scroll ke atas, kedua pelari melompat melengkung
ke tepi kiri (Taofik) dan kanan (Reza) lalu parkir; scroll ke atas membuat mereka lompat pulang. Saat ada data di belakangnya,
ikon pelari memudar. Lalu dua tab: **Ringkasan** (head-to-head,
**Latihan**, **Pemulihan**, **Progres terbaik**, **Badge**) dan **Sesi** (lihat di bawah). Saat header besar sudah
ter-scroll, header ringkas melekat di atas (hitung mundur, progres, tab). Tab terakhir diingat browser.
Tombol di kanan atas menyalakan/mematikan tiap pelari.

| Bagian | Sumber |
|---|---|
| Hitung mundur, minggu program, fase, tanda lomba | Excel: Kalender, Checkpoint |
| Ringkasan head-to-head | lampu hari ini, est. maraton, km & long run minggu ini, HRV, Body Battery, tidur, RHR, aturan Sabtu |
| Est. maraton | Riegel (eksponen 1.06): prediksi tercepat dari usaha terbaik 5K, 10K dan Half dalam 120 hari terakhir; ditampilkan juga + koreksi panas 5% |
| Menuju 42K | long run terpanjang sejak awal program |
| Skor minggu lalu | % target km, % target long run, rata tidur vs target minimum masing-masing, jumlah hari hijau |
| Latihan (filter 4 / 12 minggu / semua) | km, long run, decoupling, berat vs target per minggu yang sudah selesai; sumbu = tanggal awal minggu |
| Pemulihan (filter 7 / 14 / 30 / 60 hari) | lampu harian, tidur, HRV, Body Battery |
| 5K / 10K / Half | segmen tercepat di dalam setiap lari (data per detik): satu titik per lari. Lari yang jarak GPS-nya sedikit kurang (≥ 98%, `config.json` `effort.min_frac`) dan lari terpanjang di hari tes Checkpoint (≥ 80%, `effort.test_min_frac`) ikut dihitung: waktunya disetarakan ke jarak penuh dengan pace rata-rata, ditandai ≈ [keputusan omPik; 80% keputusan dashboard]. Klik kartu = jendela detail (grafik besar, hover ke titik terdekat, 4 mgg / 12 mgg / semua, ringkasan per pelari, 5 tercepat, ←/→ pindah jarak); garis tipis bertangga = rekor berjalan sampai hari ini, titik bercincin = tercepat. Belum ada data: grafik bayangan + tanggal tes berikutnya |
| Full | estimasi per akhir bulan, di atas pita target B; status target per pelari sebagai chip (batas, + panas, saran saat disentuh). Keempat kartu sama tinggi, grafik mengisi sisa ruang |
| Badge | 21/25/30/35K, 100 km/bulan, streak 7 & 14 minggu ≥90% target km, PR 5K/10K selama program |

### Tab Sesi

- **Linimasa cermin**: Taofik kiri, tanggal di tengah, Reza kanan; terbaru di atas; dikelompokkan per minggu program,
  dalam kotak setinggi 10 minggu: minggu yang terbuka penuh + 9 minggu tertutup (satu baris tipis), tidak lebih tinggi dari
  sisa layar di bawah header ringkas. Begitu kotak dipakai (klik / scroll), halaman bergeser sampai kotak pas di bawah header
  ringkas. Minggu aktif terbuka; membuka satu minggu menutup yang lain. Yang tidak sedang dibuka jadi abu-abu pudar dan sedikit mengecil. Warna kartu sesi memudar dari tepi
  luar: makin pekat = makin patuh rencana. Rencana yang belum dijalani = satu baris tipis.
- **Klik hari** = duel sesi: jarak, pace, HR rata, cadence, meter per detak; penilaian pelatih per jenis sesi (✓ / !);
  **Lap jam** (utama, dari file FIT): tiap lap jadi blok setinggi jaraknya dan selebar kecepatannya, kedua pelari sejajar
  per km; lap manual / sisa akhir lebih pudar; sentuh blok untuk pace, jarak, waktu, HR, cadence, asal lap.
  **Per km** (cadangan, dari data per detik): batang = kecepatan. Pita = rentang pace rencana; garis HR / cadence / elevasi
  bisa dinyalakan/dimatikan, ditumpuk di jalur luar. Waktu di zona HR; kesimpulan + saran tiap pelari.
  **Efek latihan** dan **Data Garmin** (apa adanya, ditandai GARMIN): efek latihan aerobik / anaerobik (0–5) + label + beban
  latihan, lalu tabel cermin: waktu bergerak / total, HR maks, ambang laktat, cadence, panjang langkah, kontak tanah,
  osilasi & rasio vertikal, power, elevasi, suhu, kalori, langkah, perkiraan keringat, jumlah lap. Yang tidak dikirim
  jam salah satu pelari ditulis "–".
  Penilaian tempo dan pemanasan memakai lap bila ada (lap yang tengahnya di rentang rencana ± 300 m) [keputusan dashboard].
- **Rincian hitungan** (tombol ⓘ di kartu Pace di zona 2 dan Meter per detak): tiap minggu, setiap sesi dan lap yang
  dipakai atau dicoret (dengan alasannya), jumlahnya, hasilnya, dan rumusnya, untuk dicocokkan dengan Garmin Connect.
- **Arah** (8 minggu terakhir vs sekarang; angka biru = Taofik, oranye = Reza; ▲▼ dijelaskan saat disentuh):
  pace di zona 2, meter per detak, jarak per minggu, long run terjauh menuju 42K, decoupling, cadence vs target.
- Rencana per hari dibaca dari teks sel Kalender Excel: `Total X km` (atau `X km` pertama), rentang pace `m:ss - m:ss/km`
  ("3 km pertama" = rentang pembukaan), "Detak jantung lo - hi" atau "di bawah X", "Pemanasan X km", "Tempo X km".
- Sync juga mengunduh **file FIT asli dari jam** untuk setiap lari (sekali): lap persis seperti di jam, dan data per
  detik untuk lari yang detail Garmin-nya kosong (Garmin hanya memberi detail ±120 hari terakhir). Ringkasan Garmin per
  lari (HR maks, cadence, elevasi, training effect, beban, power, suhu, langkah, jumlah lap) disimpan apa adanya.
- Cadence dan elevasi per detik ikut diunduh. **Update berikutnya mengunduh ulang semua lari sekali** (lebih lama);
  setelah itu kembali inkremental. Kalau cadence kosong pada data asli: `python pacelab.py inspect`.

| Hitungan | Rumus | Dasar |
|---|---|---|
| Pace di zona 2 | pace berbobot waktu (total waktu ÷ total km) dari **lap jam** (file FIT, ≥ 0,5 km) yang HR rata-ratanya di zona 2 (`zones[0] ≤ HR < zones[1]`, `config.json`), dari lari santai, long run, pemulihan; lari tanpa file FIT: potongan per km dari data per detik | [keputusan dashboard]; lap jam: keputusan omPik |
| Meter per detak | (jarak ÷ waktu) ÷ (HR ÷ 60), rata-rata lari selain latihan keras per minggu | [keputusan dashboard] |
| Cadence (sesi, kartu Arah) | cadence rata-rata dari Garmin per lari (`averageRunningCadenceInStepsPerMinute`), apa adanya; per minggu = rata-rata sesi. Hanya bila Garmin tidak mengirimnya: dari data per detik | keputusan omPik |
| Per km | km dipotong per 1000 m dari data per detik; HR rata berbobot waktu; potongan terakhir < 300 m dibuang | [keputusan dashboard] |

Semua angka penilaian diambil dari **profil pelari di `config.json`**, bukan dari kode: blok `coach` (berlaku untuk semua,
bisa ditimpa per pelari dengan `"coach"` di data pelari), `zones`, dan `pace` (rentang dari dokumen §3). Rentang pace/HR dari
sel Excel hari itu dipakai lebih dulu; profil jadi cadangan.

| Penilaian pelatih | Aturan (kunci `config.json`) | Dasar |
|---|---|---|
| Jarak | 95–110% rencana (`coach.km`). Long run yang dipotong gerbang pagi (−20% / −40% / ganti easy 8 km, dokumen §7) dihitung patuh | [keputusan omPik]; aturan betis diabaikan |
| HR lari santai / pemulihan | hanya km di **atas** batas atas yang dihitung, maksimal 20% km (`coach.hr_over_max`); di bawah rentang aman | [keputusan omPik] |
| HR long run | boleh lewat batas atas hanya di 25% bagian akhir (`coach.lr_tail`) dan decoupling < 8% (`coach.dec_max`). Kalau decoupling tidak ada: ≥ 75% km tidak lewat batas (`coach.lr_hr_in`) | [keputusan omPik] |
| Pace lari santai / long run | tidak dinilai; km yang lebih cepat dari batas cepat ditandai, lebih lambat tidak apa-apa | [keputusan omPik], dokumen §3 "HR mengalahkan pace" |
| Long run: buka 3 km pelan | pace 3 km pertama tidak lebih cepat dari batas cepat pembukaan − 10 dtk (`coach.open_tol_s`) | dokumen §6; 10 dtk [keputusan dashboard] |
| Long run: decoupling | < 8%; dinilai hanya ≥ 20 km dan bukan minggu lomba | dokumen §6 |
| Long run: cadence bertahan | turun < 5 spm dari paruh 1 ke paruh 2 (`coach.cad_drop`) | dokumen §6 |
| Long run: durasi | ≤ 210 menit (`coach.lr_max_min`) | dokumen §4 |
| Tempo: pace per km | tiap km tempo di rentang ± 5 dtk (`coach.tol_s`); "sedikit terlalu cepat" / "terlalu lambat". Reza: HR jadi patokan (`pace.hr_leads`), pace tidak dinilai kalau HR aman | [keputusan omPik], dokumen §3 |
| Tempo: HR | HR per km ≤ batas atas; km pertama tempo tidak dihitung | [keputusan omPik] |
| Interval: pace | tidak dinilai: data per km tidak memisahkan repetisi | [keputusan dashboard] |
| Pemanasan | pace ≥ batas cepat pace santai (`pace.easy`) dan HR rata ≤ batas atas Z2 (`zones[1]`) | [keputusan omPik] |
| Kepatuhan (cincin, warna kartu) | rata-rata: skor jarak (1 di dalam jendela), % km pace sesuai aturan di atas, % km HR tidak lewat batas atas | rumus disetujui omPik, disesuaikan aturan di atas |

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
pacelab/fit.py        pembaca file FIT Garmin (lap, sesi, data per detik) tanpa library
tools/fitgen.py       penulis file FIT kecil untuk server tiruan dan tes
pacelab/build.py      data → dist/dashboard.html (web/template.html)
tools/mock_garmin.py  server Garmin tiruan untuk tes & demo
tests/                python -m unittest discover -s tests
```
