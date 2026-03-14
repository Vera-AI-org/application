from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import engine, Base

# Import all models so SQLAlchemy registers them before create_all
import models.user_model  # noqa: F401
import models.template_model  # noqa: F401
import models.field_model  # noqa: F401
import models.extraction_job_model  # noqa: F401

from api.routers import auth_router, template_router, extraction_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vera AI - Refactored API",
    description="Document extraction tool powered by GPT-4.",
    version="3.0.0",
)

origins = [
    "http://localhost:5173",
    "https://web-client-alpha.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(template_router.router)
app.include_router(extraction_router.router)


@app.get("/", tags=["Default"])
def root():
    return {"message": "Welcome to the Vera AI API!"}