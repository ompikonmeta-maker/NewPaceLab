# Rencana yang belum diputuskan

Diperbarui 29 Okt 2026 (sore). Tidak ada yang dikerjakan sebelum omPik memilih dan bilang "gas".
Setiap rencana punya mockup dulu (lihat CLAUDE.md).

## 0a. Tab "Sesi" (versi 3, 29 Okt malam) — menunggu pilihan

Mockup: [`docs/mockup/tab-sesi.html`](mockup/tab-sesi.html) (pilih opsi di bilah atas). Data rekaan.
Sudah diputuskan: cadence ditambah ke sync; rumus kepatuhan disetujui; pace di zona 2 dan meter per detak dua-duanya tampil.

- **Tab** (header hitung mundur + lintasan tetap terlihat): T1 judul besar + garis geser · T2 tombol pil berikon ·
  T3 header ringkas melekat di atas saat di-scroll (hitung mundur, garis progres, tab).
- **Isi Sesi**: A Linimasa cermin (Taofik kiri, tanggal di tengah, Reza kanan; terbaru di atas; dikelompokkan per MS) ·
  B Pita + duel · C Rapor pelatih (nilai mingguan A–D dari 4 pilar: konsistensi, intensitas, daya tahan, pemulihan).
- **Detail duel (sama di semua opsi), semuanya cermin**: angka di dekat sumbu, batang tumbuh keluar; penilaian
  pelatih per jenis sesi (✓ / !); grafik per km kupu-kupu (batang kecepatan + pita rentang rencana, garis HR di jalur
  luar); waktu di zona cermin; satu catatan + saran per pelari.
- **Arah**: angka Taofik rata kanan, Reza rata kiri, dua garis.
- Rumus nilai A–D (opsi C) belum ada di dokumen → [keputusan dashboard], perlu disetujui bila C dipilih.

## 0. Duel per sesi + Arah (versi lanjutan, 29 Okt) — digantikan 0a

Mockup: [`docs/mockup/duel-sesi.html`](mockup/duel-sesi.html). Data di mockup rekaan.
Menggantikan rencana 1 di bawah (B dan C sudah tercakup).

1. **Pita sesi** (monitoring + rekaman): dua jalur Taofik/Reza per hari. Bentuk = jenis sesi
   (bulat santai, kapsul long run, belah ketupat keras, titik kecil pemulihan), ukuran = jarak,
   cincin hijau/kuning = kepatuhan rencana, garis putus = sesi bolong, rencana ke depan abu-abu. 2 / 4 / 12 minggu.
2. **Kartu duel** (klik satu hari): cincin kepatuhan + kondisi pagi (tidur, BB) tiap pelari; baris cermin jarak, pace,
   HR, cadence, meter per detak, decoupling (titik = lebih baik); pace per km (dua grafik kecil satu skala, pita
   rentang rencana); HR per km (satu grafik); waktu di zona Z1–Z5 (cermin); satu catatan + saran per pelari.
3. **Arah** (tren 8 minggu, dua garis per kartu): pace di zona 2, jarak per minggu, long run, decoupling, cadence, tidur;
   angka sekarang + perubahan (hijau membaik, merah memburuk).
4. Istilah bergaris titik → tooltip bahasa sederhana + rumus (decoupling, meter per detak, pace di zona 2, cadence,
   kepatuhan, zona).

Perlu diputuskan:
- Letak: "Sesi" setelah Ringkasan; "Arah" menggantikan bagian Latihan (supaya tidak dobel) atau ditambahkan?
- Cadence: tambah ke sync (unduh ulang semua lari sekali)?
- Rumus **kepatuhan rencana** belum ada di dokumen → [keputusan dashboard], perlu disetujui
  (usulan: rata-rata jarak ÷ rencana, % waktu pace di rentang, % waktu HR di rentang).
- Pace di zona 2 dan meter per detak: tampilkan keduanya atau satu saja?

## 1. Detail hasil lari per sesi — menunggu pilihan

Mockup: [`docs/mockup/detail-sesi.html`](mockup/detail-sesi.html) (buka di browser).

| Opsi | Isi | Catatan |
|---|---|---|
| **C** Pintu masuk | Di jendela jadwal, "✓ km aktual" jadi tombol → buka detail sesi; ← kembali ke minggu itu | saran, dipasang bersama B |
| **B** Jendela detail sesi | Jarak, waktu, pace, HR rata; dibanding rencana Excel per bagian (3 km pembuka, pace & HR sisanya, durasi); grafik pace & HR per km dengan pita HR rencana; waktu di zona Z1–Z5 (dokumen §2); cek aturan 110%, batas 210 menit, jeda 48 jam (§4, §5); decoupling sesi itu | saran |
| **A** Daftar sesi | Tabel per pelari: tanggal, sesi, jarak, waktu, pace, HR; filter 4 / 12 minggu / semua; klik → B | opsional |
| **D** Cadence & elevasi | Cadence per km (target, aturan "paruh 2 turun ≥ 5", §6) dan elevasi (konteks tanjakan) | butuh ubah sync + unduh ulang semua lari sekali |

Yang perlu diputuskan juga: zona HR Taofik dan Reza beda rumus (dokumen §2), disamakan setelah lomba 10K 7 Nov.
Kalau B dipasang sebelum itu, dashboard memakai zona yang tertulis di dokumen sekarang.

## 2. Aturan dokumen yang belum dipakai di dashboard

| Aturan | Dokumen | Bisa tampil di |
|---|---|---|
| Aturan 110% untuk tiap long run | §4 | B, atau penanda di grafik Long run |
| Alarm ACWR > 1,3 (volume minggu ini ÷ rata 4 minggu sebelumnya) | §4 | kartu Jarak per minggu |
| Kenaikan volume > 30% dalam 2 minggu | §4 | kartu Jarak per minggu |
| Long run lebih dari 210 menit | §4 | B, grafik Long run |
| Fase tanpa defisit (Absorb, Ramadan, Marathon, Taper) | §9 | kartu Berat |
| Cadence paruh 2 turun ≥ 5 | §6 | B (butuh D) |

## 3. Menunggu data dari omPik

- Satu hasil decoupling dari `pacelab_analyze.py` (tanggal lari + angka) untuk dicocokkan dengan dashboard.

## 4. Lain-lain (pernah ditawarkan, belum dijawab)

- Arsipkan sesi Claude lama "Garmin Personal API downloader".
- Pindahkan `garmin_probe.py` ke `tools/`.
- Buat pull request ke `main`.

## Catatan, bukan rencana

- Fase "Awal" (22 Jun – 2 Agu, MS1–6) tidak punya batang target karena sheet Kalender di Excel mulai dari MS7.
- Temuan di dokumen bagian "Yang perlu dibereskan" (rumus zona, carbo loading, isi gel, Kamus Latihan) ada di file Excel,
  bukan di dashboard.
