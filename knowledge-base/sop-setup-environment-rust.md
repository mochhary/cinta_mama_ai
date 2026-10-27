# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Rust (Rustup & Cargo)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang toolchain resmi bahasa pemrograman Rust melalui `rustup`, mengonfigurasi manajer paket dan build system `cargo`, serta menguji pembuatan biner terkompilasi dengan jaminan *memory safety* tanpa garbage collector.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau Linux.
2. Memiliki C compiler biner lokal yang aktif (Xcode Command Line Tools pada macOS, Visual Studio C++ Build Tools pada Windows, atau `gcc`/`clang` pada Linux).
3. Kapasitas ruang penyimpanan disk kosong minimal 2.0 GB.
4. Versi Rust resmi: **Rust 1.80 atau yang lebih baru** (kanal stabil).
5. Tool installer resmi wajib: `rustup` (Rust toolchain installer resmi).

## 3. Tahapan Proses

### Langkah 1: Instalasi Rust Toolchain via Rustup
- **macOS / Linux:** Jalankan script instalasi resmi `rustup` melalui terminal:
  ```bash
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  source "$HOME/.cargo/env"
  ```
- **Windows:**
  Unduh dan jalankan installer `rustup-init.exe` dari portal resmi `rust-lang.org`. Pastikan opsi *C++ Build Tools* telah terpasang saat diminta.

### Langkah 2: Verifikasi Instalasi Compiler dan Cargo
Periksa ketersediaan toolchain Rust:
```bash
rustc --version
cargo --version
rustup --version
```
Pastikan `rustc` menampilkan versi `1.80.0` atau yang lebih mutakhir.

### Langkah 3: Pembuatan Proyek Baru dengan Cargo
Gunakan Cargo untuk membuat struktur proyek biner standar:
```bash
cargo new my-rust-project --bin
cd my-rust-project
```
Cargo akan secara otomatis membuat berkas manifest `Cargo.toml`, direktori `src/`, berkas `src/main.rs`, serta konfigurasi `.gitignore`.

### Langkah 4: Pengujian Eksekusi Kode Rust Modern
1. Buka berkas `src/main.rs` dan perbarui dengan kode pengujian:
   ```rust
   fn main() {
       let language = "Rust";
       let edition = "2021/2024";

       // Uji ownership dan format string
       let message = format!("Status: Lingkungan {} (Edition {}) berhasil diverifikasi.", language, edition);
       println!("{}", message);

       // Uji pattern matching
       let check_val = Some(42);
       if let Some(val) = check_val {
           println!("Nilai terverifikasi: {}", val);
       }
   }
   ```
2. Jalankan pengecekan tipe dan kompilasi cepat tanpa membuat biner rilis:
   ```bash
   cargo check
   ```
3. Kompilasi dan eksekusi proyek:
   ```bash
   cargo run
   ```
4. Bangun biner teroptimasi untuk lingkungan produksi:
   ```bash
   cargo build --release
   ```

## 4. Dokumen yang Diperlukan
1. Berkas manifest dependensi `Cargo.toml` dan `Cargo.lock`.
2. Berkas kode sumber `src/main.rs`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `target/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 25 menit.

