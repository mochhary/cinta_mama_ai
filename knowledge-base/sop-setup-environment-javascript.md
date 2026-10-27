# Standar Operasional Prosedur (SOP): Setup dan Standarisasi Lingkungan JavaScript (Node.js 20/22 LTS & Modern ESM)

## 1. Tujuan
Memberikan panduan operasional baku bagi pengembang perangkat lunak dalam memasang, mengonfigurasi, dan menstandarisasi runtime JavaScript modern (Node.js 20/22 Active LTS) dengan standar modul ECMAScript (ESM), package manager modern, serta tool linting dan testing bawaan.

## 2. Syarat Umum
1. Komputer bersistem operasi macOS (Apple Silicon / Intel), Windows 10/11 64-bit, atau distribusi Linux (Ubuntu 20.04+, Debian 11+).
2. Memiliki hak akses pengguna lokal terminal.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.0 GB.
4. Versi runtime resmi: **Node.js 20 LTS** atau **Node.js 22 LTS**.
5. Manajer paket resmi: `npm` versi 10+ atau manajer paket modern alternatif (`pnpm` disarankan untuk efisiensi ruang disk).
6. **Kebijakan Modul:** Proyek baru wajib menggunakan standar modul ECMAScript modern (`"type": "module"` di `package.json`) menggantikan format legacy CommonJS (`require()`).

## 3. Tahapan Proses

### Langkah 1: Instalasi Node.js LTS
- **macOS / Linux:** Gunakan `nvm` (Node Version Manager):
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  source ~/.zshrc # atau source ~/.bashrc
  nvm install --lts
  nvm use --lts
  ```
- **Windows:** Pasang via `winget` atau installer resmi dari `nodejs.org`:
  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```

### Langkah 2: Verifikasi Instalasi Node.js dan NPM
Periksa versi biner pada terminal:
```bash
node --version
npm --version
```
Pastikan node menunjukkan `v20.x.x` atau `v22.x.x`.

### Langkah 3: Inisialisasi Proyek Modern ESM
1. Buat folder proyek:
   ```bash
   mkdir modern-js-project
   cd modern-js-project
   ```
2. Buat `package.json` dan tambahkan flag ESM:
   ```bash
   npm init -y
   npm pkg set type="module"
   ```

### Langkah 4: Konfigurasi Git Ignore (.gitignore)
```bash
echo "node_modules/" >> .gitignore
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo "*.log" >> .gitignore
```

### Langkah 5: Pengujian Eksekusi Kode JavaScript Modern (ES2023/ES2024)
1. Buat berkas uji `index.js`:
   ```javascript
   // Menguji fitur ES2023/ES2024: Object.groupBy dan Array.toSorted()
   const items = [
     { name: "Node.js", category: "Runtime", year: 2009 },
     { name: "FastAPI", category: "Backend", year: 2018 },
     { name: "Ollama", category: "AI", year: 2023 }
   ];

   const sortedItems = items.toSorted((a, b) => a.year - b.year);
   const grouped = Object.groupBy(sortedItems, item => item.category);

   console.log("Status: Runtime JavaScript ES2023/ES2024 terverifikasi.");
   console.log("Kategori:", Object.keys(grouped).join(", "));
   ```
2. Jalankan skrip via Node.js:
   ```bash
   node index.js
   ```
3. Pastikan teks konfirmasi dan hasil pengelompokan tercetak sukses di terminal.

## 4. Dokumen yang Diperlukan
1. Berkas konfigurasi `package.json`.
2. Berkas kode sumber uji `index.js`.
3. Berkas pengabaian version control `.gitignore`.

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 15 menit.

