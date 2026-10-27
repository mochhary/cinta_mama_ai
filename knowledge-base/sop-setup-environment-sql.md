# Standar Operasional Prosedur (SOP): Setup dan Konfigurasi Lingkungan Database SQL (PostgreSQL 16 / 17 & CLI)

## 1. Tujuan
Menetapkan prosedur baku dalam memasang engine database PostgreSQL (versi 16 atau 17), mengonfigurasi autentikasi pengguna dan database lokal, menggunakan command-line tool `psql`, serta menguji eksekusi query modern (DDL, DML, CTE `WITH`, dan fitur JSONB/MERGE).

## 2. Syarat Umum
1. Perangkat komputer dengan sistem operasi macOS, Windows 10/11 64-bit, atau Linux.
2. Memiliki hak akses administrator / `sudo`.
3. Kapasitas ruang penyimpanan disk kosong minimal 2.0 GB.
4. Versi database engine resmi: **PostgreSQL versi 16** atau **PostgreSQL 17** (disarankan via container Docker atau biner paket resmi).
5. Port standar: TCP `5432` terbuka untuk koneksi lokal.

## 3. Tahapan Proses

### Langkah 1: Pemasangan PostgreSQL
- **Opsi A (Direkomendasikan via Docker Compose):**
  Tambahkan service postgres ke `docker-compose.yml`:
  ```yaml
  postgres:
    image: postgres:16-alpine
    restart: always
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: secretpassword
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
  volumes:
    pgdata:
  ```
  Jalankan container: `docker compose up -d postgres`.

- **Opsi B (Instalasi Sistem Langsung):**
  - **macOS:** `brew install postgresql@16 && brew services start postgresql@16`
  - **Linux (Ubuntu):**
    ```bash
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
    sudo systemctl enable --now postgresql
    ```
  - **Windows:** Pasang via `winget install PostgreSQL.PostgreSQL.16` atau installer dari `enterprisedb.com`.

### Langkah 2: Verifikasi Koneksi CLI (psql)
Buka terminal dan periksa versi client:
```bash
psql --version
```
Uji koneksi ke database:
```bash
psql -h localhost -U postgres -d app_db
```

### Langkah 3: Pengujian Skrip SQL Modern (DDL, DML, JSONB, CTE)
1. Buat berkas skrip `verify_database.sql`:
   ```sql
   -- 1. Uji Pembuatan Tabel DDL dengan Constraints
   DROP TABLE IF EXISTS system_logs;
   CREATE TABLE system_logs (
       id BIGSERIAL PRIMARY KEY,
       service_name VARCHAR(100) NOT NULL,
       metadata JSONB NOT NULL DEFAULT '{}',
       created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
   );

   -- 2. Uji Insert DML dengan Data JSONB
   INSERT INTO system_logs (service_name, metadata)
   VALUES
       ('AuthService', '{"environment": "production", "status": "active"}'),
       ('RAGService', '{"model": "llama3.2:3b", "status": "ready"}');

   -- 3. Uji Query Modern dengan CTE (Common Table Expression) & JSONB Extraction
   WITH ActiveServices AS (
       SELECT
           service_name,
           metadata->>'status' AS current_status,
           created_at
       FROM system_logs
   )
   SELECT
       service_name,
       current_status,
       created_at
   FROM ActiveServices
   ORDER BY created_at DESC;
   ```
2. Eksekusi skrip SQL melalui terminal `psql`:
   ```bash
   psql -h localhost -U postgres -d app_db -f verify_database.sql
   ```
3. Pastikan hasil tabel tercetak dengan status record yang berhasil diekstrak dari JSONB.

## 4. Dokumen yang Diperlukan
1. Berkas skrip pengujian SQL `verify_database.sql`.
2. Berkas konfigurasi container `docker-compose.yml` (jika menggunakan container).
3. Salinan kredensial lingkungan `.env` (berisi `DATABASE_URL`).

## 5. Estimasi Waktu
- **Estimasi Total Pengerjaan:** 10 hingga 20 menit.

