import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import create_tables
from agent import chat

app = FastAPI(
    title="AI User Management System",
    version="1.0.0",
)


class ChatRequest(BaseModel):
    message: str
    thread_id: str


class ChatResponse(BaseModel):
    response: str
    thread_id: str


@app.on_event("startup")
def startup():
    create_tables()


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        response = chat(message=request.message, thread_id=request.thread_id)
        return ChatResponse(response=response, thread_id=request.thread_id)
    except Exception as e:
        # Print full error details to terminal
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
def root():
    return {"status": "running"}