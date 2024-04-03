from fastapi import FastAPI
from uvicorn import run

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from FastAPI!"}

# if __name__ == "__main__":
#   print('app running')    
#   run(app, host="localhost", port=8010)