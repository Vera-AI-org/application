from fastapi import FastAPI
from api.routers import auth_router, report_router, document_router
from core.database import engine
import models.user_model as user_model
from fastapi.middleware.cors import CORSMiddleware

user_model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vera AI - Refactored API",
    description="A clean API structure with separated concerns.",
    version="2.0.0",
)

origins = [
    "http://localhost:5173",
    "https://web-client-alpha.vercel.app"   
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(report_router.router)
app.include_router(document_router.router)

@app.get("/", tags=["Default"])
def root():
    return {"message": "Welcome to the Vera AI API!"}