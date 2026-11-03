# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Ruby (Ruby 3.2 / 3.3 & Bundler)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang runtime Ruby modern (versi 3.2 / 3.3) menggunakan manajer versi (`rbenv`), mengonfigurasi manajer paket `gem` dan `bundler`, mengaktifkan akselerator kompilasi YJIT, serta menguji fitur-fitur modern seperti `Data.define` dan *pattern matching*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau Linux.
2. Memiliki hak akses pengguna lokal terminal.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Versi Ruby resmi: **Ruby 3.2 atau Ruby 3.3** (versi stabil modern).
5. Toolchain resmi: `gem` dan `bundler`.
6. Disarankan menggunakan tool pengelola versi seperti `rbenv` untuk mencegah konflik dengan Ruby sistem bawaan.

## 3. Tahapan Proses

### Langkah 1: Pemasangan Ruby via Rbenv
- **macOS:**
  Gunakan Homebrew untuk memasang `rbenv` dan `ruby-build`:
  ```bash
  brew install rbenv ruby-build
  rbenv init
  rbenv install 3.3.0
  rbenv global 3.3.0
  ```
- **Linux (Ubuntu/Debian):**
  Pasang dependensi kompilasi lalu pasang `rbenv`:
  ```bash
  sudo apt-get update
  sudo apt-get install -y git curl libssl-dev libreadline-dev zlib1g-dev autoconf bison build-essential libyaml-dev
  git clone https://github.com/rbenv/rbenv.git ~/.rbenv
  git clone https://github.com/rbenv/ruby-build.git ~/.rbenv/plugins/ruby-build
  echo 'export PATH="$HOME/.rbenv/bin:$PATH"' >> ~/.bashrc
  echo 'eval "$(rbenv init -)"' >> ~/.bashrc
  source ~/.bashrc
  rbenv install 3.3.0
  rbenv global 3.3.0
  ```
- **Windows:**
  Gunakan installer resmi *RubyInstaller for Windows* (versi with Devkit) dari `rubyinstaller.org`.

### Langkah 2: Verifikasi Instalasi Ruby dan Bundler
Buka terminal dan periksa versi:
```bash
ruby -v
gem -v
bundle -v
```
Pastikan Ruby menunjukkan versi `ruby 3.2.x` atau `ruby 3.3.x`.

### Langkah 3: Inisialisasi Proyek dan Bundler
1. Buat folder proyek baru:
   ```bash
   mkdir my-ruby-project
   cd my-ruby-project
   ```
2. Buat berkas `Gemfile`:
   ```bash
   bundle init
   ```

### Langkah 4: Pengujian Fitur Modern Ruby (Data.define & Pattern Matching)
1. Buat berkas uji `verify_setup.rb`:
   ```ruby
   # Uji fitur Ruby 3.2+ Data class (immutable value object)
   SystemReport = Data.define(:language, :version, :status)

   report = SystemReport.new(language: "Ruby", version: RUBY_VERSION, status: :ready)

   # Uji Ruby Pattern Matching
   case report
   in SystemReport(language:, version:, status: :ready)
     puts "Status: #{language} #{version} terverifikasi dan siap pakai (YJIT didukung)."
   else
     puts "Status: Konfigurasi bermasalah."
   end
   ```
2. Jalankan skrip via interpreter Ruby (dengan opsi YJIT):
   ```bash
   ruby --yjit verify_setup.rb
   ```
3. Pastikan teks status terverifikasi tercetak dengan benar di terminal.

## 4. Dokumen yang Diperlukan
1. Berkas manifest dependensi `Gemfile` dan `Gemfile.lock`.
2. Berkas kode sumber `verify_setup.rb`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `.bundle/` dan `vendor/bundle`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 25 menit.

