# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Java (JDK 21 LTS)

## 1. Tujuan
Memberikan panduan operasional baku bagi pengembang perangkat lunak dalam mengunduh, memasang (instalasi), serta mengonfigurasi lingkungan runtime dan compiler Java Development Kit (JDK 21 LTS) agar proses kompilasi dan eksekusi program Java berjalan terstandarisasi, stabil, dan siap pakai.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi yang didukung resmi:
   - macOS (versi 11 Big Sur atau yang lebih baru, arsitektur x64 atau Apple Silicon ARM64).
   - Windows (Windows 10 atau 11, versi 64-bit).
   - Linux (distribusi Ubuntu 20.04+, Debian 11+, RHEL/CentOS 8+, atau Fedora).
2. Memiliki hak akses pengguna tingkat tinggi (Administrator pada Windows atau hak akses `sudo` pada macOS/Linux).
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Memori RAM sistem minimal 4 GB (disarankan 8 GB atau lebih).
5. Koneksi jaringan internet aktif dan stabil untuk mengunduh arsip biner JDK resmi.
6. Menggunakan distribusi biner resmi OpenJDK rilis Long Term Support (LTS), dengan standar minimal **Eclipse Temurin JDK 21 LTS** dari Adoptium.

## 3. Tahapan Proses

### Langkah 1: Pengunduhan Paket Biner JDK 21 Resmi
- **macOS:**
  Gunakan Homebrew pada terminal:
  ```bash
  brew install --cask temurin@21
  ```
  Atau unduh berkas installer `.pkg` langsung dari portal resmi Adoptium (https://adoptium.net).
- **Windows:**
  Gunakan Windows Package Manager (winget) pada PowerShell:
  ```powershell
  winget install EclipseAdoptium.Temurin.21.JDK
  ```
  Atau unduh installer berkas `.msi` 64-bit dari portal resmi Adoptium.
- **Linux (Ubuntu/Debian):**
  Tambahkan repositori resmi Adoptium lalu pasang melalui APT:
  ```bash
  sudo apt-get update
  sudo apt-get install -y wget apt-transport-https gpg
  wget -qO - https://packages.adoptium.net/artifactory/api/gpg/key/public | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/adoptium.gpg > /dev/null
  echo "deb https://packages.adoptium.net/artifactory/deb $(awk -F= '/^VERSION_CODENAME/{print$2}' /etc/os-release) main" | sudo tee /etc/apt/sources.list.d/adoptium.list
  sudo apt-get update
  sudo apt-get install -y temurin-21-jdk
  ```

### Langkah 2: Konfigurasi Environment Variables (JAVA_HOME & PATH)
- **macOS (zsh / ~/.zshrc):**
  Buka terminal dan tambahkan konfigurasi variabel ke berkas `~/.zshrc`:
  ```bash
  echo 'export JAVA_HOME=$(/usr/libexec/java_home -v 21)' >> ~/.zshrc
  echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.zshrc
  source ~/.zshrc
  ```
- **Linux (bash / ~/.bashrc):**
  Tambahkan baris berikut ke dalam berkas `~/.bashrc`:
  ```bash
  echo 'export JAVA_HOME=/usr/lib/jvm/temurin-21-jdk' >> ~/.bashrc
  echo 'export PATH=$JAVA_HOME/bin:$PATH' >> ~/.bashrc
  source ~/.bashrc
  ```
- **Windows:**
  Buka *System Properties* > *Environment Variables*:
  1. Pada bagian *System Variables*, klik **New**, buat variabel `JAVA_HOME` dengan nilai path instalasi (contoh: `C:\Program Files\Eclipse Adoptium\jdk-21.x.x-hotspot\`).
  2. Pilih variabel `Path`, klik **Edit**, tambahkan entri baru: `%JAVA_HOME%\bin`.
  3. Simpan perubahan dan buka kembali Command Prompt / PowerShell baru.

### Langkah 3: Verifikasi Instalasi Compiler dan Runtime
Buka terminal atau command prompt baru, kemudian jalankan dua perintah verifikasi berikut:
```bash
java --version
javac --version
```
Pastikan terminal menampilkan output biner OpenJDK versi 21 (LTS) dari Temurin/Adoptium.

### Langkah 4: Pengujian Eksekusi Kode Sumber Sederhana
1. Buat berkas baru bernama `VerifySetup.java` dengan kode pengujian:
   ```java
   public class VerifySetup {
       public static void main(String[] args) {
           System.out.println("Status: Lingkungan Java 21 LTS terverifikasi dan siap digunakan.");
       }
   }
   ```
2. Jalankan berkas menggunakan fitur *Single-File Source-Code Launcher* (tanpa membuat berkas class manual):
   ```bash
   java VerifySetup.java
   ```
3. Pastikan teks konfirmasi berhasil tercetak pada jendela terminal tanpa galat.

## 4. Dokumen yang Diperlukan
1. Berkas biner installer atau paket JDK 21 resmi (`.pkg`, `.msi`, atau paket `.deb`).
2. Berkas konfigurasi shell profil pengguna (`~/.zshrc`, `~/.bashrc`, atau berkas konfigurasi *System Environment Variables*).
3. Berkas kode sumber uji coba verifikasi (`VerifySetup.java`).
4. Catatan atau tangkapan layar output perintah `java --version` sebagai dokumentasi kepatuhan setup.

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 25 menit.
  - Pengunduhan paket JDK: 5 - 10 menit (tergantung kecepatan bandwidth).
  - Pemasangan biner & konfigurasi variabel lingkungan: 5 - 10 menit.
  - Validasi dan pengujian eksekusi: 3 - 5 menit.
