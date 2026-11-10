# Rumus, Batas Angka, dan Sumber — Program Marathon 2027 (Taofik & Reza)

Versi 10 Nov 2026. Perubahan terakhir:
- §7b: aturan lampu (hijau/kuning/merah)
- §5: jarak strides dalam rencana
- §3b (8 Nov): cara menentukan target lomba

Satu tempat untuk semua angka yang dipakai di Excel, skrip `pacelab_analyze.py`, NewPaceLab, dan saran harian.

**Tanda jenis dasar:**
- **[P]** penelitian / pedoman resmi
- **[K]** keputusan pelatih atau praktik umum (masuk akal, tapi bukan hasil penelitian khusus)
- **[E]** perkiraan kasar

---

## 1. Kalender

| Hal | Rumus / angka | Dasar |
|---|---|---|
| Nomor minggu (MS) | MS = bulat_bawah((tanggal − 22 Jun 2026) / 7) + 1. Minggu = Senin–Minggu | [K] |
| Hari lomba | Minggu 13 Jun 2027 = MS51 | — |
| Tukar sesi | Kalau sesi digeser (misalnya long run pindah ke Minggu), catat di `overrides.json`. Penilaian memakai sesi yang ditukar | [K] |

## 2. Detak jantung dan zona

| Hal | Rumus / angka | Dasar |
|---|---|---|
| LTHR (ambang batas) | Rata-rata HR **20 menit terakhir** dari usaha keras ~30 menit, dilari sendiri | [P] Friel, *The Triathlete's Training Bible* |
| LTHR Taofik | **176**. Tes 28 Jun: 175,8. Lomba 10K 7 Nov tidak mendukung dugaan 178–179 | data tes |
| LTHR Reza | **173**. Tes 25 Jul: 173,2. Race 5K 11 Okt: 174. Perkiraan Garmin 7 Nov: 170 | data tes |
| HRmax | Taofik 201, Reza 191 (Reza mungkin sebenarnya 193–196) | data jam |
| Zona Taofik | Z1 <133, Z2 133–150, Z3 151–161, Z4 162–176, Z5 ≥177 | lihat catatan |
| Zona Reza | Z1 <139, Z2 139–152, Z3 153–163, Z4 164–173, Z5 ≥174 | lihat catatan |
| Waktu di zona | Dihitung tiap detik dari HR per record. Celah lebih dari 10 detik dipotong jadi 10 detik | skrip |

**⚠ Catatan zona:** batas zona kedua pelari **tidak memakai persentase LTHR yang sama**.

| | Awal Z2 | Awal Z3 | Awal Z4 | Awal Z5 |
|---|---|---|---|---|
| Taofik | 76% LTHR | 86% | 92% | 101% |
| Reza | 80% LTHR | 88% | 95% | 101% |

Penyebabnya: zona Taofik berasal dari data lama, sedangkan zona Reza dihitung ulang. Lomba 10K 7 Nov gagal sebagai kalibrasi, jadi **penyamaan rumus zona ditunda sampai half marathon 23 Jan 2027.**

## 3. Pace

| Hal | Rumus / angka | Dasar |
|---|---|---|
| Prediksi waktu jarak lain | T2 = T1 × (D2/D1)^1,06 | [P] Riegel 1981, *American Scientist* |
| VDOT dan pace latihan | Tabel Daniels dari waktu lomba | [P] Daniels, *Daniels' Running Formula* |
| Koreksi panas untuk prediksi lomba | Lihat §3b langkah 2 | [K] |
| Panas saat latihan keras | Di atas 30°C: perlambat 5–8%. Di atas 32°C: jadi lari santai | [K], arah sejalan dengan Ely 2007 (MSSE) dan konsensus panas Racinais 2015 (BJSM) |
| Aturan utama | **HR mengalahkan pace.** Kalau HR lewat batas atas, pace diturunkan | [K] |

