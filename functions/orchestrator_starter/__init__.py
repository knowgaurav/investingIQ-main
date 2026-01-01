"""HTTP Starter for Analysis Orchestrator."""
import logging
import azure.functions as func
import azure.durable_functions as df

logger = logging.getLogger(__name__)


async def main(req: func.HttpRequest, starter: str) -> func.HttpResponse:
    """HTTP trigger to start the analysis orchestration."""
    client = df.DurableOrchestrationClient(starter)
    
    try:
        body = req.get_json()
        ticker = body.get("ticker", "").upper().strip()
        task_id = body.get("task_id")
        llm_config = body.get("llm_config")
        
        if not ticker:
            return func.HttpResponse("Missing ticker", status_code=400)
        
        instance_id = await client.start_new(
            "orchestrator_func",
            client_input={
                "ticker": ticker,
                "task_id": task_id,
                "llm_config": llm_config,
            }
        )
        
        logger.info(f"Started orchestration {instance_id} for {ticker}")
        return client.create_check_status_response(req, instance_id)
        
    except Exception as e:
        logger.error(f"Failed to start orchestration: {e}")
        return func.HttpResponse(str(e), status_code=500)
