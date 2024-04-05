from fastapi import FastAPI
from uvicorn import run
from ai_aroma import AIAroma
from pydantic import BaseModel
import asyncio

class Message(BaseModel):
    id: str
    content: str

app = FastAPI()

ai_aroma_object = AIAroma()

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

@app.post("/send_message")
async def send_message(message:Message):
    print(ai_aroma_object.dict)
    message = dict(message)
    result = await ai_aroma_object.on_message(message)
    print(result)
    return result

# if __name__ == "__main__":
#   print('app running')    
#   run(app, host="127.0.0.1", port=8010)