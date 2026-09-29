from pathlib import Path

from fastapi import (
    APIRouter,
    Request,
)
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
)
from fastapi.templating import Jinja2Templates

from app.models import (
    ImageTestRequest,
    PromptRequest,
)

from app.services.exporters import (
    export_comic_to_pdf,
)

from app.services.gemini_flash import (
    generate_outline,
)

from app.services.gemini_pro import (
    generate_story,
)

from app.services.image_generator import (
    generate_panel_image,
)

from app.services.layout_builder import (
    build_layout,
)


BASE_DIR = Path(__file__).resolve().parents[1]

templates = Jinja2Templates(
    directory=str(
        BASE_DIR / "templates"
    )
)

router = APIRouter()


def generate_comic(
    data: PromptRequest,
):
    """
    Complete ComicCraft pipeline:

    1. Gemini Flash -> outline
    2. Gemini Pro -> narration/dialogue
    3. Hugging Face -> images
    4. Layout builder
    5. PDF exporter
    """

    outline = generate_outline(
        story_prompt=data.story_prompt,
        character_name=data.character_name,
        setting=data.setting,
        tone=data.tone,
    )

    story = generate_story(
        outline=outline,
        character_name=data.character_name,
        tone=data.tone,
    )

    image_paths = []

    for panel in outline["panels"]:
        image_prompt = (
            f"{panel['image_prompt']}. "
            f"Art style: {data.art_style}. "
            f"Comic panel composition. "
            f"No text, no speech bubbles."
        )

        image_path = generate_panel_image(
            prompt=image_prompt,
            panel_number=panel["panel"],
        )

        image_paths.append(
            image_path
        )

    layout = build_layout(
        outline=outline,
        story=story,
        image_paths=image_paths,
    )

    pdf_path = export_comic_to_pdf(
        layout
    )

    return {
        "outline": outline,
        "story": story,
        "layout": layout,
        "pdf_path": pdf_path,
    }


@router.get(
    "/",
    response_class=HTMLResponse,
)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        },
    )


@router.post(
    "/generate",
    response_class=HTMLResponse,
)
async def generate(
    request: Request,
):
    try:
        form = await request.form()

        data = PromptRequest(
            story_prompt=form.get(
                "story_prompt",
                "",
            ),
            character_name=form.get(
                "character_name",
                "Alex",
            ),
            setting=form.get(
                "setting",
                "A futuristic city",
            ),
            tone=form.get(
                "tone",
                "Adventure",
            ),
            art_style=form.get(
                "art_style",
                "Modern comic book",
            ),
        )

        result = generate_comic(
            data
        )

        return templates.TemplateResponse(
            "comic_preview.html",
            {
                "request": request,
                "result": result,
            },
        )

    except Exception as exc:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error": str(exc),
            },
            status_code=500,
        )


@router.post(
    "/generate-comic/json",
)
async def generate_comic_json(
    data: PromptRequest,
):
    try:
        result = generate_comic(
            data
        )

        return JSONResponse(
            content=result
        )

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(exc),
            },
        )


@router.post(
    "/test-image",
)
async def test_image(
    data: ImageTestRequest,
):
    try:
        image_path = generate_panel_image(
            prompt=data.prompt,
            panel_number=999,
        )

        return {
            "success": True,
            "image": image_path,
        }

    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
            },
        )


@router.get(
    "/export-success",
    response_class=HTMLResponse,
)
async def export_success(
    request: Request,
):
    return templates.TemplateResponse(
        "export_success.html",
        {
            "request": request,
        },
    )


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "application": "ComicCraft",
    }