| Pace (/km) | Taofik | Reza |
|---|---|---|
| Recovery | 9:15–9:45 | 9:20–9:50 |
| Easy / long run | 8:40–9:15 | 8:45–9:20 |
| Pace maraton (MP) | 7:15–7:30 | 7:45 sekarang, target 7:30 |
| Half marathon | 7:00 | ~7:30 |
| Tempo ≤4 km | **6:00–6:10** | 7:10–7:20, HR jadi patokan |
| Tempo ≥5 km | **6:10–6:20** (berdasarkan lomba 10K 7 Nov) | 7:10–7:20, HR jadi patokan |
| Interval | 6:00–6:15 (ditinjau 23 Jan) | 6:20–6:30 |

## 3b. Cara menentukan target lomba (WAJIB, berlaku sejak 8 Nov 2026)

Aturan ini lahir dari kesalahan target lomba 10K 7 Nov. Targetnya 59:24, hasilnya 68:49. Penyebabnya: target dihitung dari usaha pendek, dan aturan panas tidak dipakai.

| Langkah | Aturan | Dasar |
|---|---|---|
| 1. Dasar hitungan | **Hanya waktu lomba atau tes UTUH** (minimal 5 km tanpa berhenti), dihitung pakai Riegel. **Dilarang** memakai potongan tempo, interval, atau km tercepat dalam lomba | [P] Riegel 1981. Pelajaran 7 Nov |
| 2. Koreksi panas | Suhu saat start 28–30°C: +3%. 30–32°C: **+5%**. Di atas 32°C: **+8%** | [K] sesuai §3; arahnya sejalan dengan Ely 2007 |
| 3. Koreksi kelelahan | Long run ≥18 km kurang dari 7 hari sebelum lomba: **+2%** | [K] |
| 4. Koreksi jam start | Start setelah 06:00: pakai perkiraan suhu di km terakhir, bukan suhu saat start | [K] |
| 5. Paruh pertama | **Dikunci pakai HR, tanpa target pace.** km 1 ≤ LTHR − 15, km 2 ≤ LTHR − 6, km 3–5 ≤ LTHR − 2 | [K] |
| 6. Paruh kedua | Pace boleh naik setelah km 5 **hanya kalau** HR masih ≥4 denyut di bawah LTHR | [K] |
| 7. Target yang ditulis | Selalu dalam bentuk **rentang** (misalnya 64–66 menit), bukan satu angka | [K] |
| 8. Cek silang | Kalau target lebih cepat dari hitungan Riegel tanpa koreksi, **target salah**. Pakai hasil Riegel yang sudah dikoreksi | [K] |

**Contoh (Taofik, 7 Nov, kalau aturan ini sudah dipakai):** 5K 31:29 → Riegel 65:38 → panas +5% → kelelahan +2% → **sekitar 70 menit** (rentang 69–71). Kalau 31:29 dianggap terlalu lambat karena start penuh sesak, angka itu dipakai sebagai batas lambat saja, bukan dibuang.

**Aturan km pertama (semua tempo, tes, dan lomba):**
- km 1 dilari **di pace paling lambat dari rentang, atau lebih lambat lagi.**
- Kalau km 1 ternyata 10 detik lebih cepat dari rencana, km 2 **wajib** 10 detik lebih lambat.
- Pasang alert di jam: pace minimum dan HR maksimum.

Riwayat start terlalu cepat: Reza 15 Okt, 27 Okt, 1 Nov, 7 Nov (km 1 di 6:17, padahal rencananya 7:25).

## 4. Volume dan risiko cedera

