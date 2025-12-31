"""MLflow tracking utilities for LLM operations."""
import hashlib
import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Optional

import mlflow
from mlflow.entities import RunStatus

from app.config import get_settings

logger = logging.getLogger(__name__)


class MLflowTracker:
    """MLflow tracker for LLM calls and prompt versioning."""
    
    def __init__(self):
        """Initialize MLflow tracker with settings."""
        settings = get_settings()
        self._tracking_uri = settings.mlflow_tracking_uri
        self._experiment_name = settings.mlflow_experiment_name
        self._initialized = False
        self._prompt_versions: Dict[str, str] = {}
    
    def _ensure_initialized(self) -> bool:
        """Ensure MLflow is initialized. Returns True if successful."""
        if self._initialized:
            return True
        
        try:
            mlflow.set_tracking_uri(self._tracking_uri)
            mlflow.set_experiment(self._experiment_name)
            self._initialized = True
            logger.info(f"MLflow initialized with URI: {self._tracking_uri}")
            return True
        except Exception as e:
            logger.warning(f"Failed to initialize MLflow: {e}")
            return False
    
    def create_experiment(self, experiment_name: str) -> Optional[str]:
        """
        Create or get an experiment for a specific analysis type.
        
        Args:
            experiment_name: Name of the experiment (e.g., "sentiment-analysis")
            
        Returns:
            Experiment ID or None if failed
        """
        if not self._ensure_initialized():
            return None
        
        try:
            experiment = mlflow.get_experiment_by_name(experiment_name)
            if experiment:
                return experiment.experiment_id
            
            experiment_id = mlflow.create_experiment(experiment_name)
            logger.info(f"Created MLflow experiment: {experiment_name}")
            return experiment_id
        except Exception as e:
            logger.warning(f"Failed to create experiment {experiment_name}: {e}")
            return None
    
    def _get_prompt_version(self, prompt_template: str) -> str:
        """Generate a version hash for a prompt template."""
        return hashlib.md5(prompt_template.encode()).hexdigest()[:8]
    
    def log_prompt_template(
        self,
        template_name: str,
        template_content: str,
        tags: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Log a prompt template with versioning.
        
        Args:
            template_name: Name identifier for the template
            template_content: The actual prompt template text
            tags: Optional additional tags
            
        Returns:
            Version hash of the template
        """
        if not self._ensure_initialized():
            return None
        
        try:
            version = self._get_prompt_version(template_content)
            self._prompt_versions[template_name] = version
            
            with mlflow.start_run(run_name=f"prompt-{template_name}-{version}"):
                mlflow.log_param("template_name", template_name)
                mlflow.log_param("template_version", version)
                mlflow.log_text(template_content, f"prompts/{template_name}.txt")
                
                if tags:
                    mlflow.set_tags(tags)
                
                mlflow.set_tag("type", "prompt_template")
            
            logger.debug(f"Logged prompt template: {template_name} v{version}")
            return version
        except Exception as e:
            logger.warning(f"Failed to log prompt template: {e}")
            return None
    
    @contextmanager
    def track_llm_call(
        self,
        operation: str,
        model_name: str,
        prompt_template: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager to track an LLM call.
        
        Args:
            operation: Type of operation (e.g., "chat", "sentiment", "summarize")
            model_name: Name of the LLM model used
            prompt_template: Optional prompt template name for tracking
            metadata: Optional additional metadata
            
        Yields:
            Dict to store metrics (input_tokens, output_tokens, etc.)
        """
        metrics = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
            "success": True,
            "error": None
        }
        
        start_time = time.time()
        
        try:
            yield metrics
        except Exception as e:
            metrics["success"] = False
            metrics["error"] = str(e)
            raise
        finally:
            latency_ms = (time.time() - start_time) * 1000
            metrics["latency_ms"] = latency_ms
            
            self._log_llm_metrics(
                operation=operation,
                model_name=model_name,
                prompt_template=prompt_template,
                metrics=metrics,
                metadata=metadata
            )
    
    def _log_llm_metrics(
        self,
        operation: str,
        model_name: str,
        prompt_template: Optional[str],
        metrics: Dict[str, Any],
        metadata: Optional[Dict[str, Any]]
    ):
        """Log LLM call metrics to MLflow."""
        if not self._ensure_initialized():
            return
        
        try:
            run_name = f"{operation}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            with mlflow.start_run(run_name=run_name):
                # Log parameters
                mlflow.log_param("operation", operation)
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("success", metrics.get("success", True))
                
                if prompt_template:
                    mlflow.log_param("prompt_template", prompt_template)
                    version = self._prompt_versions.get(prompt_template)
                    if version:
                        mlflow.log_param("prompt_version", version)
                
                # Log metrics
                mlflow.log_metric("input_tokens", metrics.get("input_tokens", 0))
                mlflow.log_metric("output_tokens", metrics.get("output_tokens", 0))
                mlflow.log_metric("total_tokens", metrics.get("total_tokens", 0))
                mlflow.log_metric("latency_ms", metrics.get("latency_ms", 0))
                mlflow.log_metric("cost_usd", metrics.get("cost", 0.0))
                
                # Log tags
                mlflow.set_tag("type", "llm_call")
                mlflow.set_tag("operation", operation)
                
                if metrics.get("error"):
                    mlflow.set_tag("error", metrics["error"])
                
                # Log additional metadata
                if metadata:
                    for key, value in metadata.items():
                        if isinstance(value, (int, float)):
                            mlflow.log_metric(f"meta_{key}", value)
                        else:
                            mlflow.log_param(f"meta_{key}", str(value)[:250])
                
        except Exception as e:
            logger.warning(f"Failed to log LLM metrics to MLflow: {e}")
    
    def log_llm_call(
        self,
        operation: str,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        cost: float = 0.0,
        prompt_template: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Directly log an LLM call (alternative to context manager).
        
        Args:
            operation: Type of operation
            model_name: Name of the LLM model
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Latency in milliseconds
            cost: Cost in USD
            prompt_template: Optional prompt template name
            success: Whether the call succeeded
            error: Error message if failed
            metadata: Optional additional metadata
        """
        metrics = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "cost": cost,
            "success": success,
            "error": error
        }
        
        self._log_llm_metrics(
            operation=operation,
            model_name=model_name,
            prompt_template=prompt_template,
            metrics=metrics,
            metadata=metadata
        )


# Singleton instance
_mlflow_tracker: Optional[MLflowTracker] = None


def get_mlflow_tracker() -> MLflowTracker:
    """Get or create the MLflow tracker singleton."""
    global _mlflow_tracker
    if _mlflow_tracker is None:
        _mlflow_tracker = MLflowTracker()
    return _mlflow_tracker
