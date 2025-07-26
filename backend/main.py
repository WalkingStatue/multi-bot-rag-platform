from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Multi-Bot RAG Platform API",
    description="Backend API for the Multi-Bot RAG Platform",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker health checks"""
    return JSONResponse(content={"status": "healthy"})

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Multi-Bot RAG Platform API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)