| Hal | Rumus / batas | Dasar |
|---|---|---|
| **Aturan 110% (utama)** | Long run ≤ 1,1 × lari terpanjang dalam 30 hari terakhir | [P] Frandsen dkk. 2025, BJSM (5.200 pelari): satu sesi lebih dari 10% di atas lari terpanjang 30 hari → risiko cedera naik |
| Kenaikan volume mingguan | Hati-hati kalau naik lebih dari 30% dalam 2 minggu | [P] Nielsen dkk. 2014, JOSPT (pelari pemula) |
| "Aturan 10%" mingguan | **Tidak dipakai** sebagai pengaman utama | [P] Buist 2008, AJSM: tidak menurunkan cedera pada pemula |
| ACWR (rasio akut:kronis) | Volume minggu ini ÷ rata-rata 4 minggu sebelumnya. Alarm kalau lebih dari 1,3 | [P] Gabbett 2016, BJSM. Banyak dikritik (Impellizzeri 2020), jadi dipakai sebagai alarm kasar saja |
| Batas durasi long run | Berhenti di 210 menit (3 jam 30 menit), berapa pun km-nya | [K] praktik umum pelatih maraton amatir |
| Minggu ringan | Tiap minggu ke-4, volume turun sekitar 30% | [K] |
| Lari sehari setelah lomba | Pemulihan 6 km, bukan lari sedang | [K] |
| Long run terhadap volume mingguan | Saat ini 45–55%. Pedoman pelatih biasanya ≤30–35%. Diterima karena cuma lari 4 hari seminggu; pengamannya aturan 110% | [K] |
| Pemanasan / pendinginan latihan keras | Pemanasan 2–2,5 km, pendinginan 1–3 km. Jumlahnya harus sama dengan "Total" di sel | [K] |
| Penilaian jarak sesi | Patuh kalau 95–110% dari jarak rencana. Jarak rencana sudah termasuk tambahan strides (§5). Potongan yang disengaja karena gerbang (§7/§7b) dihitung patuh | [K] |

## 5. Intensitas

| Hal | Angka | Dasar |
|---|---|---|
| Porsi latihan keras | Sekitar 9% dari total km. Sisanya santai | [P] Seiler 2010 (IJSPP); Stöggl & Sperlich 2014 (Front Physiol): pola sekitar 80/20 |
| Jeda setelah long run | Latihan keras paling cepat 48 jam setelah long run. Gerbangnya: HR saat pemanasan normal | [K] |
| Tempo | Km pertama di pace paling lambat dari rentang. Rasanya berat tapi terkendali, masih bisa 3–4 kata | [K] |
| Strides | 12–20 detik cepat (85–90% usaha), lalu jalan 60 detik, 4–6×, dalam satu file rekaman yang sama | [K] |
| **Jarak strides dalam rencana** | Kalau sel menyebut strides: **+0,15 km per stride** (termasuk jalan kakinya). Contoh: "6 km + 6 strides" = 6,9 km. Pendinginan yang tidak tertulis di sel: +0 | [K] keputusan 10 Nov 2026 |
| Deteksi strides | Kecepatan dari jam (`enhanced_speed`) >2,6 m/s selama minimal 6 detik. Jangan pakai kecepatan dari selisih jarak, karena puncaknya terbaca terlalu cepat | [K] |

## 6. Long run: aturan khusus

| Hal | Angka | Dasar |
|---|---|---|
| Pembukaan | 3 km pertama di pace recovery. Transisi ke pace easy di km 4–6 | [K] |
| **Decoupling (Pa:HR)** | Lihat rumus di bawah tabel | [P] Friel / TrainingPeaks: di bawah 5% = daya tahan aerobik bagus |
| Target decoupling | Di bawah 8% untuk long run ≥20 km sebelum MS43. Lebih longgar dari 5% karena panas | [K] |
| HR long run (aturan B) | HR boleh lewat batas atas **hanya di 25% bagian akhir**, dan decoupling di bawah 8%. Cadangan kalau decoupling tidak bisa dihitung (aturan A): lulus kalau ≥75% km di bawah batas atas | [K] keputusan 29 Okt 2026 |
| Cadence paruh 1 → paruh 2 | Waspada kalau turun 5 atau lebih. Hitung hanya saat berlari (kecepatan >1,5 m/s), tanpa jalan kaki | [K] tanda bentuk lari mulai rusak karena capek |
| Target cadence | Taofik 168–172, Reza 172–176. Naik maksimal sekitar 10% bertahap | [P] Heiderscheit 2011 (MSSE): cadence +5–10% mengurangi beban lutut dan pinggul |

