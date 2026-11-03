# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman C# (.NET 8/9 SDK & C# 12/13)

## 1. Tujuan
Menetapkan prosedur operasional baku bagi pengembang perangkat lunak dalam memasang .NET SDK modern (versi 8 LTS atau versi 9), mengonfigurasi command-line interface `dotnet`, serta menguji eksekusi fitur modern C# seperti *Top-Level Statements*, *Primary Constructors*, *Record Structs*, dan *Pattern Matching*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS (x64 / Apple Silicon ARM64), Windows 10/11 64-bit, atau Linux (Ubuntu, Debian, Fedora, RHEL).
2. Memiliki hak akses pengguna lokal untuk mengeksekusi biner .NET CLI.
3. Kapasitas ruang penyimpanan disk kosong minimal 2.5 GB.
4. Versi SDK resmi: **.NET 8.0 SDK (LTS)** atau **.NET 9.0 SDK** (Standard Term Support).
5. Toolchain resmi: `dotnet` CLI dan NuGet Package Manager.

## 3. Tahapan Proses

### Langkah 1: Pemasangan .NET SDK Resmi
- **macOS:**
  Gunakan Homebrew atau unduh installer resmi `.pkg` dari `dotnet.microsoft.com`:
  ```bash
  brew install --cask dotnet-sdk
  ```
- **Windows:**
  Gunakan Windows Package Manager (`winget`):
  ```powershell
  winget install Microsoft.DotNet.SDK.8
  ```
- **Linux (Ubuntu):**
  Tambahkan paket repositori resmi Microsoft:
  ```bash
  sudo apt-get update
  sudo apt-get install -y dotnet-sdk-8.0
  ```

### Langkah 2: Verifikasi Instalasi .NET SDK
Buka terminal dan jalankan perintah verifikasi:
```bash
dotnet --version
dotnet --info
```
Pastikan biner menampilkan versi `.NET 8.0.xxx` atau `9.0.xxx`.

### Langkah 3: Pembuatan Proyek Baru dengan .NET CLI
1. Buat folder proyek baru dan inisialisasi console app:
   ```bash
   dotnet new console -n MyCSharpApp
   cd MyCSharpApp
   ```
   Perintah ini akan membuat berkas proyek `MyCSharpApp.csproj` dan berkas kode `Program.cs`.

### Langkah 4: Pengujian Fitur Modern C# 12 (Primary Constructors & Records)
1. Perbarui berkas `Program.cs`:
   ```csharp
   // Uji C# Top-Level Statements & C# 12 Primary Constructors
   var app = new SystemService("CintaMamaAI C# Core", "8.0 / 9.0");
   app.PrintStatus();

   // Definisi record struct modern
   public readonly record struct SystemService(string Name, string RuntimeVersion)
   {
       public void PrintStatus()
       {
           Console.WriteLine($"Layanan: {Name}");
           Console.WriteLine($"Versi Runtime .NET: {RuntimeVersion}");
           Console.WriteLine("Status: Lingkungan C# (.NET SDK) berhasil diverifikasi dan siap digunakan.");
       }
   }
   ```
2. Jalankan aplikasi via .NET CLI:
   ```bash
   dotnet run
   ```
3. Bangun biner mandiri yang teroptimasi:
   ```bash
   dotnet build -c Release
   ```

## 4. Dokumen yang Diperlukan
1. Berkas proyek `MyCSharpApp.csproj`.
2. Berkas kode sumber `Program.cs`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `bin/` dan `obj/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.

