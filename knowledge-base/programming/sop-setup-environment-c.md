# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman C (C17 / C23 Standards & Make/CMake)

## 1. Tujuan
Menetapkan prosedur operasional baku bagi pengembang perangkat lunak dalam mengonfigurasi toolchain compiler bahasa C (GCC, Clang, atau MSVC) dengan dukungan standar ISO C17 dan C23, mengelola alokasi memori dinamis secara aman, serta memastikan eksekusi kode biner C efisien dan terbebas dari kebocoran memori (*memory leak*).

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau distribusi Linux.
2. Memiliki hak akses administrator / `sudo` untuk instalasi paket build essential.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.5 GB.
4. Compiler biner C resmi yang mendukung standar minimal **ISO C17 / C23**:
   - macOS: Apple Clang (via Xcode Command Line Tools).
   - Linux: GCC versi 10+ atau Clang versi 13+.
   - Windows: MinGW-w64 (GCC), LLVM Clang, atau Microsoft Visual C++ (MSVC /std:c11 /std:c17).
5. Build tool otomasi: `make` atau `cmake`.
6. Tool analisis memori disarankan: `valgrind` (pada Linux) atau AddressSanitizer (`-fsanitize=address`).

## 3. Tahapan Proses

### Langkah 1: Pemasangan Compiler C dan Build Tools
- **macOS:**
  ```bash
  xcode-select --install
  brew install make cmake
  ```
- **Linux (Ubuntu/Debian):**
  ```bash
  sudo apt-get update
  sudo apt-get install -y build-essential gcc make valgrind
  ```
- **Windows:**
  Gunakan `winget` untuk memasang compiler GCC (MinGW-w64) atau LLVM:
  ```powershell
  winget install BrechtSanders.MinGW-w64
  ```

### Langkah 2: Verifikasi Versi Compiler C
Buka terminal dan jalankan verifikasi compiler:
```bash
gcc --version # atau clang --version
```
Pastikan compiler mendukung flag standar modern `-std=c17` atau `-std=c2x` / `-std=c23`.

### Langkah 3: Pembuatan Struktur Proyek C
Buat folder proyek baru:
```bash
mkdir modern-c-project
cd modern-c-project
mkdir src
```

### Langkah 4: Pembuatan Kode Pengujian Fitur Modern C (Generic Selection & Safe Pointer)
Buat berkas `src/main.c`:
```c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

// Uji fitur C11/C17/C23 Generic Selection (_Generic)
#define type_name(x) _Generic((x), \
    int: "int", \
    float: "float", \
    double: "double", \
    char*: "string", \
    default: "unknown")

typedef struct {
    int id;
    const char* name;
    bool active;
} SystemConfig;

int main(void) {
    // Alokasi memori dinamis aman
    SystemConfig* cfg = (SystemConfig*)malloc(sizeof(SystemConfig));
    if (cfg == NULL) {
        fprintf(stderr, "Galat: Gagal mengalokasikan memori!\n");
        return 1;
    }

    // Designated Initializers
    *cfg = (SystemConfig){ .id = 101, .name = "CintaMamaAI Kernel", .active = true };

    int num = 42;
    printf("Tipe data variabel num terdeteksi: %s\n", type_name(num));
    printf("Status Modul [%s]: %s\n", cfg->name, cfg->active ? "AKTIF" : "NONAKTIF");
    printf("Status: Lingkungan Bahasa C (C17/C23) berhasil diverifikasi dan aman.\n");

    // Pelepasan memori wajib guna mencegah memory leak
    free(cfg);
    cfg = NULL;

    return 0;
}
```

### Langkah 5: Kompilasi dan Eksekusi
1. Kompilasi menggunakan standar C17 dengan flag peringatan ketat (*strict warnings*) dan AddressSanitizer:
   ```bash
   gcc -std=c17 -Wall -Wextra -pedantic -fsanitize=address src/main.c -o app
   ```
2. Jalankan berkas biner:
   ```bash
   ./app
   ```
3. Pastikan program mengeksekusi seluruh baris konfirmasi tanpa menimbulkan kesalahan alokasi memori (*segfault* / *leak*).

## 4. Dokumen yang Diperlukan
1. Berkas kode sumber `src/main.c`.
2. Berkas automasi build `Makefile` atau `CMakeLists.txt`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan biner `./app`, `*.o`, dan `*.a`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.

