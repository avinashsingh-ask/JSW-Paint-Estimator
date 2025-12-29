"""FastAPI application entry point."""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from api import api_router
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Get frontend directory path
FRONTEND_DIR = Path(__file__).parent / "frontend"  # Fixed: removed extra .parent

# Create FastAPI app
app = FastAPI(
    title=os.getenv("APP_NAME", "JSW Paint Estimator"),
    version=os.getenv("APP_VERSION", "1.0.0"),
    description="""
    Paint estimation API with two scenarios:
    
    **Scenario 1: Manual Estimation**
    - User inputs room dimensions, doors, windows
    - System calculates paintable area, paint quantity, and cost
    
    **Scenario 2: OpenCV-based Estimation**
    - User uploads room images
    - System detects doors/windows using YOLO
    - Estimates dimensions and calculates requirements
    
    Provides detailed product breakdown (primer, putty, paint) and cost estimation.
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
# In development, allow all origins. In production, use specific origins.
debug_mode = os.getenv("DEBUG", "True").lower() == "true"

if debug_mode:
    # Allow all origins in development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when allow_origins is ["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Use specific origins in production
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router)

# Serve static files (CSS, JS) directly at root level
if FRONTEND_DIR.exists():
    # Mount CSS directory
    css_dir = FRONTEND_DIR / "css"
    if css_dir.exists():
        app.mount("/css", StaticFiles(directory=str(css_dir)), name="css")
    
    # Mount JS directory
    js_dir = FRONTEND_DIR / "js"
    if js_dir.exists():
        app.mount("/js", StaticFiles(directory=str(js_dir)), name="js")
    
    # Mount entire frontend as static (for any other static assets)
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
async def root():
    """Serve the frontend application."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    else:
        return {
            "message": "JSW Paint Estimator API",
            "version": os.getenv("APP_VERSION", "1.0.0"),
            "docs": "/docs",
            "health": "/health",
            "note": "Frontend not found. API is available at /docs"
        }


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors and log details for debugging."""
    print(f"\n❌ VALIDATION ERROR on {request.method} {request.url.path}")
    print(f"   Errors: {exc.errors()}")
    print(f"   Body: {exc.body}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": str(exc.body)[:500]}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    uvicorn.run(
        "main:app",  # Fixed: Changed from "app.main:app" to "main:app"
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
