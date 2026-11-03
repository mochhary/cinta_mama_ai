# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Swift (Swift 5.10 / Swift 6 & SPM)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang toolchain resmi bahasa pemrograman Swift, mengonfigurasi Swift Package Manager (SPM), serta menguji eksekusi kode biner dengan standar fitur *strict concurrency*, *Actors*, dan *modern async/await*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi:
   - macOS (versi 13 Ventura, 14 Sonoma, atau yang lebih baru).
   - Linux (Ubuntu 20.04/22.04/24.04 atau Amazon Linux 2/2023).
   - Windows 10/11 64-bit (dengan Swift toolchain for Windows).
2. Kapasitas ruang penyimpanan disk kosong minimal 4.0 GB (khusus macOS membutuhkan alokasi Xcode Command Line Tools).
3. Versi compiler Swift resmi: **Swift 5.10** atau **Swift 6.0** (versi terkini).
4. Toolchain resmi: Swift Package Manager (`swift package`).

## 3. Tahapan Proses

### Langkah 1: Pemasangan Swift Toolchain Resmi
- **macOS:**
  Pasang Xcode Command Line Tools yang sudah memuat kompiler Swift resmi:
  ```bash
  xcode-select --install
  ```
- **Linux (Ubuntu):**
  Unduh arsip biner resmi dari `swift.org/download`, pasang dependensi sistem, dan tambahkan biner ke PATH:
  ```bash
  sudo apt-get update
  sudo apt-get install -y binutils git gnupg2 libc6-dev libcurl4-openssl-dev libedit2 libgcc-s1 libsqlite3-0 libstdc++-11-dev libxml2-dev pkg-config tzdata zlib1g-dev
  # Ekstrak biner swift dan ekspor PATH sesuai lokasi instalasi
  ```
- **Windows:**
  Gunakan installer resmi *Swift for Windows* dari `swift.org/download`.

### Langkah 2: Verifikasi Instalasi Swift
Buka terminal dan periksa versi:
```bash
swift --version
```
Pastikan terminal menampilkan output biner `Apple Swift version 5.10` atau `Swift version 6.x`.

### Langkah 3: Pembuatan Paket Biner dengan Swift Package Manager (SPM)
1. Buat direktori kerja proyek:
   ```bash
   mkdir my-swift-project
   cd my-swift-project
   ```
2. Inisialisasi struktur paket executable:
   ```bash
   swift package init --type executable
   ```
   Perintah ini akan secara otomatis membuat berkas manifest `Package.swift` dan struktur folder `Sources/`.

### Langkah 4: Pengujian Fitur Modern Swift (Async/Await & Actors)
1. Perbarui berkas `Sources/main.swift`:
   ```swift
   import Foundation

   // Uji Actor untuk thread-safe concurrency
   actor StatusTracker {
       private var messageCount = 0

       func record(message: String) -> String {
           messageCount += 1
           return "[\(messageCount)] \(message)"
       }
   }

   @main
   struct App {
       static func main() async {
           let tracker = StatusTracker()
           let status = await tracker.record(message: "Status: Lingkungan Swift modern berhasil diverifikasi.")
           print(status)
       }
   }
   ```
2. Jalankan aplikasi langsung melalui SPM:
   ```bash
   swift run
   ```
3. Bangun biner rilis teroptimasi:
   ```bash
   swift build -c release
   ```

## 4. Dokumen yang Diperlukan
1. Berkas manifest paket `Package.swift` dan `Package.resolved`.
2. Berkas kode sumber `Sources/main.swift`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `.build/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 25 menit.