**Rumus decoupling:**
- Ambil hanya record dengan HR di atas 80 dan kecepatan di atas 0,6 m/s (kecepatan dari jam).
- Bagi dua berdasarkan jumlah record (paruh 1 dan paruh 2).
- Rasio tiap paruh = kecepatan rata-rata ÷ HR rata-rata.
- Decoupling = (rasio paruh 1 − rasio paruh 2) ÷ rasio paruh 1 × 100%.
- Dilaporkan dua versi: data penuh, dan tanpa 3 km pertama (dihitung menurut jarak). Yang dinilai versi tanpa 3 km pertama.
- **Hanya berlaku untuk lari dengan pace rata.** Untuk tempo, interval, lomba, dan lari dengan strides: tulis "tidak berlaku".

## 7. Tidur dan pemulihan (gerbang pagi)

Gerbang dinilai dari **data pagi di hari sesi itu sendiri** (misalnya long run Sabtu memakai data Sabtu pagi).

| Kondisi | Tindakan | Dasar |
|---|---|---|
| Tidur ≥6 jam **dan** Body Battery ≥50 | Jalankan sesuai rencana | [K] |
| Tidur 5–6 jam **atau** Body Battery <50 | Long run dipotong 20%, pace recovery | [K] |
| Tidur <5 jam **dan** Body Battery <40 | Long run dipotong 40% | [K] |
| HRV di bawah normal (Taofik <43), atau RHR naik ≥5 | Latihan keras jadi lari santai | [P] arah sejalan dengan latihan berpanduan HRV (Kiviniemi 2007, EJAP) |
| Target tidur | Taofik minimal 6 jam 30 menit, Reza minimal 6 jam 15 menit. Malam sebelum long run 7 jam | [K]. Penelitian perpanjangan tidur menunjukkan performa naik (Mah 2011, *Sleep*) |
| Libur lari ≤7 hari | Ulangi minggu sebelumnya | [K], sejalan dengan tabel kembali-latihan Daniels |
| Libur lari 8–21 hari | Mundur 2–3 minggu di kalender | [K] |
| Libur lari >21 hari | Mulai lagi dengan lari-jalan | [K] |

Body Battery adalah angka buatan Garmin (rumusnya tidak dipublikasikan), jadi batasnya keputusan pelatih.

## 7b. Aturan lampu (keputusan 10 Nov 2026)

| Lampu | Penyebab | Long run | Latihan keras |
|---|---|---|---|
| **Hijau** | §7 lolos dan status HRV Balanced | Sesuai rencana | Sesuai rencana |
| **Kuning** | §7 baris 2, atau HRV semalam turun di bawah normal 1–2 malam | **Potong 20%** | Jadi lari santai |
| **Merah** | Status HRV Low/Unbalanced ≥3 hari, atau Garmin "Strained" | **Lari santai ≤8 km, atau istirahat** | Istirahat atau lari santai |

- Selalu pakai yang **paling ketat** antara §7 dan lampu.
- Sesi yang dilari lebih jauh atau lebih keras dari batas gerbang ditandai **"gerbang dilewati"**, bukan "patuh".
- Status HRV Garmin = rata-rata 7 hari dibanding rentang pribadi, bukan angka semalam. Angka HRV antar pelari tidak bisa dibandingkan.

## 8. Makan dan minum

| Hal | Rumus / angka | Dasar |
|---|---|---|
| Karbo saat lari | Lari 1–2,5 jam: 30–60 g/jam. Lebih dari 2,5 jam: sampai 90 g/jam, campur glukosa dan fruktosa | [P] Jeukendrup 2014, *Sports Med* |
| Tahapan latihan perut | MS7–15: 30–45 g/jam → MS16–33: 45–60 → MS39–46: 55–70 → MS47+: 60–75 | [K], mengikuti Jeukendrup |
| Isi gel | Dianggap 25 g per gel. **Cek label: GU biasanya 22 g** | label |
| Keringat per jam | (berat sebelum − berat sesudah + liter diminum) ÷ jam lari | [P] metode standar |
| Hasil tes keringat | Taofik 0,74 L/jam, Reza 0,77 L/jam | data tes |
| Batas kehilangan cairan | Berat badan turun tidak lebih dari 2% | [P] ACSM 2007 (Sawka), *Exercise and fluid replacement* |
| Sodium | Perlu untuk lari lebih dari 90 menit. Dosis per kapsul: cek label SaltStick | [K] |
| Carbo loading H-2 dan H-1 | Di Excel: 8–10 g/kg/hari. **⚠ Pedoman: 10–12 g/kg selama 36–48 jam** | [P] Burke 2011, *J Sports Sci*; Thomas dkk. 2016 (ACSM/AND/DC) |
| Protein | 1,6–2,0 g/kg/hari | [P] Morton 2018, BJSM: manfaat mendatar di sekitar 1,6 g/kg |

