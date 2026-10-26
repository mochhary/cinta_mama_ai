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

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "templates" / "index.html"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class GenerateRequest(BaseModel):
    prompt: str


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
    async with httpx.AsyncClient(timeout=120.0) as client:
        selected_model = await get_available_model(client)
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": selected_model,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
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
def health_check():
    return {
        "status": "ok",
        "service": "CintaMamaAI",
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
    """Stream token dan telemetri langsung dari Ollama baris demi baris dengan persona CintaMamaAI."""
    async with httpx.AsyncClient(timeout=120.0) as check_client:
        selected_model = await get_available_model(check_client)

    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": request.prompt,
        "system": SYSTEM_PROMPT,
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