from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes.chat import router as chat_router
from routes.auth import router as auth_router

app = FastAPI(
    title='NOC API',
    description='Network Operation Center API Platform',
    version='0.0.1'
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    init_db()


app.include_router(auth_router)
app.include_router(chat_router)


@app.get('/')
async def default():
    return 'Default route'
