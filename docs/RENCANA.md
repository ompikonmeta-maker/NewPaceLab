# Rencana yang belum diputuskan

Diperbarui 29 Okt 2026 (sore). Tidak ada yang dikerjakan sebelum omPik memilih dan bilang "gas".
Setiap rencana punya mockup dulu (lihat CLAUDE.md).

## Daftar perbaikan 1–5 — **sudah dibuat** (29 Okt): M4, A+B+C, 3a, tanpa bayangan, 10 minggu

1. **Penanda minggu aktif di batang target km mingguan** (kotak panjang di sekeliling batang minggu ini, di bawah
   lintasan) terlalu tegas. Buat lebih tenang, atau beri beberapa opsi garis yang lebih tenang. Sekarang:
   `.wkcol.now{outline:1.5px solid var(--text)}` di `pacelab/web/template.html`.
2. **Kartu Progres terbaik (5K / 10K / Half / Full) banyak ruang kosong.** Tinggi satu baris kartu ikut kartu Full
   (status target, + panas, saran), jadi 5K/10K punya celah besar antara angka dan grafik; kartu Half yang belum ada
   datanya tetap setinggi kartu lain dan hanya berisi "belum ada".
   omPik: **tinggi semua kartu tetap sama.** Usulan solusi (mockup nanti):
   - A. Grafik mengisi sisa tinggi kartu (kartu jadi kolom fleksibel), jadi celah di 5K/10K hilang dan grafik lebih tinggi.
   - B. Isi kartu Full dipadatkan (status + panas + saran jadi satu baris chip, rincian di tooltip) supaya teks semua
     kartu kira-kira sama tinggi; grafik tetap sejajar di bawah.
   - C. Kartu kosong (Half belum ada data) diisi grafik bayangan + info kapan tes Half berikutnya, bukan ruang kosong.
3. **Grafik Reza di 5K / 10K berhenti di Juli.** Sudah dicek: grafik hanya menggambar titik saat rekor membaik
   (`renderPB`, data `pb` di `metrics`). Rekor 5K Reza terakhir membaik akhir Juli, 10K pertengahan Juli; sesudahnya
   belum ada segmen yang lebih cepat, jadi garis berhenti. Garis Taofik sampai Oktober karena ia memecahkan rekor
   di Oktober. Bukan data hilang (perlu dipastikan di data asli: lari Reza Agustus–Oktober ada di Latihan).
   ~~Usulan: garis diteruskan datar sampai hari ini.~~ **omPik memilih:** tampilkan semua data — segmen 5K tercepat
   dari setiap lari (bukan hanya saat rekor membaik) — lalu highlight titik yang tercepat. Sama untuk 10K, Half, dst.
   Perlu: build mengirim usaha terbaik per lari per jarak (sekarang hanya deret rekor).
4. **Bayangan abu-abu saat hari diklik** (kartu sesi yang dibuka, mis. Reza Kamis 29 Okt) dihilangkan. Asalnya dari
   fokus F3: `.ss-box.fx2 .ss-fr.on .ss-sc{box-shadow:0 12px 32px …}`, ditambah warna gradasi kartu yang ikut terlihat
   seperti bayangan di sisi luar.
5. **Linimasa: kotak setinggi 10 minggu** (sebelumnya 8; di HP tetap maksimal 78% layar).

Mockup semua nomor: [`docs/mockup/perbaikan-1.html`](mockup/perbaikan-1.html) — menunggu pilihan dan "gas".

## 0c. Penilaian pelatih v2 + ikon transparan — **sudah dibuat** (29 Okt)

Mockup: [`docs/mockup/penilaian-pelatih-v2.html`](mockup/penilaian-pelatih-v2.html).
Diputuskan 29 Okt: jarak 95–110% (potongan gerbang tidur dihitung patuh, aturan betis diabaikan); HR hanya dinilai
di atas batas atas; long run opsi B (lewat batas hanya di 25% akhir + decoupling < 8%, cadangan A ≥ 75% km bila
decoupling tidak ada); pace santai tidak dinilai, hanya km lebih cepat dari batas cepat ditandai; tempo/interval per km
±5 dtk, km 1 tempo tidak dihitung untuk HR; pemanasan ≥ batas cepat pace santai dan HR ≤ batas atas Z2. Semua angka
dari profil pelari di `config.json`. Dicatat di README sebagai [keputusan omPik]. Ikon pelari memudar saat menutupi data.

