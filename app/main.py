from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.routers import users, discover, connections, sessions
from app.routers.websocket import router as websocket_router

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded



app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://blablagoa.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# rate limiting for if user send large number of requests 
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(users.router)
app.include_router(discover.router)
app.include_router(connections.router)
app.include_router(sessions.router)
app.include_router(websocket_router)

@app.get("/health", tags=["health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "debug": settings.DEBUG
    }