## 9. Berat badan

| Hal | Angka | Dasar |
|---|---|---|
| Kecepatan turun (Reza) | 0,19 kg/minggu (0,24% berat badan/minggu). Maksimal 0,5 kg/minggu | [P] Garthe 2011 (IJSNEM): turun pelan (~0,7%/minggu) menjaga otot lebih baik |
| Batas bawah | Taofik 65 kg, Reza 73 kg. Kalau rata-rata 4 minggu tembus ke bawah, tambah porsi makan | [K] |
| Defisit distop | Saat lampu merah, atau status HRV Low/Unbalanced | [K] |
| Beban per langkah | Sekitar 2–3× berat badan | [P] Cavanagh & Lafortune 1980 |
| Manfaat 1 kg turun | Sekitar 1,5–2,5 detik/km | [E] |
| Fase tanpa defisit | Absorb, Ramadan (kecuali turun sendiri), fase Marathon, Taper | [K] |

## 10. Latihan kekuatan (tanpa alat, mulai 28 Okt 2026)

| Hal | Angka | Dasar |
|---|---|---|
| Frekuensi | 2× seminggu: Rabu kaki, Jumat perut dan pinggul. Ramadan 1× seminggu | [K] |
| Intensitas | Sisakan 3–4 repetisi di akhir set | [K] |
| Manfaat cedera | Latihan kekuatan menurunkan cedera olahraga **menjadi kurang dari 1/3** (RR sekitar 0,32). Penelitiannya olahraga umum, bukan khusus lari | [P] Lauersen 2014, BJSM |
| Manfaat performa | Lari jadi lebih hemat tenaga | [P] Blagrove 2018, *Sports Med* |
| Lompatan (pogo, A-skip) | Baru mulai setelah 4 minggu rutin. Jangan sehari sebelum tempo atau long run | [K] |

## 11. Sepatu

| Hal | Angka | Dasar |
|---|---|---|
| Bergantian beberapa sepatu | Risiko cedera sekitar 39% lebih rendah | [P] Malisoux 2015, *Scand J Med Sci Sports* |
| Rotasi Taofik | Ultraboost (sekarang) → Novablast 6 → Superblast 3 (Des). Hindari Metaspeed | [K] |

## 12. Taper

| Hal | Angka | Dasar |
|---|---|---|
| Lama | 3 minggu (MS49–51) | [P] Bosquet 2007, MSSE: taper optimal ~2 minggu, volume turun 41–60%, intensitas dijaga |
| Volume | −28% → −45% → minggu lomba sangat ringan | [K] |
| Beban berat terakhir | 14 hari sebelum lomba | [K] |

## 13. Kalibrasi ulang

| Kapan | Apa |
|---|---|
| ~~Lomba 10K, 7 Nov 2026~~ | **Gagal sebagai kalibrasi.** Taofik banyak jalan kaki, Reza berhenti di 5 km. LTHR tetap 176 dan 173 (Garmin memperkirakan Reza 170). Data ini tidak mendukung dugaan LTHR Taofik 178–179 |
| Half marathon, 23 Jan 2027 | Penyamaan rumus zona, pace tempo dan interval dikunci (interval Taofik 6:00–6:15 sekarang hampir sama dengan tempo, perlu ditinjau), pace maraton dikunci. Target half marathon dibuat dengan aturan §3b |
| Tes 10K, 10 Apr 2027 | Evaluasi G3: decoupling di bawah 8% di long run ≥20 km |

