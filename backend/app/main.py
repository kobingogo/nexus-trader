from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import market, ai, anomaly, review, watchlist, llm

app = FastAPI(
    title="NEXUS Trader API",
    description="Backend API for NEXUS Trader (A-Share Edition)",
    version="1.0.0"
)

# Global Timeout for blocking operations (e.g. akshare/requests)
import socket
socket.setdefaulttimeout(15)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(market.router, prefix="/api/v1/market", tags=["Market Data"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI Services"])
app.include_router(anomaly.router, prefix="/api/v1/anomaly", tags=["Anomaly Detection"])
app.include_router(review.router, prefix="/api/v1/review", tags=["Daily Review"])
app.include_router(review.router, prefix="/api/v1/review", tags=["Daily Review"])
app.include_router(watchlist.router, prefix="/api/v1/watchlist", tags=["Watchlist"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["LLM Management"])
from app.routers import market_sentiment, logic_chain
app.include_router(market_sentiment.router, prefix="/api/v1/market", tags=["Market Sentiment"])
app.include_router(logic_chain.router, prefix="/api/v1/logic", tags=["Logic Chain"])

@app.get("/")
def read_root():
    return {"message": "Welcome to NEXUS Trader API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
