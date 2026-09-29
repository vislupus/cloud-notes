from sqlalchemy import select

from app.models import TITLE_MAX_LENGTH, Note


def create(client, title="First note", content="Hello"):
    return client.post("/notes", data={"title": title, "content": content}, follow_redirects=False)


def all_notes(db):
    db.expire_all()
    return db.scalars(select(Note).order_by(Note.id)).all()


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_empty_list(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "No notes yet" in response.text


def test_new_note_form(client):
    response = client.get("/notes/new")
    assert response.status_code == 200
    assert 'action="/notes"' in response.text


def test_create_note(client, db):
    response = create(client, title="  Groceries  ", content="Milk\nEggs")
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    [note] = all_notes(db)
    assert note.title == "Groceries"
    assert note.content == "Milk\nEggs"
    assert note.created_at is not None
    assert note.updated_at == note.created_at

    page = client.get("/")
    assert "Groceries" in page.text
    assert "Milk\nEggs" in page.text


def test_create_note_requires_title(client, db):
    response = create(client, title="   ", content="orphan")
    assert response.status_code == 422
    assert "Title is required." in response.text
    assert "orphan" in response.text
    assert all_notes(db) == []


def test_create_note_rejects_long_title(client, db):
    response = create(client, title="x" * (TITLE_MAX_LENGTH + 1))
    assert response.status_code == 422
    assert all_notes(db) == []


def test_list_shows_note_count(client):
    create(client, title="One")
    assert "1 note<" in client.get("/").text
    create(client, title="Two")
    assert "2 notes<" in client.get("/").text


def test_list_has_delete_confirmation(client, db):
    create(client, title="Confirm me")
    note = all_notes(db)[0]
    page = client.get("/").text
    assert "Delete this note?" in page
    assert f'action="/notes/{note.id}/delete"' in page


def test_list_escapes_html(client):
    create(client, title="<script>alert(1)</script>")
    page = client.get("/")
    assert "<script>alert(1)</script>" not in page.text
    assert "&lt;script&gt;" in page.text


def test_list_orders_most_recently_updated_first(client, db):
    create(client, title="Older")
    create(client, title="Newer")
    older = all_notes(db)[0]
    client.post(f"/notes/{older.id}", data={"title": "Older (edited)", "content": ""})

    page = client.get("/").text
    assert page.index("Older (edited)") < page.index("Newer")


def test_edit_note_form(client, db):
    create(client, title="Draft", content="Body")
    note = all_notes(db)[0]
    response = client.get(f"/notes/{note.id}/edit")
    assert response.status_code == 200
    assert 'value="Draft"' in response.text
    assert f'action="/notes/{note.id}"' in response.text


def test_update_note(client, db):
    create(client, title="Draft", content="Body")
    original = all_notes(db)[0]
    created_at = original.created_at

    response = client.post(
        f"/notes/{original.id}",
        data={"title": "Final", "content": "Updated body"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    [note] = all_notes(db)
    assert note.title == "Final"
    assert note.content == "Updated body"
    assert note.created_at == created_at
    assert note.updated_at > note.created_at


def test_update_note_validation(client, db):
    create(client, title="Keep me")
    note = all_notes(db)[0]
    response = client.post(f"/notes/{note.id}", data={"title": "", "content": "x"})
    assert response.status_code == 422
    assert all_notes(db)[0].title == "Keep me"


def test_delete_note(client, db):
    create(client, title="Doomed")
    create(client, title="Survivor")
    doomed = all_notes(db)[0]

    response = client.post(f"/notes/{doomed.id}/delete", follow_redirects=False)
    assert response.status_code == 303
    assert [n.title for n in all_notes(db)] == ["Survivor"]


def test_missing_note_returns_404(client):
    assert client.get("/notes/999/edit").status_code == 404
    assert client.post("/notes/999", data={"title": "x"}).status_code == 404
    assert client.post("/notes/999/delete").status_code == 404
