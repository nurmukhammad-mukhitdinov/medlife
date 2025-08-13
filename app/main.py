import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import config
from app.routers import (
    locations,
    users,
    hospitals,
    doctors,
    queue,
    chat,
    hospital_admins,
    doctor_bookings,
    service_prices,
)
from app.version import __version__

# ----------------- Routers -----------------
api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(locations.router)
api_router.include_router(hospitals.router)
api_router.include_router(doctors.router)
api_router.include_router(queue.router)
api_router.include_router(chat.router)
api_router.include_router(hospital_admins.router)
api_router.include_router(doctor_bookings.router)
api_router.include_router(service_prices.router)

def create_app() -> FastAPI:
    app = FastAPI(
        title=config.PROJECT_NAME,
        version=__version__,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )

    # ----------------- Fully open CORS -----------------
    # allow_origin_regex=".*" dynamically reflects the Origin,
    # so it works with allow_credentials=True
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=".*",  # match any origin
        allow_credentials=True,   # allow cookies / Authorization headers
        allow_methods=["*"],      # allow all HTTP methods
        allow_headers=["*"],      # allow all request headers
        expose_headers=["*"],     # expose all response headers
    )

    # ----------------- Fully open Host -----------------
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # allow any Host header
    )

    # ----------------- HTTPS redirect (optional) -----------------
    if config.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # ----------------- GZip compression -----------------
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # ----------------- Security headers -----------------
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if config.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response

    # ----------------- Routes -----------------
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def health_check():
        return {"status": "ok", "project": config.PROJECT_NAME, "docs": "/docs"}

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.RELOAD,
    )
