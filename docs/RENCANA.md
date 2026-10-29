# Rencana yang belum diputuskan

Diperbarui 29 Okt 2026. Tidak ada yang dikerjakan sebelum omPik memilih dan bilang "gas".
Setiap rencana punya mockup dulu (lihat CLAUDE.md).

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
