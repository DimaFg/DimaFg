from datetime import UTC, datetime

from app.adapter.database.models.portfolio import (
    Photo,
    PhotoCategory,
    PhotoVariant,
    ProcessingStatus,
)


def test_health(client):
    assert client.get("/api/health/live").json() == {"status": "ok"}
    r = client.get("/api/health/ready")
    assert r.status_code == 200 and r.json()["database"] == "ok"


def test_request_id_is_returned(client):
    r = client.get("/api/health/live", headers={"X-Request-ID": "abc12345-test"})
    assert r.headers["x-request-id"] == "abc12345-test"


def test_services_sorted_and_active_only(client, db):
    from app.adapter.database.models.services import Service

    db.query(Service).filter(Service.slug == "print").update({"is_active": False})
    db.commit()
    items = client.get("/api/v1/services").json()["items"]
    slugs = [i["slug"] for i in items]
    assert slugs[0] == "events"
    assert "print" not in slugs


def _photo(db, slug, **kw):
    cat = db.query(PhotoCategory).filter_by(slug=kw.pop("category", "street")).one()
    photo = Photo(
        slug=slug,
        title=slug,
        alt_text="alt",
        category=cat,
        width=1600,
        height=1067,
        aspect_ratio=1.5,
        original_key=f"originals/{slug}.jpg",
        processing_status=kw.pop("status", ProcessingStatus.ready),
        is_published=kw.pop("published", True),
        published_at=datetime.now(UTC),
        **kw,
    )
    photo.variants = [
        PhotoVariant(
            format="webp", width=640, height=427, size_bytes=1, object_key=f"p/{slug}-640.webp"
        )
    ]
    db.add(photo)
    db.commit()
    return photo


def test_portfolio_shows_only_public_photos(client, db):
    _photo(db, "bridge-sunset")
    _photo(db, "draft", published=False)
    _photo(db, "processing", status=ProcessingStatus.processing)
    _photo(db, "wedding", category="event")

    body = client.get("/api/v1/portfolio").json()
    assert {c["slug"] for c in body["categories"]} >= {"street", "event"}
    assert {p["slug"] for p in body["items"]} == {"bridge-sunset", "wedding"}
    # приватный ключ оригинала не утекает
    assert "original_key" not in body["items"][0]
    assert body["items"][0]["sources"][0]["url"].startswith("https://")

    street = client.get("/api/v1/portfolio", params={"category": "street"}).json()
    assert [p["slug"] for p in street["items"]] == ["bridge-sunset"]

    assert client.get("/api/v1/portfolio/bridge-sunset").json()["category"] == "street"
    r = client.get("/api/v1/portfolio/draft")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"
    assert r.json()["error"]["request_id"]


def test_portfolio_rejects_bad_filter(client):
    r = client.get("/api/v1/portfolio", params={"category": "DROP TABLE"})
    assert r.status_code == 422
    assert "category" in r.json()["error"]["fields"]


def test_ready_reports_revision(client):
    assert client.get("/api/health/ready").json()["revision"] == "0001"


def test_ready_fails_on_revision_mismatch(client):
    from sqlalchemy import text

    from app.adapter.database.base import engine

    with engine.begin() as conn:
        conn.execute(text("UPDATE alembic_version SET version_num = 'stale'"))
    try:
        r = client.get("/api/health/ready")
        assert r.status_code == 503
    finally:
        with engine.begin() as conn:
            conn.execute(text("UPDATE alembic_version SET version_num = '0001'"))
