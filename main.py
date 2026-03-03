from fastapi import FastAPI
from database import init_db
from routes.chat import router as chat_router

app = FastAPI(
    title='NOC API',
    description='Network Operation Center API Platform',
    version='0.0.1'
)


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(chat_router)


@app.get('/')
async def default():
    return 'Default route'