---

### Yang perlu dibereskan
1. Rumus zona Taofik dan Reza berbeda → samakan di half marathon 23 Jan 2027.
2. Carbo loading 8–10 g/kg di Excel lebih rendah dari pedoman 10–12 g/kg → perlu diputuskan.
3. Isi gel dianggap 25 g, padahal GU 22 g → hitungan jumlah gel saat lomba bisa kurang 1–2.
4. ~~Sheet Kamus Latihan masih menulis "pendinginan 1 km"~~ → sudah dibetulkan 8 Nov.

### Daftar pustaka
- Blagrove RC dkk. 2018. Effects of strength training on the physiological determinants of middle- and long-distance running performance. *Sports Med*.
- Bosquet L dkk. 2007. Effects of tapering on performance: a meta-analysis. *Med Sci Sports Exerc*.
- Buist I dkk. 2008. No effect of a graded training program on the number of running-related injuries in novice runners. *Am J Sports Med*.
- Burke LM dkk. 2011. Carbohydrates for training and competition. *J Sports Sci*.
- Cavanagh PR, Lafortune MA. 1980. Ground reaction forces in distance running. *J Biomech*.
- Daniels J. *Daniels' Running Formula*.
- Ely MR dkk. 2007. Impact of weather on marathon-running performance. *Med Sci Sports Exerc*.
- Frandsen JSB dkk. 2025. How much running is too much? Identifying high-risk running sessions in a 5200-person cohort study. *Br J Sports Med*.
- Friel J. *The Triathlete's Training Bible*.
- Gabbett TJ. 2016. The training–injury prevention paradox. *Br J Sports Med*.
- Garthe I dkk. 2011. Effect of two different weight-loss rates on body composition and strength and power-related performance in elite athletes. *Int J Sport Nutr Exerc Metab*.
- Heiderscheit BC dkk. 2011. Effects of step rate manipulation on joint mechanics during running. *Med Sci Sports Exerc*.
- Impellizzeri FM dkk. 2020. Acute:chronic workload ratio: conceptual issues and fundamental pitfalls. *Int J Sports Physiol Perform*.
- Jeukendrup A. 2014. A step towards personalized sports nutrition: carbohydrate intake during exercise. *Sports Med*.
- Kiviniemi AM dkk. 2007. Endurance training guided individually by daily heart rate variability measurements. *Eur J Appl Physiol*.
- Lauersen JB dkk. 2014. The effectiveness of exercise interventions to prevent sports injuries. *Br J Sports Med*.
- Mah CD dkk. 2011. The effects of sleep extension on the athletic performance of collegiate basketball players. *Sleep*.
- Malisoux L dkk. 2015. Can parallel use of different running shoes decrease running-related injury risk? *Scand J Med Sci Sports*.
- Morton RW dkk. 2018. A systematic review, meta-analysis and meta-regression of the effect of protein supplementation on resistance training-induced gains in muscle mass and strength. *Br J Sports Med*.
- Nielsen RO dkk. 2014. Excessive progression in weekly running distance and risk of running-related injuries. *J Orthop Sports Phys Ther*.
- Racinais S dkk. 2015. Consensus recommendations on training and competing in the heat. *Br J Sports Med*.
- Riegel PS. 1981. Athletic records and human endurance. *American Scientist*.
- Sawka MN dkk. 2007. ACSM position stand: Exercise and fluid replacement. *Med Sci Sports Exerc*.
- Seiler S. 2010. What is best practice for training intensity and duration distribution in endurance athletes? *Int J Sports Physiol Perform*.
- Stöggl T, Sperlich B. 2014. Polarized training has greater impact on key endurance variables than threshold, high intensity, or high volume training. *Front Physiol*.
- Thomas DT, Erdman KA, Burke LM. 2016. Position of the Academy of Nutrition and Dietetics, Dietitians of Canada, and the ACSM: Nutrition and athletic performance. *Med Sci Sports Exerc*.
