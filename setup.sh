#!/usr/bin/env bash
# ==============================================================================
# Script Setup & Inisialisasi Otomatis CintaMamaAI RAG Environment
# Menjalankan container, mengunduh model Ollama, dan mengindeks Vector DB
# ==============================================================================
set -e

echo "=========================================================="
echo "          CINTAMAMAAI - SETUP ENVIRONMENT OTOMATIS        "
echo "=========================================================="

# 1. Periksa apakah Docker daemon aktif
if ! docker info > /dev/null 2>&1; then
    echo "[ERROR] Docker tidak terdeteksi aktif."
    echo "        Silakan pastikan Docker Desktop sudah dibuka dan berjalan."
    exit 1
fi
echo "[OK] Docker daemon aktif."

# 2. Nyalakan seluruh container service lewat Docker Compose
echo "[INFO] Menjalankan seluruh service container (API, Ollama, OpenSearch)..."
docker compose up -d --build

# 3. Tunggu service Ollama siap
echo "[INFO] Menunggu service Ollama siap..."
MAX_RETRY=30
COUNT=0
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRY ]; then
        echo "[ERROR] Timeout menunggu Ollama service."
        exit 1
    fi
done
echo "[OK] Service Ollama siap di http://localhost:11434."

# 4. Pull model LLaMA dan Nomic Embed jika belum ada
pull_model_if_missing() {
    MODEL_NAME=$1
    if ! docker compose exec -T ollama ollama list | grep -q "$MODEL_NAME"; then
        echo "[INFO] Mengunduh model $MODEL_NAME ke Ollama (bisa memakan waktu beberapa menit)..."
        docker compose exec -T ollama ollama pull "$MODEL_NAME"
        echo "[OK] Model $MODEL_NAME berhasil diunduh."
    else
        echo "[OK] Model $MODEL_NAME sudah tersedia di Ollama."
    fi
}

pull_model_if_missing "nomic-embed-text"
pull_model_if_missing "llama3.2:3b"

# 5. Tunggu service OpenSearch siap
echo "[INFO] Menunggu service OpenSearch siap..."
COUNT=0
until curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; do
    sleep 2
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRY ]; then
        echo "[ERROR] Timeout menunggu OpenSearch service."
        exit 1
    fi
done
echo "[OK] Service OpenSearch siap di http://localhost:9200."

# 6. Periksa dan jalankan Indexing data jika index OpenSearch masih kosong
DOC_COUNT=$(curl -s "http://localhost:9200/knowledge_base/_count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d: -f2 || echo "0")
if [ -z "$DOC_COUNT" ] || [ "$DOC_COUNT" -eq 0 ]; then
    echo "[INFO] Indeks knowledge_base masih kosong. Menjalankan indexing otomatis..."
    docker compose exec -T api python -c "
from app.vectordb import index_knowledge_base
index_knowledge_base()
"
    echo "[OK] Data embedding berhasil diindeks ke OpenSearch."
else
    echo "[OK] Indeks OpenSearch sudah terisi ($DOC_COUNT dokumen terdaftar)."
fi

# 7. Informasi Layanan
echo "=========================================================="
echo "               SELURUH LAYANAN SIAP DIGUNAKAN             "
echo "=========================================================="
echo "Web UI & Chatbot : http://localhost:8000"
echo "OpenSearch API   : http://localhost:9200"
echo "Ollama API       : http://localhost:11434"
echo "=========================================================="
echo "[INFO] Untuk mematikan layanan, jalankan: docker compose down"
echo "[INFO] Untuk melihat log container, jalankan: docker compose logs -f"

