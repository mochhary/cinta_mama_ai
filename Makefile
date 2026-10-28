.PHONY: setup up down logs status index test

# Default: jalankan script setup otomatis
setup:
	@chmod +x ./setup.sh
	@./setup.sh

# Nyalakan service Docker
up:
	docker compose up -d

# Matikan service Docker
down:
	docker compose down

# Pantau log seluruh container
logs:
	docker compose logs -f

# Cek status kesehatan seluruh container
status:
	docker compose ps
	@echo "\n--- OpenSearch Cluster Health ---"
	@curl -s http://localhost:9200/_cluster/health?pretty || true
	@echo "\n--- OpenSearch Document Count ---"
	@curl -s http://localhost:9200/knowledge_base/_count?pretty || true
	@echo "\n--- Ollama Models ---"
	@curl -s http://localhost:11434/api/tags || true

# Jalankan proses indexing vektor ulang
index:
	docker compose exec api python -c "from app.vectordb import index_knowledge_base; index_knowledge_base()"

# Uji coba pencarian semantik vektor
test:
	docker compose exec api python -m app.vectordb

