from fastapi import FastAPI
from api.routes import router

app = FastAPI(
    title="LabPulse",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "LabPulse API Running"}
