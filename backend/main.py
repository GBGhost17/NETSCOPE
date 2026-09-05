"""FastAPI main application"""
from fastapi import FastAPI

app = FastAPI(title="NetScope API", version="1.0.0")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NetScope API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
