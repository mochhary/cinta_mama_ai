# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Pemrograman Kotlin (Kotlin 2.0+ & Gradle)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang compiler Kotlin, mengintegrasikannya dengan Java Development Kit (JDK 21 LTS), serta mengonfigurasi build automation Gradle dengan Kotlin DSL (`build.gradle.kts`) untuk memanfaatkan compiler modern K2 dan fitur *smart casts*.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau distribusi Linux.
2. Memori RAM sistem minimal 4 GB (disarankan 8 GB atau lebih untuk efisiensi Gradle daemon).
3. Kapasitas ruang penyimpanan disk kosong minimal 2.5 GB.
4. Terpasang runtime **Java Development Kit (JDK 21 LTS)** resmi (Temurin/Adoptium).
5. Versi compiler Kotlin resmi: **Kotlin 2.0.0 atau yang lebih baru** (K2 Compiler enabled).
6. Build tool resmi: **Gradle versi 8.5+**.

## 3. Tahapan Proses

### Langkah 1: Instalasi Kotlin CLI dan SDKMAN
- **macOS / Linux:** Gunakan SDKMAN (*Software Development Kit Manager*):
  ```bash
  curl -s "https://get.sdkman.io" | bash
  source "$HOME/.sdkman/bin/sdkman-init.sh"
  sdk install java 21.0.3-tem
  sdk install kotlin
  sdk install gradle
  ```
- **Windows:** Pasang via `winget` atau Chocolatey:
  ```powershell
  winget install JetBrains.Kotlin
  winget install Gradle.Gradle
  ```

### Langkah 2: Verifikasi Instalasi Kotlin
Buka terminal dan periksa versi:
```bash
kotlin -version
kotlinc -version
gradle -v
```
Pastikan `kotlinc` menampilkan versi `2.0.x` atau yang lebih mutakhir.

### Langkah 3: Inisialisasi Proyek Gradle dengan Kotlin DSL
1. Buat folder proyek baru:
   ```bash
   mkdir my-kotlin-project
   cd my-kotlin-project
   ```
2. Inisialisasi struktur aplikasi berbasis Gradle Kotlin DSL:
   ```bash
   gradle init --type kotlin-application --dsl kotlin --project-name my-kotlin-app --package com.example.app --no-incubating
   ```

### Langkah 4: Pengujian Fitur Modern Kotlin 2.0 (Smart Casts & Data Objects)
1. Buka atau buat berkas `app/src/main/kotlin/com/example/app/App.kt`:
   ```kotlin
   package com.example.app

   // Uji Data Object Kotlin modern
   sealed interface AppState {
       data object Initializing : AppState
       data class Running(val version: String) : AppState
   }

   fun evaluateState(state: AppState): String {
       // Uji exhaustive when dan Smart Cast 2.0
       return when (state) {
           is AppState.Initializing => "Memulai inisialisasi lingkungan..."
           is AppState.Running => "Status: Kotlin ${state.version} K2 Compiler aktif dan terverifikasi."
       }
   }

   fun main() {
       val state: AppState = AppState.Running(KotlinVersion.CURRENT.toString())
       println(evaluateState(state))
   }
   ```
2. Jalankan kompilasi dan aplikasi via Gradle:
   ```bash
   ./gradlew run
   ```
   *(Pada Windows: `gradlew.bat run`).*

## 4. Dokumen yang Diperlukan
1. Berkas build konfigurasi `build.gradle.kts` dan `settings.gradle.kts`.
2. Berkas kode sumber `App.kt`.
3. Berkas pengabaian version control `.gitignore` (mengabaikan folder `.gradle/` dan `build/`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 15 hingga 25 menit.

