from fastapi import FastAPI
from api.controllers import stt

app = FastAPI()

# Include routers
app.include_router(stt.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
