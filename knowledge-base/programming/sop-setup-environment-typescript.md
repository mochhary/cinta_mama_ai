# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman TypeScript (TypeScript 5.x & Node.js 20/22 LTS)

## 1. Tujuan
Menetapkan prosedur baku bagi pengembang perangkat lunak dalam mengonfigurasi runtime JavaScript (Node.js LTS), menginstalasi TypeScript compiler (`tsc`), serta mengatur konfigurasi `tsconfig.json` modern agar proses pengembangan aplikasi berbasis TypeScript berjalan dengan *strict type safety*, performa optimal, dan terhindar dari konflik dependensi.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 (64-bit), atau distribusi Linux.
2. Memiliki hak akses pengguna lokal untuk mengeksekusi Node.js dan memasang modul paket NPM.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Tersedia runtime **Node.js versi 20 LTS atau 22 LTS** (Active LTS) beserta manajer paket `npm` versi 10+.
5. Koneksi internet aktif untuk mengunduh pustaka dari npm registry resmi (`registry.npmjs.org`).
6. **Kebijakan Isolasi Proyek Wajib:** Sangat dianjurkan menginstal compiler TypeScript secara lokal per proyek (`npm install -D typescript`) dibandingkan instalasi global guna menjamin konsistensi versi compiler antar anggota tim.

## 3. Tahapan Proses

### Langkah 1: Pemeriksaan Node.js & NPM
Buka terminal dan pastikan Node.js serta NPM sudah terpasang dengan versi yang sesuai:
```bash
node -v
npm -v
```
Pastikan output versi Node.js minimal `v20.x.x` atau `v22.x.x`. Jika belum terpasang, gunakan nvm (*Node Version Manager*) atau unduh installer resmi dari `nodejs.org`.

### Langkah 2: Inisialisasi Proyek Node.js
Buat direktori proyek baru dan inisialisasi file manifest `package.json`:
```bash
mkdir my-ts-project
cd my-ts-project
npm init -y
```

### Langkah 3: Instalasi TypeScript dan Tooling Eksekusi
Pasang TypeScript 5.x compiler, definitions Node.js, serta runtime runner cepat (`tsx` atau `ts-node`):
```bash
npm install -D typescript @types/node tsx
```

### Langkah 4: Pembuatan Konfigurasi TypeScript (tsconfig.json)
Jalankan inisialisasi konfigurasi dasar atau buat berkas `tsconfig.json` dengan konfigurasi modern:
```bash
npx tsc --init
```
Pastikan pengaturan utama di dalam `tsconfig.json` mengaktifkan fitur strict dan resolusi modul modern:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src/**/*"]
}
```

### Langkah 5: Konfigurasi Git Ignore (.gitignore)
Tambahkan entri build artifacts dan `node_modules` ke dalam `.gitignore`:
```bash
echo "node_modules/" >> .gitignore
echo "dist/" >> .gitignore
echo "*.tsbuildinfo" >> .gitignore
```

### Langkah 6: Pembuatan dan Pengujian Skrip TypeScript
1. Buat folder `src/` dan file uji `src/verify_setup.ts`:
   ```bash
   mkdir src
   ```
2. Isi file `src/verify_setup.ts`:
   ```typescript
   interface EnvironmentCheck {
     language: string;
     version: string;
     status: "READY" | "ERROR";
   }

   const check: EnvironmentCheck = {
     language: "TypeScript",
     version: "5.x",
     status: "READY"
   };

   console.log(`Status: ${check.language} ${check.version} lingkungan terverifikasi (${check.status}).`);
   ```
3. Eksekusi pengujian langsung tanpa kompilasi manual:
   ```bash
   npx tsx src/verify_setup.ts
   ```
4. Atau uji kompilasi ke JavaScript biner:
   ```bash
   npx tsc
   node dist/verify_setup.js
   ```

## 4. Dokumen yang Diperlukan
1. Berkas manifest `package.json` dan `package-lock.json`.
2. Berkas konfigurasi kompilasi `tsconfig.json`.
3. Berkas pengabaian versi `.gitignore`.
4. Berkas pengujian kode sumber `src/verify_setup.ts`.

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 15 menit.

