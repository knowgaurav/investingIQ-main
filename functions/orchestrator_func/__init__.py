"""Analysis Orchestrator - Fan-out/Fan-in pattern for stock analysis.

Flow:
1. Fetch stock data + news (sequential)
2. Cache in Redis for LLM tool access
3. Fan-out: ML analysis + LLM analysis (parallel)
4. Fan-in: Aggregate results
"""
import azure.durable_functions as df


def orchestrator_function(context: df.DurableOrchestrationContext):
    input_data = context.get_input()
    ticker = input_data["ticker"]
    task_id = input_data["task_id"]
    llm_config = input_data.get("llm_config")
    
    # Step 1: Fetch data (sequential)
    fetch_result = yield context.call_activity("activity_fetch_data", {
        "ticker": ticker,
        "task_id": task_id,
    })
    
    stock_data = fetch_result["stock_data"]
    news_data = fetch_result["news_data"]
    
    # Step 2: Cache in Redis
    yield context.call_activity("activity_cache_data", {
        "ticker": ticker,
        "stock_data": stock_data,
        "news_data": news_data,
    })
    
    # Step 3: Fan-out to ML and LLM analysis
    parallel_tasks = []
    
    # ML Analysis (always)
    parallel_tasks.append(context.call_activity("activity_ml_analysis", {
        "ticker": ticker,
        "task_id": task_id,
        "stock_data": stock_data,
        "news_data": news_data,
    }))
    
    # LLM Analysis (only if llm_config present)
    if llm_config:
        parallel_tasks.append(context.call_activity("activity_llm_analysis", {
            "ticker": ticker,
            "task_id": task_id,
            "llm_config": llm_config,
        }))
    
    # Step 4: Fan-in
    results = yield context.task_all(parallel_tasks)
    
    # Step 5: Aggregate
    aggregated = yield context.call_activity("activity_aggregate", {
        "ticker": ticker,
        "task_id": task_id,
        "stock_data": stock_data,
        "news_data": news_data,
        "analysis_results": results,
        "llm_enabled": llm_config is not None,
    })
    
    return aggregated


main = df.Orchestrator.create(orchestrator_function)