## 0d. Linimasa 8 minggu + fokus + gradasi + lompatan pelari — **sudah dibuat** (29 Okt): F2+F3, G4, J3 tanpa pegas

Mockup: [`docs/mockup/linimasa-fokus.html`](mockup/linimasa-fokus.html). Kotak setinggi 8 minggu dengan scrollbar
yang hilang sendiri; buka satu minggu = yang lain tertutup. Fokus dipilih: F2 + F3 (pudar abu-abu + mengecil,
yang aktif terangkat dengan bayangan). Lompatan dipilih: J3 + pegas. Gradasi: G1 cermin (pekat = dekat target km) ·
G2 batang progres + garis target · G3 garis tengah + bingkai (hiasan) · G4 kartu sesi (pekat = kepatuhan); boleh gabung.

## 0b. Tab "Sesi" — T3 + A versi 7, Long run A + Cadence A — **sudah dibuat** (29 Okt)

Sudah ada di dashboard (lihat README, bagian Tab Sesi). Sisa: cek cadence/elevasi pada data Garmin asli
(kalau kosong: `python pacelab.py inspect`).

Versi 7: garis HR / cadence / elevasi ditumpuk jadi satu di jalur luar (batang pace terpisah); angka kartu Arah
opsi B (berwarna biru/oranye); setiap ▲▼ punya penjelasan bahasa sederhana saat disentuh; opsi grafik Long run
(A menuju 42K · B batang per minggu · C garis per minggu) dan Cadence (A pita target · B garis + pita ·
C jarum metronom): dipilih Long run A + Cadence A.


Versi 6 (hanya yang dikomentari): nama hari lengkap; tooltip per km satu baris per pelari; garis HR / cadence /
elevasi bisa ditumpuk langsung di atas batang pace (opsi baru) atau di jalur luar (v5); penanda pemilik angka di
kartu Arah: A nama kecil, B angka berwarna, C pil berwarna, D label langsung di grafik — menunggu pilihan.


Mockup: [`docs/mockup/tab-sesi-T3A.html`](mockup/tab-sesi-T3A.html). Data rekaan.

- T3: header besar tetap; saat di-scroll muncul header ringkas melekat (hitung mundur, progres, tab Ringkasan | Sesi).
- A: linimasa cermin dikelompokkan per minggu program; minggu aktif terbuka, minggu lain tertutup (ringkasan km dan
  sesi dijalani/terjadwal tiap pelari); klik minggu = buka/tutup.
- Klik hari: detail duel terbuka dan baris tanggal otomatis bergeser ke atas layar (di bawah header ringkas).
- Baris angka: kolom angka menyesuaikan angka terlebar; semua batang mulai dari garis putus-putus yang sama;
  tidak ada penanda unggul.
- Per km: tombol Detak jantung / Cadence / Elevasi; yang aktif ditumpuk dalam satu jalur, dibedakan jenis garis
  (HR garis penuh + titik, cadence putus-putus, elevasi titik-titik + area).
- Rencana yang belum dijalani: satu baris tipis (km rencana di kiri/kanan, tanggal di tengah).
- Satuan selalu ditulis (bpm, spm, m, j, %, /km, kg); "Body Battery" ditulis lengkap (skor 0–100, tanpa satuan).
- Arah: pace zona 2 = lintasan (titik bergerak dari 8 minggu lalu ke sekarang); meter per detak = garis miring
  dulu → sekarang; jarak per minggu = batang cermin atas/bawah; long run = tangga menuju 42K; decoupling = jarum
  di busur zona dokumen (<5, 5–8, ≥8); cadence = jejak titik di pita target.
- Data baru yang dibutuhkan dari Garmin: cadence dan elevasi per detik (sync diubah, semua lari diunduh ulang sekali).

## 0a. Tab "Sesi" (versi 3, 29 Okt malam) — sudah dipilih T3 + A

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
