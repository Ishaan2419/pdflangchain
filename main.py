from fastapi import FastAPI
from model import ChatRequest
from service import ask_question


app=FastAPI()

@app.get("/")
def home():
    return {"message": "RAG API Running 🚀"}

@app.post("/chat")
def chat_api(request: ChatRequest):
    answer=ask_question(
        request.session_id,
        request.query
    )
    
    return{
        "session_id":request.session_id,
        "Question":request.query,
        "Answer":answer
    }