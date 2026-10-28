# CintaMamaAI - Popular Programming Languages Docs & Syntax RAG

Sistem asisten tanya-jawab pemrograman berbasis Retrieval-Augmented Generation (RAG) bertenaga Ollama (Llama 3.2 3B & Nomic Embed Text), OpenSearch k-NN Vector DB, dan FastAPI.

---

## Panduan Cepat (Quickstart)

Cukup jalankan satu perintah berikut setelah melakukan clone atau pull repository ini:

```bash
./setup.sh
```

Atau menggunakan `make`:

```bash
make setup
```

Script `setup.sh` secara semi-otomatis akan melakukan:
1. Memeriksa ketersediaan dan status Docker daemon.
2. Membangun (*build*) dan menyalakan seluruh service container (`api`, `ollama`, `opensearch`).
3. Menunggu service siap (*healthcheck polling*).
4. Mengunduh model Ollama yang dibutuhkan (`nomic-embed-text` dan `llama3.2:3b`) jika belum tersedia.
5. Memeriksa status Vector DB dan melakukan indexing otomatis 2.167 chunk pengetahuan ke OpenSearch jika index masih kosong.

Setelah script selesai, seluruh sistem langsung siap digunakan tanpa konfigurasi manual tambahan.

---

## Alamat Layanan

| Layanan | URL | Keterangan |
| :--- | :--- | :--- |
| **Web UI & Chatbot** | [http://localhost:8000](http://localhost:8000) | Antarmuka chat interaktif modern |
| **API Healthcheck** | [http://localhost:8000/health](http://localhost:8000/health) | Endpoint status layanan API |
| **OpenSearch Vector DB** | [http://localhost:9200](http://localhost:9200) | REST API Vector Database (port 9200) |
| **Ollama API** | [http://localhost:11434](http://localhost:11434) | Endpoint LLM & Embedding Engine |

---

## Perintah Operasional

Berikut adalah perintah-perintah praktis yang dapat digunakan:

* **Menjalankan Layanan**:
  ```bash
  docker compose up -d
  # atau
  make up
  ```

* **Mematikan Layanan**:
  ```bash
  docker compose down
  # atau
  make down
  ```

* **Melihat Log Seluruh Container**:
  ```bash
  docker compose logs -f
  # atau
  make logs
  ```

* **Memeriksa Status Layanan & Jumlah Dokumen Vektor**:
  ```bash
  make status
  ```

* **Menjalankan Indexing Vektor Manual**:
  ```bash
  make index
  ```

* **Menguji Pencarian Semantik Vektor**:
  ```bash
  make test
  ```

---

## Struktur Folder Utama

* `app/`: Kode sumber backend FastAPI (`main.py`, `embeddings.py`, `vectordb.py`, `tokens.py`, `ingest.py`).
* `app/templates/`: File antarmuka Web UI modern (`index.html`).
* `knowledge-base/`: Sumber dokumen SOP 15 bahasa pemrograman, PDF resmi, dan data chunk embedding (`embedded_chunks.json`).
* `data/`: Berkas dokumentasi CSV dan PDF hasil scraping.
* `scripts/`: Skrip otomasi scraping dan konversi dokumen.
* `setup.sh`: Skrip instalasi dan inisialisasi lingkungan otomatis.

