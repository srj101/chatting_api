from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.routers import auth, users, chats, messages, files, api_keys
from app.middleware import APIKeyMiddleware

app = FastAPI(
    title="Chat API",
    description="A simple chat API with authentication, file uploads, and more",
    version="1.0.0",
    docs_url=None  # We'll create a custom docs endpoint
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API key middleware
app.add_middleware(APIKeyMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(chats.router, prefix="/api/v1", tags=["Chats"])
app.include_router(messages.router, prefix="/api/v1", tags=["Messages"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Chat API Documentation",
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
    )

@app.on_event("startup")
async def startup():
    init_db()

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Chat API. Visit /docs for documentation."}