from fastapi import FastAPI
from app.core.config import settings


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",       # interactive API explorer at /docs
    redoc_url="/redoc"      # alternative docs at /redoc
)


# Health check — first endpoint, most important one
# AWS load balancer, Render, and Docker all ping this
# to know if your app is alive
@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "debug_mode": settings.DEBUG
    }