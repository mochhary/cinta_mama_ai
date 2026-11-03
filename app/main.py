import os
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
import httpx
from pydantic import BaseModel

try:
    from app.system_prompt import SYSTEM_PROMPT
except ImportError:
    try:
        from system_prompt import SYSTEM_PROMPT
    except ImportError:
        SYSTEM_PROMPT = "Kamu adalah CintaMamaAI, asisten AI yang hangat, penuh kasih, dan bijaksana untuk keluarga."

app = FastAPI(
    title="CintaMamaAI API",
    description="Backend service & RAG Web UI untuk asisten dokumentasi bahasa pemrograman populer up-to-date bertenaga Ollama & FastAPI",
    version="1.0.0",
)

from app.embeddings import embed_text
from app.vector_store import VectorStore

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

OPENSEARCH_BASE_URL = os.getenv("OPENSEARCH_BASE_URL", "http://opensearch:9200")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "cinta-mama-docs")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))

vector_store = VectorStore(base_url=OPENSEARCH_BASE_URL)

KNOWLEDGE_BASE_PATH = os.environ.get("KNOWLEDGE_BASE_PATH", "/app/knowledge-base")


def retrieve_rag_context(query: str, top_k: int = RAG_TOP_K) -> tuple[str, list[dict]]:
    """Melakukan pencarian semantik ke OpenSearch dan menyusun konteks dokumen RAG."""
    try:
        query_embedding = embed_text(query, base_url=OLLAMA_BASE_URL)
        hits = vector_store.search(OPENSEARCH_INDEX, query_embedding, k=top_k)
        if not hits:
            return "", []

        context_parts = []
        for hit in hits:
            doc_id = hit.get("_id", "doc")
            score = hit.get("_score", 0.0)
            source_text = hit.get("_source", {}).get("text", "")
            snippet = source_text[:1200]
            context_parts.append(f"- [Dokumen: {doc_id} | Skor: {score:.4f}]\n{snippet}")

        return "\n\n".join(context_parts), hits
    except Exception:
        return "", []

class GenerateRequest(BaseModel):
    prompt: str


class Message(BaseModel):
    role: str
    content: str


class ChatStreamRequest(BaseModel):
    messages: list[Message]


async def get_available_model(client: httpx.AsyncClient) -> str:
    """Otomatis mendeteksi model yang terinstal di Ollama."""
    try:
        res = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        if res.status_code == 200:
            models = res.json().get("models", [])
            installed_names = [m.get("name") for m in models if m.get("name")]

            # Jika model dari environment terpasang, gunakan itu
            if DEFAULT_MODEL and any(DEFAULT_MODEL in name for name in installed_names):
                return DEFAULT_MODEL

            # Jika tidak, pakai model pertama yang ada di Ollama
            if installed_names:
                return installed_names[0]
    except Exception:
        pass

    return DEFAULT_MODEL


async def call_ollama_generate(prompt: str):
    system_prompt = SYSTEM_PROMPT
    context_str, _ = retrieve_rag_context(prompt, top_k=RAG_TOP_K)
    if context_str:
        system_prompt += f"\n\nKonteks dari Knowledge Base Dokumentasi & SOP Pemrograman CintaMamaAI:\n{context_str}\n\nInstruksi: Utamakan penggunaan fakta teknis, konfigurasi, dan langkah operasional dari konteks di atas."

    async with httpx.AsyncClient(timeout=120.0) as client:
        selected_model = await get_available_model(client)
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
        }

        try:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return {
                "status": "success",
                "brand": "CintaMamaAI",
                "model": selected_model,
                "response": data.get("response", ""),
                "done": data.get("done", True),
                "total_duration": data.get("total_duration"),
                "load_duration": data.get("load_duration"),
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
                "eval_duration": data.get("eval_duration"),
            }
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=f"Tidak dapat terhubung ke Ollama service di {OLLAMA_BASE_URL}. Pastikan container Ollama aktif.",
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Ollama error: {e.response.text}",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Menampilkan Web UI chat interaktif modern CintaMamaAI."""
    if TEMPLATE_PATH.exists():
        return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>CintaMamaAI API is running. UI template not found.</h1>")


@app.get("/health")
@app.get("/test")
async def health_check():
    active_model = DEFAULT_MODEL
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            active_model = await get_available_model(client)
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "CintaMamaAI",
        "model": active_model,
        "message": "Service is healthy and ready",
    }


@app.post("/generate")
async def generate_post(request: GenerateRequest):
    return await call_ollama_generate(request.prompt)


@app.get("/generate")
async def generate_get(prompt: str):
    return await call_ollama_generate(prompt)


@app.post("/generate/stream")
async def generate_stream_endpoint(request: GenerateRequest):
    """Stream token dan telemetri langsung dari Ollama baris demi baris dengan persona CintaMamaAI + RAG."""
    system_prompt = SYSTEM_PROMPT
    context_str, _ = retrieve_rag_context(request.prompt, top_k=RAG_TOP_K)
    if context_str:
        system_prompt += f"\n\nKonteks dari Knowledge Base Dokumentasi & SOP Pemrograman CintaMamaAI:\n{context_str}\n\nInstruksi: Utamakan penggunaan fakta teknis, konfigurasi, dan langkah operasional dari konteks di atas."

    async with httpx.AsyncClient(timeout=120.0) as check_client:
        selected_model = await get_available_model(check_client)

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": request.prompt,
        "system": system_prompt,
        "stream": True,
    }

    async def stream_generator():
        client = httpx.AsyncClient(timeout=180.0)
        try:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield f'{{"error": "Ollama error: {err_body.decode()}"}}\n'
                    return
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"
        except httpx.ConnectError:
            yield '{"error": "Tidak dapat terhubung ke Ollama container."}\n'
        except Exception as e:
            yield f'{{"error": "{str(e)}"}}\n'
        finally:
            await client.aclose()

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")


@app.post("/chat/stream")
async def chat_stream_endpoint(request: ChatStreamRequest):
    """Stream percakapan multi-turn baris demi baris dari Ollama dengan RAG retrieval."""
    if not request.messages or request.messages[-1].role != "user":
        raise HTTPException(
            status_code=400,
            detail="messages harus non-kosong dan elemen terakhir harus role 'user'",
        )

    recent = request.messages[-5:]  # history window
    user_query = recent[-1].content

    system_prompt = SYSTEM_PROMPT
    context_str, _ = retrieve_rag_context(user_query, top_k=RAG_TOP_K)
    if context_str:
        system_prompt += f"\n\nKonteks dari Knowledge Base Dokumentasi & SOP Pemrograman CintaMamaAI:\n{context_str}\n\nInstruksi: Utamakan penggunaan fakta teknis, konfigurasi, dan langkah operasional dari konteks di atas."

    async with httpx.AsyncClient(timeout=120.0) as check_client:
        selected_model = await get_available_model(check_client)

    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": selected_model,
        "messages": [{"role": "system", "content": system_prompt}]
        + [{"role": m.role, "content": m.content} for m in recent],
        "stream": True,
    }

    async def stream_generator():
        client = httpx.AsyncClient(timeout=180.0)
        try:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    err_body = await response.aread()
                    yield f'{{"error": "Ollama error: {err_body.decode()}"}}\n'
                    return
                async for line in response.aiter_lines():
                    if line:
                        yield f"{line}\n"
        except httpx.ConnectError:
            yield '{"error": "Tidak dapat terhubung ke Ollama container."}\n'
        except Exception as e:
            yield f'{{"error": "{str(e)}"}}\n'
        finally:
            await client.aclose()

    return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
