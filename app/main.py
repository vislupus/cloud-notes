from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import TITLE_MAX_LENGTH, Note

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Cloud Notes", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

DbSession = Annotated[Session, Depends(get_db)]


def get_note_or_404(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


def validate_note(title: str, content: str) -> tuple[str, str, list[str]]:
    title = title.strip()
    errors = []
    if not title:
        errors.append("Title is required.")
    elif len(title) > TITLE_MAX_LENGTH:
        errors.append(f"Title must be at most {TITLE_MAX_LENGTH} characters.")
    return title, content, errors


def render_form(request: Request, *, note: Note | None, title: str, content: str,
                errors: list[str] | None = None, status_code: int = 200) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "note_form.html",
        {
            "note": note,
            "title": title,
            "content": content,
            "errors": errors or [],
            "title_max_length": TITLE_MAX_LENGTH,
        },
        status_code=status_code,
    )


@app.get("/health")
def health(db: DbSession) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            {"status": "error", "database": "unavailable"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    return JSONResponse({"status": "ok", "database": "ok"})


@app.get("/", response_class=HTMLResponse)
def list_notes(request: Request, db: DbSession):
    notes = db.scalars(select(Note).order_by(Note.updated_at.desc(), Note.id.desc())).all()
    return templates.TemplateResponse(request, "index.html", {"notes": notes})


@app.get("/notes/new", response_class=HTMLResponse)
def new_note(request: Request):
    return render_form(request, note=None, title="", content="")


@app.post("/notes", response_class=HTMLResponse)
def create_note(
    request: Request,
    db: DbSession,
    title: Annotated[str, Form()] = "",
    content: Annotated[str, Form()] = "",
):
    title, content, errors = validate_note(title, content)
    if errors:
        return render_form(request, note=None, title=title, content=content,
                           errors=errors, status_code=422)
    db.add(Note(title=title, content=content))
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/notes/{note_id}/edit", response_class=HTMLResponse)
def edit_note(request: Request, note_id: int, db: DbSession):
    note = get_note_or_404(db, note_id)
    return render_form(request, note=note, title=note.title, content=note.content)


@app.post("/notes/{note_id}", response_class=HTMLResponse)
def update_note(
    request: Request,
    note_id: int,
    db: DbSession,
    title: Annotated[str, Form()] = "",
    content: Annotated[str, Form()] = "",
):
    note = get_note_or_404(db, note_id)
    title, content, errors = validate_note(title, content)
    if errors:
        return render_form(request, note=note, title=title, content=content,
                           errors=errors, status_code=422)
    note.title = title
    note.content = content
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/notes/{note_id}/delete")
def delete_note(note_id: int, db: DbSession):
    note = get_note_or_404(db, note_id)
    db.delete(note)
    db.commit()
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
