from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from redis_config import test_redis_connection
from routers import auth, links, redirect


# Test Redis connection on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run on application startup."""
    try:
        test_redis_connection()
        print("✓ Redis connected successfully")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Make sure Redis is running: sudo systemctl start redis")
    yield


app = FastAPI(
    title="URL Shortener App",
    description="Fast, cached URL shortening service",
    version="1.0.0",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# CORS configuration (allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(links.router)
app.include_router(redirect.router)


@app.get("/health")
def health_check():
    """Check if API is running."""
    return {"status": "ok", "message": "URL Shortener API is running"}


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {"message": "URL Shortener API", "docs": "/docs", "health": "/health"}
