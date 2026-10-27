# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Dart (Dart 3.x & Pub)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang Dart SDK resmi (versi 3.x), mengonfigurasi variabel lingkungan, serta menguji eksekusi fitur modern seperti *Sound Null Safety*, *Records*, *Pattern Matching*, dan *Class Modifiers*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau distribusi Linux.
2. Memiliki hak akses pengguna lokal untuk mengeksekusi biner Dart SDK.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Versi Dart SDK resmi: **Dart versi 3.0 atau yang lebih baru** (Dart 3.4 / 3.5 disarankan).
5. Toolchain resmi: `dart` CLI dan manajer paket `dart pub`.

## 3. Tahapan Proses

### Langkah 1: Pemasangan Dart SDK Resmi
- **macOS:** Gunakan Homebrew:
  ```bash
  brew tap dart-lang/dart
  brew install dart
  ```
- **Linux (Ubuntu/Debian):** Tambahkan repositori resmi Google Dart:
  ```bash
  sudo apt-get update
  sudo apt-get install -y apt-transport-https
  wget -qO- https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo gpg --dearmor -o /usr/share/keyrings/dart.gpg
  echo 'deb [signed-by=/usr/share/keyrings/dart.gpg arch=amd64] https://storage.googleapis.com/download.dartlang.org/linux/debian stable main' | sudo tee /etc/apt/sources.list.d/dart_stable.list
  sudo apt-get update
  sudo apt-get install -y dart
  ```
- **Windows:** Pasang via `winget` atau Chocolatey:
  ```powershell
  winget install Dart-Lang.Dart-SDK
  ```

### Langkah 2: Verifikasi Instalasi Dart SDK
Buka terminal dan periksa versi:
```bash
dart --version
```
Pastikan terminal menampilkan versi `Dart SDK version: 3.x.x`.

### Langkah 3: Pembuatan Proyek Dart Baru
1. Buat direktori dan inisialisasi aplikasi command-line:
   ```bash
   dart create -t console my_dart_project
   cd my_dart_project
   ```
   Perintah ini akan membuat berkas manifest `pubspec.yaml`, folder `bin/`, dan `lib/`.

### Langkah 4: Pengujian Fitur Modern Dart 3 (Records & Patterns)
1. Buka berkas `bin/my_dart_project.dart` dan perbarui kode pengujian:
   ```dart
   // Uji Dart 3 Records dengan positional & named parameters
   (String, {int code, bool active}) getSystemStatus() {
     return ("Lingkungan Dart 3.x terverifikasi", code: 200, active: true);
   }

   void main() {
     // Uji Dart 3 Pattern Matching & Destructuring
     var (message, code: statusCode, active: isRunning) = getSystemStatus();

     print('Pesan: $message');
     print('Kode Respon: $statusCode (Aktif: $isRunning)');

     // Uji switch expression dengan pattern matching
     var label = switch (statusCode) {
       200 => "Status: Sukses dan siap digunakan.",
       _ => "Status: Terjadi kesalahan."
     };
     print(label);
   }
   ```
2. Jalankan aplikasi via Dart runtime:
   ```bash
   dart run
   ```
3. Uji kompilasi ke biner mandiri AOT (*Ahead-of-Time*):
   ```bash
   dart compile exe bin/my_dart_project.dart -o app_dart
   ./app_dart
   ```

## 4. Dokumen yang Diperlukan
1. Berkas manifest dependensi `pubspec.yaml` dan `pubspec.lock`.
2. Berkas kode sumber `bin/my_dart_project.dart`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `.dart_tool/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 15 menit.

