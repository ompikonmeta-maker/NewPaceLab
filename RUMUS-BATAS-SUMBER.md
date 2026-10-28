# Rumus, Batas Angka, dan Sumber — Program Marathon 2027 (Taofik & Reza)

Versi 28 Okt 2026. Satu tempat untuk semua angka yang dipakai di Excel, skrip `pacelab_analyze.py`, dan saran harian.

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

## 2. Detak jantung dan zona

| Hal | Rumus / angka | Dasar |
|---|---|---|
| LTHR (ambang batas) | Rata-rata HR **20 menit terakhir** dari usaha keras ~30 menit, dilari sendiri | [P] Friel, *The Triathlete's Training Bible* |
| LTHR Taofik | 176. Tes 28 Jun: 175,8. Kemungkinan sebenarnya 178–179 | data tes |
| LTHR Reza | 173. Tes 25 Jul: 173,2. Race 5K 11 Okt: 174 | data tes |
| HRmax | Taofik 201, Reza 191 (Reza mungkin sebenarnya 193–196) | data jam |
| Zona Taofik | Z1 <133, Z2 133–150, Z3 151–161, Z4 162–176, Z5 ≥177 | lihat catatan |
| Zona Reza | Z1 <139, Z2 139–152, Z3 153–163, Z4 164–173, Z5 ≥174 | lihat catatan |
| Waktu di zona | Dihitung tiap detik dari HR per record. Celah lebih dari 10 detik dipotong jadi 10 detik | skrip |

**⚠ Catatan zona:** batas zona kedua pelari **tidak memakai persentase LTHR yang sama**.

| | Awal Z2 | Awal Z3 | Awal Z4 | Awal Z5 |
|---|---|---|---|---|
| Taofik | 76% LTHR | 86% | 92% | 101% |
| Reza | 80% LTHR | 88% | 95% | 101% |

Penyebabnya: zona Taofik berasal dari data lama, sedangkan zona Reza dihitung ulang. **Akan disamakan dengan satu rumus setelah lomba 10K tanggal 7 Nov.**

## 3. Pace

| Hal | Rumus / angka | Dasar |
|---|---|---|
| Prediksi waktu jarak lain | T2 = T1 × (D2/D1)^1,06 | [P] Riegel 1981, *American Scientist* |
| VDOT dan pace latihan | Tabel Daniels dari waktu lomba | [P] Daniels, *Daniels' Running Formula* |
| Koreksi panas untuk prediksi | Ditambah sekitar 5% | [E] |
| Panas saat latihan keras | Di atas 30°C: perlambat 5–8%. Di atas 32°C: jadi lari santai | [K], arah sejalan dengan Ely 2007 (MSSE) dan konsensus panas Racinais 2015 (BJSM) |
| Aturan utama | **HR mengalahkan pace.** Kalau HR lewat batas atas, pace diturunkan | [K] |

| Pace (/km) | Taofik | Reza |
|---|---|---|
| Recovery | 9:15–9:45 | 9:20–9:50 |
| Easy / long run | 8:40–9:15 | 8:45–9:20 |
| Pace maraton (MP) | 7:15–7:30 | 7:45 sekarang, target 7:30 |
| Half marathon | 7:00 | ~7:30 |
| Tempo | **6:00–6:10** (sementara sampai 7 Nov) | 7:10–7:20, HR jadi patokan |
| Interval | 6:00–6:15 | 6:20–6:30 |

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

## 5. Intensitas

| Hal | Angka | Dasar |
|---|---|---|
| Porsi latihan keras | Sekitar 9% dari total km. Sisanya santai | [P] Seiler 2010 (IJSPP); Stöggl & Sperlich 2014 (Front Physiol): pola sekitar 80/20 |
| Jeda setelah long run | Latihan keras paling cepat 48 jam setelah long run. Gerbangnya: HR saat pemanasan normal | [K] |
| Tempo | Km pertama di pace paling lambat dari rentang. Rasanya berat tapi terkendali, masih bisa 3–4 kata | [K] |
| Strides | 12–20 detik cepat (85–90% usaha), lalu jalan 60 detik, 4–6×, dalam satu file rekaman yang sama | [K] |

## 6. Long run: aturan khusus

| Hal | Angka | Dasar |
|---|---|---|
| Pembukaan | 3 km pertama di pace recovery. Transisi ke pace easy di km 4–6 | [K] |
| **Decoupling (Pa:HR)** | Lihat rumus di bawah tabel | [P] Friel / TrainingPeaks: di bawah 5% = daya tahan aerobik bagus |
| Target decoupling | Di bawah 8% untuk long run ≥20 km sebelum MS43. Lebih longgar dari 5% karena panas | [K] |
| Cadence paruh 1 → paruh 2 | Waspada kalau turun 5 atau lebih | [K] tanda bentuk lari mulai rusak karena capek |
| Target cadence | Taofik 168–172, Reza 172–176. Naik maksimal sekitar 10% bertahap | [P] Heiderscheit 2011 (MSSE): cadence +5–10% mengurangi beban lutut dan pinggul |

**Rumus decoupling:**
- Ambil hanya record dengan HR di atas 80 dan kecepatan di atas 0,6 m/s.
- Bagi dua berdasarkan jumlah record (paruh 1 dan paruh 2).
- Rasio tiap paruh = kecepatan rata-rata ÷ HR rata-rata.
- Decoupling = (rasio paruh 1 − rasio paruh 2) ÷ rasio paruh 1 × 100%.
- Dilaporkan dua versi: data penuh, dan tanpa 3 km pertama. Yang dinilai versi tanpa 3 km pertama.
- **Hanya berlaku untuk lari dengan pace rata.** Tidak berlaku untuk tempo atau interval.

## 7. Tidur dan pemulihan (gerbang pagi)

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

Koreksi: sebelumnya saya menulis "turun sekitar 1/3". Yang benar: risiko cedera turun **menjadi** kurang dari 1/3, atau turun sekitar 2/3.

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
| Lomba 10K, 7 Nov 2026 | LTHR dan zona disamakan rumusnya, pace tempo dikunci |
| Half marathon, 23 Jan 2027 | Pace maraton dikunci |
| Tes 10K, 10 Apr 2027 | Evaluasi G3: decoupling di bawah 8% di long run ≥20 km |

---

### Yang perlu dibereskan (temuan saat menyusun dokumen ini)
1. Rumus zona Taofik dan Reza berbeda → samakan setelah 7 Nov.
2. Carbo loading 8–10 g/kg di Excel lebih rendah dari pedoman 10–12 g/kg → perlu diputuskan.
3. Isi gel dianggap 25 g, padahal GU 22 g → hitungan jumlah gel saat lomba bisa kurang 1–2.
4. Sheet Kamus Latihan masih menulis "pendinginan 1 km" untuk tempo, padahal di kalender sudah 1–3 km.

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
