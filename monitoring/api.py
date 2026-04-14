# monitoring/api.py
from fastapi import FastAPI
import uvicorn
from utils.config import CONFIG
from utils.logger import log
from execution.ib_broker import IBBroker # For a quick connectivity check

app = FastAPI()
broker = IBBroker()

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "ok", "bot_name": CONFIG['general']['bot_name']}

@app.get("/account")
async def account_info():
    """Returns current account information."""
    try:
        broker.connect()
        info = broker.get_account_info()
        broker.disconnect()
        return {"status": "success", "data": info}
    except Exception as e:
        log.error(f"Failed to fetch account info for API: {e}")
        return {"status": "error", "message": str(e)}

def run_api():
    """Starts the FastAPI server."""
    port = CONFIG['monitoring']['health_check_port']
    log.info(f"Starting health check API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")