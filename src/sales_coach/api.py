import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, UploadFile, File, Form
from fastapi.responses import PlainTextResponse, FileResponse
from pydantic import ValidationError
from .config import Settings
from .engine import Engine
from .models import CallContext, Confirmation, Strict
from .store import Conflict


class Revision(Strict):
    expected_revision: int


def create_app(settings=None, engine=None):
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app):
        if not settings.api_token:
            raise RuntimeError("COACH_API_TOKEN must be set before starting the HTTP API")
        app.state.engine = engine or Engine(settings)
        yield
        if engine is None:
            app.state.engine.close()

    app = FastAPI(title="Sales Coaching Engine", version="0.1.0", lifespan=lifespan)

    def auth(authorization: str | None = Header(default=None)):
        if not settings.api_token or not secrets.compare_digest(authorization or "", f"Bearer {settings.api_token}"):
            raise HTTPException(401, "Bearer token required")

    def service():
        return app.state.engine

    @app.exception_handler(KeyError)
    async def missing(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=404, content={"detail": "Call not found"})

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(ValueError)
    async def invalid(request, exc):
        from fastapi.responses import JSONResponse
        message = "Invalid input schema" if isinstance(exc, ValidationError) else str(exc)
        return JSONResponse(status_code=422, content={"detail": message})

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    @app.post("/v1/examples/{name}", dependencies=[Depends(auth)], status_code=201)
    def staged(name: str):
        return service().submit_fixture(name)

    @app.post("/v1/calls", dependencies=[Depends(auth)], status_code=202)
    async def upload(audio: UploadFile = File(...), context: str = Form("{}")):
        try:
            parsed = CallContext.model_validate_json(context)
            chunks, size = [], 0
            while chunk := await audio.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise HTTPException(413, "Upload exceeds configured limit")
                chunks.append(chunk)
            return service().submit_audio(b"".join(chunks), audio.filename or "audio.wav", parsed)
        finally:
            await audio.close()

    @app.get("/v1/calls/{call_id}", dependencies=[Depends(auth)])
    def get(call_id: str):
        return service().get(call_id)

    @app.post("/v1/calls/{call_id}/confirmation", dependencies=[Depends(auth)], status_code=202)
    def confirm(call_id: str, body: Confirmation):
        return service().confirm(call_id, body)

    @app.post("/v1/calls/{call_id}/retry", dependencies=[Depends(auth)], status_code=202)
    def retry(call_id: str, body: Revision):
        return service().retry(call_id, body.expected_revision)

    @app.get("/v1/calls/{call_id}/report", dependencies=[Depends(auth)], response_class=PlainTextResponse)
    def get_report(call_id: str):
        return service().report(call_id)

    @app.get("/v1/calls/{call_id}/audio", dependencies=[Depends(auth)])
    def audio(call_id: str):
        path, media_type = service().media(call_id)
        return FileResponse(path, media_type=media_type, filename=f"{call_id}{path.suffix}")

    @app.get("/v1/reps/{rep_id}/history", dependencies=[Depends(auth)])
    def history(rep_id: str):
        return service().history(rep_id)

    @app.delete("/v1/calls/{call_id}", dependencies=[Depends(auth)])
    def delete(call_id: str):
        return service().delete(call_id)

    return app
