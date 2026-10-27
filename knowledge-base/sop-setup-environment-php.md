# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman PHP (PHP 8.2 / 8.3 / 8.4 & Composer)

## 1. Tujuan
Menetapkan prosedur operasional baku bagi pengembang perangkat lunak dalam memasang runtime PHP modern (versi 8.2, 8.3, atau 8.4), mengaktifkan ekstensi wajib, memasang manajer dependensi Composer, serta menguji fitur OOP dan sintaks modern PHP.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau distribusi Linux (Ubuntu 22.04+, Debian 12+).
2. Memiliki hak akses administrator atau `sudo` untuk memasang paket sistem.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.0 GB.
4. Versi PHP resmi: **PHP 8.2 atau yang lebih baru** (PHP 8.3 / 8.4 disarankan).
5. Manajer dependensi resmi: **Composer versi 2.6+**.
6. Ekstensi wajib: `openssl`, `mbstring`, `pdo`, `tokenizer`, `xml`, `ctype`, dan `curl`.

## 3. Tahapan Proses

### Langkah 1: Pemasangan PHP Modern
- **macOS:** Gunakan Homebrew:
  ```bash
  brew install php@8.3
  brew link --force --overwrite php@8.3
  ```
- **Linux (Ubuntu/Debian):** Gunakan PPA Ondrej Sury untuk versi PHP mutakhir:
  ```bash
  sudo apt-get update
  sudo apt-get install -y software-properties-common
  sudo add-apt-repository -y ppa:ondrej/php
  sudo apt-get update
  sudo apt-get install -y php8.3 php8.3-cli php8.3-common php8.3-curl php8.3-mbstring php8.3-xml php8.3-zip
  ```
- **Windows:** Pasang via Windows Package Manager:
  ```powershell
  winget install PHP.PHP.8.3
  ```
  Atau gunakan distribusi terkelola seperti ServBay, XAMPP versi terbaru, atau zip biner resmi dari `windows.php.net`.

### Langkah 2: Pemasangan Manajer Paket Composer
Pasang Composer secara global melalui terminal:
```bash
php -r "copy('https://getcomposer.org/installer', 'composer-setup.php');"
php composer-setup.php --install-dir=/usr/local/bin --filename=composer
php -r "unlink('composer-setup.php');"
```
*(Pada Windows, unduh installer `Composer-Setup.exe` dari `getcomposer.org`).*

### Langkah 3: Verifikasi Instalasi PHP dan Composer
Buka terminal dan periksa versi:
```bash
php -v
composer -V
```
Pastikan PHP menampilkan versi minimal `8.2.x` atau `8.3.x`.

### Langkah 4: Inisialisasi Proyek dan Pengujian Sintaks Modern PHP
1. Buat folder proyek dan inisialisasi:
   ```bash
   mkdir my-php-project
   cd my-php-project
   composer init --no-interaction
   ```
2. Buat berkas uji `verify_setup.php` untuk memvalidasi fitur modern (Readonly Class, Match Expression, dan Enums):
   ```php
   <?php
   // Uji Enum bawaan PHP 8.1+
   enum EnvironmentStatus: string {
       case Ready = "READY";
       case Failed = "FAILED";
   }

   // Uji Readonly Class PHP 8.2+
   readonly class SystemChecker {
       public function __construct(
           public string $phpVersion,
           public EnvironmentStatus $status
       ) {}

       public function evaluate(): string {
           return match($this->status) {
               EnvironmentStatus::Ready => "Sukses: PHP {$this->phpVersion} siap digunakan.",
               EnvironmentStatus::Failed => "Galat: Konfigurasi PHP bermasalah."
           };
       }
   }

   $checker = new SystemChecker(phpversion(), EnvironmentStatus::Ready);
   echo $checker->evaluate() . PHP_EOL;
   ```
3. Eksekusi skrip melalui terminal:
   ```bash
   php verify_setup.php
   ```

## 4. Dokumen yang Diperlukan
1. Berkas konfigurasi dependensi `composer.json` dan `composer.lock`.
2. Berkas kode sumber uji `verify_setup.php`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `vendor/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.

