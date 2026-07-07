# IntraNEW PDF Validator

Aplikasi validasi lokal berbasis **Next.js + React + TypeScript** untuk membaca PDF laporan produksi SIINas/IntraNEW yang diunggah validator, lalu memberi penilaian kewajaran per bagian sampai **Pengelolaan Limbah Cair**. Bagian setelah itu, termasuk INDI 4.0 dan catatan lain di bawahnya, sengaja diabaikan sesuai kebutuhan validasi saat ini.

PDF diproses di browser menggunakan `pdfjs-dist`. Aplikasi tidak meminta username/password, tidak membuka sesi IntraNEW, dan tidak mengirim data laporan ke API eksternal.

## Fitur

- Upload PDF laporan produksi dan PDF batas kewajaran harga per KBLI.
- Ekstraksi teks PDF di sisi browser.
- Parsing bagian laporan: identitas, data umum, persediaan, kapasitas, produksi dan penjualan, bahan baku, bahan penolong, investasi, tenaga kerja, prakerin, air, energi, pengeluaran, rencana produksi, mesin, limbah padat, limbah B3, dan limbah cair.
- Validasi rule-based per bagian dengan severity `LOW`, `MEDIUM`, `HIGH`, dan `CRITICAL`.
- Perbandingan harga rata-rata per kg terhadap batas kewajaran KBLI dari PDF referensi.
- Risk score 0-100, rekomendasi keseluruhan, ringkasan temuan per bagian, dan catatan validator siap ditempel.
- Export hasil validasi ke file HTML.

## Install

```powershell
cd "C:\Users\Admin\Documents\Project Validasi\intranew-validator"
pnpm install
```

Jika `pnpm` belum ada di PATH, gunakan Node.js/pnpm yang tersedia di runtime Codex atau install Node.js LTS lalu aktifkan Corepack:

```powershell
corepack enable
corepack prepare pnpm@latest --activate
```

## Menjalankan Lokal

```powershell
pnpm dev
```

Buka `http://127.0.0.1:3000`.

Cara pakai:

1. Upload PDF laporan produksi.
2. Upload PDF batas kewajaran harga per KBLI.
3. Hasil analisis otomatis muncul setelah file terbaca.
4. Baca ringkasan, temuan per bagian, dan catatan validator.
5. Klik ikon export pada panel `Catatan Validator` bila perlu menyimpan HTML report.

## Testing

```powershell
pnpm test
pnpm typecheck
pnpm build
```

Test memakai fixture teks kecil, bukan file PDF perusahaan mentah, agar validasi parser dan rules tetap bisa dijalankan tanpa data sensitif.

## Deploy ke Vercel

Project ini siap sebagai aplikasi Next.js standar.

```powershell
pnpm build
```

Di Vercel:

- Framework preset: `Next.js`
- Build command: `pnpm build`
- Install command: `pnpm install`
- Output directory: biarkan default

Catatan privasi: parsing PDF saat ini berjalan di browser pengguna. Jangan menambahkan upload ke API eksternal kecuali ada persetujuan dan kebijakan keamanan data yang jelas.

## Struktur Penting

- `app/` - halaman Next.js.
- `components/ValidatorApp.tsx` - UI upload, validasi, ringkasan, tabel temuan, dan export.
- `lib/pdfText.ts` - ekstraksi teks PDF menggunakan PDF.js.
- `lib/reportParser.ts` - parser bagian laporan sampai Pengelolaan Limbah Cair.
- `lib/priceLimits.ts` - parser batas kewajaran harga per KBLI.
- `lib/validator.ts` - rules engine dan risk score.
- `tests/` - unit test parser dan validasi.

## Troubleshooting

Jika PDF tidak terbaca, cek apakah file hasil scan gambar. Versi awal ini membaca teks PDF digital, bukan OCR.

Jika bagian tertentu kosong, struktur PDF kemungkinan berbeda. Aplikasi tetap menampilkan warning parser agar pola section di `lib/reportParser.ts` bisa disesuaikan.

Jika batas harga KBLI tidak masuk, pastikan PDF referensi memiliki baris KBLI dengan pola kode 5 digit dan rentang harga numerik.
