from fastapi import FastAPI
from fastapi.responses import HTMLResponse


app = FastAPI(title="ComicCraftAI")


@app.get("/", response_class=HTMLResponse)
async def home() -> str:
	return "<h1>ComicCraftAI</h1><p>Server is running.</p>"


@app.get("/health")
async def health() -> dict[str, str]:
	return {
		"status": "ok",
		"application": "ComicCraft",
	}
