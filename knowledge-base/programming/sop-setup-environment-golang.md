# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Go (Golang 1.22 / 1.23)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang compiler Go (Golang), mengonfigurasi variabel lingkungan sistem (`GOPATH`, `GOBIN`, `PATH`), serta menginisialisasi sistem dependensi berbasis Go Modules (`go.mod`) dan Multi-module Workspaces (`go.work`) untuk menjamin proses kompilasi cepat dan performa tinggi.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau distribusi Linux (64-bit / ARM64).
2. Memiliki hak akses pengguna atau administrator untuk meletakkan biner sistem.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Versi toolchain resmi: **Go versi 1.22** atau **Go 1.23** (versi terkini).
5. Koneksi internet aktif untuk mengunduh modul paket dari Go Module Mirror (`proxy.golang.org`).

## 3. Tahapan Proses

### Langkah 1: Instalasi Go Toolchain Resmi
- **macOS:** Pasang via Homebrew:
  ```bash
  brew install go
  ```
  Atau unduh installer `.pkg` dari portal resmi `go.dev/dl`.
- **Linux (Ubuntu/Debian):**
  Unduh arsip tarball resmi, ekstrak ke `/usr/local`, lalu bersihkan cache:
  ```bash
  wget https://go.dev/dl/go1.23.0.linux-amd64.tar.gz
  sudo rm -rf /usr/local/go && sudo tar -C /usr/local -xzf go1.23.0.linux-amd64.tar.gz
  ```
- **Windows:** Pasang via `winget`:
  ```powershell
  winget install GoLang.Go
  ```
  Atau unduh file installer `.msi` dari `go.dev/dl`.

### Langkah 2: Konfigurasi Environment Variables (PATH & GOPATH)
- **macOS / Linux:** Tambahkan baris berikut ke `~/.zshrc` atau `~/.bashrc`:
  ```bash
  echo 'export PATH=$PATH:/usr/local/go/bin:$(go env GOPATH)/bin' >> ~/.zshrc
  source ~/.zshrc
  ```
- **Windows:** Pastikan path `C:\Program Files\Go\bin` dan `%USERPROFILE%\go\bin` telah ditambahkan ke variabel `Path` pengguna.

### Langkah 3: Verifikasi Instalasi Go
Jalankan perintah verifikasi pada terminal:
```bash
go version
go env GOPATH
```
Pastikan versi yang tampil menunjukkan minimal `go1.22.x` atau `go1.23.x`.

### Langkah 4: Inisialisasi Proyek dan Go Modules
1. Buat direktori kerja proyek:
   ```bash
   mkdir my-go-project
   cd my-go-project
   ```
2. Inisialisasi Go Module baru:
   ```bash
   go mod init example.com/my-go-project
   ```
   Perintah ini akan membuat berkas `go.mod` yang mencatat modul dan versi Go.

### Langkah 5: Pengujian Eksekusi Kode Go Modern (Range over Integer & Slices)
1. Buat berkas `main.go`:
   ```go
   package main

   import (
       "fmt"
       "runtime"
   )

   func main() {
       fmt.Printf("Versi Go Runtime: %s\n", runtime.Version())
       fmt.Printf("Sistem Operasi/Arsitektur: %s/%s\n", runtime.GOOS, runtime.GOARCH)

       // Fitur baru Go 1.22: Range over integer
       fmt.Print("Tes Range over Integer (Go 1.22+): ")
       for i := range 3 {
           fmt.Printf("%d ", i)
       }
       fmt.Println("\nStatus: Lingkungan Golang terverifikasi dan siap pakai.")
   }
   ```
2. Jalankan program secara langsung:
   ```bash
   go run main.go
   ```
3. Kompilasi menjadi biner mandiri yang dapat didistribusikan:
   ```bash
   go build -o app
   ./app
   ```

## 4. Dokumen yang Diperlukan
1. Berkas modul `go.mod` dan `go.sum`.
2. Berkas kode sumber `main.go`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan biner hasil build).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.

