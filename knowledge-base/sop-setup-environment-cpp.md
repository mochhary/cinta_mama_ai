# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman C++ (Modern C++20 / C++23 & CMake)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang compiler C++ modern yang mendukung standar C++20 / C++23 (Clang, GCC, atau MSVC), mengonfigurasi generator build system CMake, serta menguji eksekusi fitur modern seperti *Concepts*, *Ranges*, dan *Smart Pointers*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau Linux.
2. Memiliki hak akses administrator / `sudo`.
3. Kapasitas ruang penyimpanan disk kosong minimal 3.0 GB.
4. Compiler C++ resmi yang mendukung standar minimal **C++20**:
   - macOS: Apple Clang versi 14+ (termasuk dalam Xcode Command Line Tools).
   - Linux: GCC versi 11+ atau Clang versi 14+.
   - Windows: Visual Studio 2022 C++ Build Tools (MSVC v143+) atau LLVM Clang.
5. Build System generator: **CMake versi 3.20+** dan build tool **Ninja** atau **Make**.

## 3. Tahapan Proses

### Langkah 1: Pemasangan Compiler C++ dan CMake
- **macOS:**
  Pasang Xcode Command Line Tools dan CMake:
  ```bash
  xcode-select --install
  brew install cmake ninja
  ```
- **Linux (Ubuntu/Debian):**
  Pasang compiler GCC modern dan CMake:
  ```bash
  sudo apt-get update
  sudo apt-get install -y build-essential g++ cmake ninja-build
  ```
- **Windows:**
  Pasang Visual Studio Build Tools atau LLVM Clang via `winget`:
  ```powershell
  winget install Kitware.CMake
  winget install LLVM.LLVM
  ```

### Langkah 2: Verifikasi Versi Compiler & CMake
Buka terminal dan periksa ketersediaan toolchain:
```bash
g++ --version # atau clang++ --version
cmake --version
```
Pastikan compiler mendukung flag standar `-std=c++20` atau `-std=c++23`.

### Langkah 3: Pembuatan Struktur Proyek CMake
1. Buat direktori kerja proyek:
   ```bash
   mkdir modern-cpp-project
   cd modern-cpp-project
   ```
2. Buat berkas konfigurasi `CMakeLists.txt`:
   ```cmake
   cmake_minimum_required(VERSION 3.20)
   project(ModernCppProject LANGUAGES CXX)

   set(CMAKE_CXX_STANDARD 20)
   set(CMAKE_CXX_STANDARD_REQUIRED ON)
   set(CMAKE_CXX_EXTENSIONS OFF)

   add_executable(app src/main.cpp)
   ```

### Langkah 4: Pengujian Fitur Modern C++20 (Concepts & Smart Pointers)
1. Buat direktori `src/` dan file `src/main.cpp`:
   ```bash
   mkdir src
   ```
2. Tulis kode pengujian pada `src/main.cpp`:
   ```cpp
   #include <iostream>
   #include <memory>
   #include <concepts>
   #include <string>

   // Uji fitur C++20 Concepts
   template <typename T>
   concept Printable = requires(T a) {
       std::cout << a;
   };

   template <Printable T>
   void print_message(const T& msg) {
       std::cout << msg << std::endl;
   }

   int main() {
       // Uji Modern Smart Pointer
       auto ptr = std::make_unique<std::string>("Status: Lingkungan C++20 berhasil diverifikasi dan siap dipakai.");
       print_message(*ptr);
       return 0;
   }
   ```

### Langkah 5: Kompilasi dan Eksekusi
Gunakan CMake untuk mengonfigurasi dan membangun proyek:
```bash
cmake -B build -S .
cmake --build build
./build/app
```
*(Pada Windows, eksekusi `./build/Debug/app.exe`).*

## 4. Dokumen yang Diperlukan
1. Berkas build generator `CMakeLists.txt`.
2. Berkas kode sumber `src/main.cpp`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `build/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 30 menit.

