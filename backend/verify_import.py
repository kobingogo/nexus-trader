
import time
print("Importing app.routers.logic_chain...")
s = time.time()
from app.routers import logic_chain
print(f"Imported logic_chain in {time.time()-s:.4f}s")

print("Importing app.routers.market_sentiment...")
s = time.time()
from app.routers import market_sentiment
print(f"Imported market_sentiment in {time.time()-s:.4f}s")
