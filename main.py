import traceback
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from database import create_tables
from agent import chat

# Initialize FastAPI application
app = FastAPI(
    title="AI User Management System",
    version="1.0.0",
)


# Request model for chat endpoint
class ChatRequest(BaseModel):
    message: str
    thread_id: str


# Response model returned by the API
class ChatResponse(BaseModel):
    response: str
    thread_id: str


# Run setup tasks when the API starts
@app.on_event("startup")
def startup():
    create_tables()


# Main endpoint that receives user messages and returns the AI response
@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        response = chat(message=request.message, thread_id=request.thread_id)
        return ChatResponse(response=response, thread_id=request.thread_id)

    except Exception as e:
        # Print full traceback in the server logs for debugging
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Simple health check endpoint
@app.get("/")
def root():
    return {"status": "running"}