# Standar Operasional Prosedur (SOP): Setup dan Standarisasi Lingkungan Pemrograman Python (Virtual Environment & Dependensi)

## 1. Tujuan
Menetapkan prosedur operasional baku bagi pengembang perangkat lunak dan data science dalam mengonfigurasi interpreter Python, membuat lingkungan virtual terisolasi (*Virtual Environment*), serta mengelola dependensi paket eksternal agar proyek berjalan konsisten, reproduktif, dan terhindar dari konflik versi paket antar proyek.

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 (64-bit), atau distribusi Linux.
2. Memiliki hak akses pengguna lokal untuk mengeksekusi interpreter Python dan menginstalasi paket pustaka.
3. Kapasitas ruang penyimpanan disk kosong minimal 1.0 GB.
4. Tersedia interpreter Python resmi dengan versi minimal **Python 3.10** atau versi rilis stabil terkini (**Python 3.11 / 3.12** disarankan).
5. Koneksi internet aktif untuk mengakses repositori resmi Python Package Index (PyPI).
6. **Kebijakan Isolasi Wajib:** Pengembang dilarang keras menginstalasi paket pustaka pihak ketiga secara global (`pip install` tanpa mengaktifkan virtual environment) guna menjaga integritas sistem operasi dan mencegah kerusakan dependensi sistem.

## 3. Tahapan Proses

### Langkah 1: Pemeriksaan Interpreter Python Global
Buka terminal atau command prompt, lalu periksa ketersediaan dan versi Python yang terpasang pada sistem:
```bash
python3 --version
# Pada Windows, jika python3 tidak terdefinisi:
python --version
```
Pastikan versi yang terpasang adalah Python 3.10 atau versi di atasnya.

### Langkah 2: Pembuatan Direktori Proyek
Arahkan terminal ke direktori kerja yang dituju, atau buat direktori baru untuk proyek:
```bash
mkdir my-python-project
cd my-python-project
```

### Langkah 3: Pembuatan Lingkungan Virtual Terisolasi (Virtual Environment)
Gunakan modul bawaan standar Python `venv` untuk membuat lingkungan virtual lokal dengan nama konvensi standar `.venv`:
```bash
python3 -m venv .venv
```
Perintah ini akan membuat folder `.venv/` yang berisi salinan mandiri dari biner Python, compiler tools, dan pustaka `site-packages` terisolasi.

### Langkah 4: Aktivasi Lingkungan Virtual
- **macOS / Linux (bash/zsh):**
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell):**
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
  *(Catatan: Jika muncul galat Execution Policy di PowerShell, jalankan `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`).*

Setelah diaktifkan, pastikan prompt terminal menampilkan prefiks `(.venv)` yang menandakan sesi saat ini berada di dalam lingkungan virtual.

### Langkah 5: Pemutakhiran Pip & Tooling Dasar
Di dalam lingkungan virtual yang aktif, perbarui tool manajemen paket `pip`, `setuptools`, dan `wheel` ke versi paling mutakhir:
```bash
python -m pip install --upgrade pip setuptools wheel
```

### Langkah 6: Instalasi Paket dan Dokumentasi Dependensi (requirements.txt)
1. Pasang paket pustaka yang dibutuhkan proyek, misalnya:
   ```bash
   pip install httpx fastapi
   ```
2. Bekukan (*freeze*) seluruh daftar pustaka beserta nomor versinya secara presisi ke dalam berkas `requirements.txt`:
   ```bash
   pip freeze > requirements.txt
   ```
3. Jika mereplikasi proyek yang sudah ada, pasang dependensi langsung dari berkas acuan:
   ```bash
   pip install -r requirements.txt
   ```

### Langkah 7: Konfigurasi Pengabaian Git (.gitignore)
Buat berkas `.gitignore` pada akar repositori agar direktori lingkungan virtual tidak ikut terunggah ke version control:
```bash
echo ".venv/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
```

### Langkah 8: Pengujian Eksekusi Skrip Python
1. Buat berkas uji coba sederhana bernama `verify_env.py`:
   ```python
   import sys

   print(f"Versi Python: {sys.version}")
   print(f"Prefix Virtual Environment: {sys.prefix}")
   assert sys.prefix != sys.base_prefix, "Galat: Virtual environment belum aktif!"
   print("Status: Lingkungan virtual Python aktif dan terverifikasi aman.")
   ```
2. Jalankan skrip melalui terminal:
   ```bash
   python verify_env.py
   ```
3. Pastikan asersi berhasil dan status terverifikasi tercetak dengan sukses.

## 4. Dokumen yang Diperlukan
1. Berkas biner interpreter Python resmi (dari https://python.org atau manajer paket OS).
2. Berkas manifes daftar dependensi pustaka (`requirements.txt` atau `pyproject.toml`).
3. Berkas konfigurasi pengabaian repositori git (`.gitignore`).
4. Berkas skrip uji coba verifikasi lingkungan virtual (`verify_env.py`).
5. Log versi biner interpreter (`python --version`) dan daftar paket terpasang (`pip list`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.
  - Pemeriksaan interpreter dan pembuatan virtual environment: 3 - 5 menit.
  - Aktivasi dan pemutakhiran `pip`: 2 - 3 menit.
  - Instalasi paket dependensi dan pembuatan `requirements.txt`: 5 - 10 menit.
  - Validasi uji eksekusi skrip: 2 menit.
