import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import config
from app.routers import locations, users, hospitals, doctors, queue
from app.version import __version__

# 1. Collect all sub‑routers under a single API router

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(locations.router)
api_router.include_router(hospitals.router)
api_router.include_router(doctors.router)
api_router.include_router(queue.router)


def create_app() -> FastAPI:
    app = FastAPI(
        title=config.PROJECT_NAME,
        version=__version__,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,  # disable redoc if you don't need it
    )

    # 2. Enforce HTTPS in production (redirects HTTP → HTTPS)
    if config.ENVIRONMENT == "production":
        app.add_middleware(HTTPSRedirectMiddleware)

    # 3. Trust only specified hosts
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=config.TRUSTED_HOSTS,
    )

    # 4. GZip compress responses over 1000 bytes
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 5. CORS must be outermost so it can respond to OPTIONS (preflight) before any redirect
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "https://medlife-production.up.railway.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 6. Add custom security headers on every response
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains; preload"
        )
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
        return response

    # 7. Register the API routers
    app.include_router(api_router)

    # 8. Health‑check endpoint (not shown in OpenAPI)
    @app.get("/", include_in_schema=False)
    async def health_check():
        return {
            "status": "ok",
            "project": config.PROJECT_NAME,
            "docs": "/docs",
        }

    return app


# 9. Create the app instance
app = create_app()

# 10. If run as a script, launch Uvicorn
if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=config.RELOAD,
    )
