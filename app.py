from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import Response

from database.database import engine, SessionLocal
from database import models
from routes import user, recipe

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recipe-Service",
              description="This is a test project, with auto docs for the API",
              version="0.1")


@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response("Internal server error", status_code=500)
    try:
        request.state.db = SessionLocal()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response


app.include_router(user.router, prefix='/user')
app.include_router(recipe.router, prefix='/recipe')
