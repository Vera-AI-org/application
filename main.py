from fastapi import FastAPI
from api.routers import auth_router, report_router
from core.database import engine
import models.user_model as user_model

user_model.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Vera AI - Refactored API",
    description="A clean API structure with separated concerns.",
    version="2.0.0",
)

app.include_router(auth_router.router)
app.include_router(report_router.router)

@app.get("/", tags=["Default"])
def root():
    return {"message": "Welcome to the Vera AI API!"}