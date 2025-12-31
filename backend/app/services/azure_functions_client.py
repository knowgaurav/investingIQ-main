"""Azure Functions client for triggering parallel analysis."""
import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def trigger_analysis(ticker: str, task_id: str) -> dict:
    """
    Trigger Azure Functions orchestrator for parallel analysis.
    
    The orchestrator will:
    1. Fetch stock data and news in parallel
    2. Run sentiment, summary, insights in parallel
    3. Embed documents
    4. Save report
    """
    settings = get_settings()
    url = f"{settings.azure_functions_url}/api/analyze"
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, json={
                "ticker": ticker,
                "task_id": task_id
            })
            
            if response.status_code == 202:
                data = response.json()
                logger.info(f"Started Azure Functions orchestration for {ticker}: {data}")
                return {"status": "started", "instance_id": data.get("instance_id")}
            else:
                logger.error(f"Azure Functions error: {response.status_code} - {response.text}")
                return {"status": "error", "error": response.text}
                
    except Exception as e:
        logger.error(f"Failed to trigger Azure Functions: {e}")
        return {"status": "error", "error": str(e)}


async def check_orchestration_status(instance_id: str) -> dict:
    """Check status of an orchestration instance."""
    settings = get_settings()
    url = f"{settings.azure_functions_url}/runtime/webhooks/durabletask/instances/{instance_id}"
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            return response.json()
    except Exception as e:
        logger.error(f"Failed to check status: {e}")
        return {"status": "error", "error": str(e)}
