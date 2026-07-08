from api.index import app


def test_vercel_entrypoint_exposes_fastapi_app():
    assert app is not None
    assert hasattr(app, "router")
