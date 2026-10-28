# NewPaceLab — aturan untuk Claude

Dashboard marathon Taofik & Reza (lihat README.md). Bahasa UI: Indonesia, ringkas.

## Sumber rumus dan batas angka

- **`docs/RUMUS-BATAS-SUMBER.md` adalah acuan tunggal** untuk semua rumus, batas angka, dan teks saran.
  Setiap hitungan di `pacelab/metrics.py`, status warna dan saran di `pacelab/web/template.html`
  harus cocok dengan dokumen ini.
- Kalau dokumen dan kode berbeda, ikuti dokumen. Kalau dokumen tidak mengatur suatu angka,
  jangan mengarang diam-diam: tandai sebagai **[keputusan dashboard]** di README dan tanyakan ke omPik.
- Kalau dokumen diperbarui, cocokkan ulang kode dan README, lalu laporkan bedanya sebelum mengubah.

## Cara kerja dengan omPik

- Buat mockup dulu untuk perubahan tampilan; jangan eksekusi sebelum omPik bilang "gas".
- Sertakan bukti (screenshot) saat melapor. Beri opsi dan tanya bila ragu; jangan berasumsi.
- Jangan pernah mencetak atau commit key Garmin, `keys/`, `programs/*.xlsx`, `data/`, `.token_cache/`, `dist/`.
- Tes: `python -m unittest discover -s tests` (Python 3.8+ tanpa library tambahan).
