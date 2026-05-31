"""LLM Analysis Service - Orchestrates LLM-based stock analysis with tool calling.

This service follows the Strategy pattern for LLM providers and uses
tool calling to retrieve stock data from Redis cache.
"""
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from openai import OpenAI

from .llm_tools import StockDataTools, get_tool_definitions
from .llm_analysis_schemas import LLM_ANALYSIS_JSON_SCHEMA, LLMAnalysisResult

logger = logging.getLogger(__name__)

ANALYSIS_SYSTEM_PROMPT = """You are InvestingIQ, an expert financial analyst AI. Your task is to provide comprehensive stock analysis by gathering data using the available tools and then synthesizing insights.

## Your Analysis Process:
1. First, gather all available data using the provided tools
2. Analyze the data from multiple perspectives (technical, fundamental, sentiment)
3. Generate price predictions based on the analysis
4. Provide a clear investment recommendation

## Guidelines:
- Be objective and data-driven in your analysis
- Consider both bullish and bearish scenarios
- Highlight key risks and uncertainties
- Provide specific price levels for support, resistance, and targets
- Always include a disclaimer that this is not financial advice

## Tool Usage:
- Use get_stock_prices to analyze price trends and technical patterns
- Use get_company_info for fundamental analysis
- Use get_news_articles for sentiment analysis
- Use get_earnings_data for earnings assessment

Analyze the stock thoroughly and provide your complete analysis in the structured format."""


class BaseLLMAnalyzer(ABC):
    """Abstract base class for LLM analyzers."""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or self.default_model
        self._tools = StockDataTools()
        self._client = self._create_client()
    
    @property
    @abstractmethod
    def default_model(self) -> str:
        pass
    
    @property
    @abstractmethod
    def base_url(self) -> str:
        pass
    
    def _create_client(self) -> OpenAI:
        return OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def analyze(self, ticker: str) -> dict:
        """Run complete analysis for a stock ticker."""
        logger.info(f"Starting LLM analysis for {ticker}")
        
        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": f"Please analyze the stock {ticker} comprehensively. Start by gathering data using the available tools, then provide your complete analysis."}
        ]
        
        tool_definitions = get_tool_definitions()
        gathered_data = {}
        max_tool_rounds = 5
        
        for round_num in range(max_tool_rounds):
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tool_definitions,
                tool_choice="auto" if round_num < max_tool_rounds - 1 else "none",
            )
            
            assistant_message = response.choices[0].message
            messages.append(assistant_message.model_dump())
            
            if not assistant_message.tool_calls:
                break
            
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                result = self._tools.execute_tool(tool_name, tool_args)
                
                if result.success:
                    gathered_data[tool_name] = result.data
                
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result.data if result.success else {"error": result.error}, default=str)
                }
                messages.append(tool_response)
        
        return self._generate_structured_analysis(ticker, messages, gathered_data)
    
    def _generate_structured_analysis(self, ticker: str, messages: list, gathered_data: dict) -> dict:
        """Generate structured analysis output."""
        messages.append({
            "role": "user",
            "content": "Now provide your complete analysis in the structured JSON format. Include all sections: technical, fundamental, sentiment, prediction, and recommendation."
        })
        
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": LLM_ANALYSIS_JSON_SCHEMA
                }
            )
            
            analysis_json = json.loads(response.choices[0].message.content)
            analysis_json["ticker"] = ticker.upper()
            analysis_json["analysis_timestamp"] = datetime.utcnow().isoformat()
            
            return {
                "success": True,
                "analysis": analysis_json,
                "gathered_data": gathered_data,
            }
            
        except Exception as e:
            logger.error(f"Failed to generate structured analysis: {e}")
            return self._fallback_analysis(ticker, messages, gathered_data, str(e))
    
    def _fallback_analysis(self, ticker: str, messages: list, gathered_data: dict, error: str) -> dict:
        """Fallback to unstructured analysis if structured fails."""
        try:
            messages.append({
                "role": "user",
                "content": "Please provide your analysis as a JSON object with keys: technical, fundamental, sentiment, prediction, recommendation. Each should contain relevant analysis."
            })
            
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            
            content = response.choices[0].message.content
            
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            
            analysis = json.loads(content)
            analysis["ticker"] = ticker.upper()
            analysis["analysis_timestamp"] = datetime.utcnow().isoformat()
            analysis["_fallback"] = True
            
            return {
                "success": True,
                "analysis": analysis,
                "gathered_data": gathered_data,
            }
            
        except Exception as fallback_error:
            logger.error(f"Fallback analysis also failed: {fallback_error}")
            return {
                "success": False,
                "error": f"Primary: {error}, Fallback: {str(fallback_error)}",
                "gathered_data": gathered_data,
            }


class OpenAIAnalyzer(BaseLLMAnalyzer):
    """OpenAI-based analyzer."""
    
    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1"


class AnthropicAnalyzer(BaseLLMAnalyzer):
    """Anthropic-based analyzer (via OpenAI-compatible endpoint)."""
    
    @property
    def default_model(self) -> str:
        return "claude-haiku-4-5"
    
    @property
    def base_url(self) -> str:
        return "https://api.anthropic.com/v1"
    
    def _create_client(self) -> OpenAI:
        from anthropic import Anthropic
        return Anthropic(api_key=self.api_key)
    
    def analyze(self, ticker: str) -> dict:
        """Anthropic-specific analysis using native client."""
        logger.info(f"Starting Anthropic analysis for {ticker}")
        
        tool_definitions = self._convert_tools_to_anthropic()
        gathered_data = {}
        
        messages = [
            {"role": "user", "content": f"Please analyze the stock {ticker} comprehensively. Start by gathering data using the available tools, then provide your complete analysis."}
        ]
        
        max_tool_rounds = 5
        
        for round_num in range(max_tool_rounds):
            response = self._client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=ANALYSIS_SYSTEM_PROMPT,
                tools=tool_definitions,
                messages=messages,
            )
            
            if response.stop_reason == "end_turn":
                text_content = next((b.text for b in response.content if hasattr(b, 'text')), "")
                return self._parse_anthropic_response(ticker, text_content, gathered_data)
            
            tool_uses = [b for b in response.content if b.type == "tool_use"]
            if not tool_uses:
                text_content = next((b.text for b in response.content if hasattr(b, 'text')), "")
                return self._parse_anthropic_response(ticker, text_content, gathered_data)
            
            messages.append({"role": "assistant", "content": response.content})
            
            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_args = tool_use.input
                
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                result = self._tools.execute_tool(tool_name, tool_args)
                
                if result.success:
                    gathered_data[tool_name] = result.data
                
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": json.dumps(result.data if result.success else {"error": result.error}, default=str)
                })
            
            messages.append({"role": "user", "content": tool_results})
        
        return {"success": False, "error": "Max tool rounds exceeded", "gathered_data": gathered_data}
    
    def _convert_tools_to_anthropic(self) -> list:
        """Convert OpenAI tool format to Anthropic format."""
        openai_tools = get_tool_definitions()
        anthropic_tools = []
        
        for tool in openai_tools:
            func = tool["function"]
            anthropic_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"]
            })
        
        return anthropic_tools
    
    def _parse_anthropic_response(self, ticker: str, content: str, gathered_data: dict) -> dict:
        """Parse Anthropic response into structured format."""
        try:
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            analysis = json.loads(content)
            analysis["ticker"] = ticker.upper()
            analysis["analysis_timestamp"] = datetime.utcnow().isoformat()
            
            return {"success": True, "analysis": analysis, "gathered_data": gathered_data}
        except json.JSONDecodeError:
            return {
                "success": True,
                "analysis": {
                    "ticker": ticker.upper(),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "raw_analysis": content,
                    "_unstructured": True
                },
                "gathered_data": gathered_data,
            }


class OHMYGPTAnalyzer(BaseLLMAnalyzer):
    """OHMYGPT-based analyzer."""
    
    @property
    def default_model(self) -> str:
        return "gpt-4o-mini"
    
    @property
    def base_url(self) -> str:
        return "https://api.ohmygpt.com/v1"


class OpenRouterAnalyzer(BaseLLMAnalyzer):
    """OpenRouter-based analyzer."""
    
    @property
    def default_model(self) -> str:
        return "xiaomi/mimo-v2-flash:free"
    
    @property
    def base_url(self) -> str:
        return "https://openrouter.ai/api/v1"


class GoogleAnalyzer(BaseLLMAnalyzer):
    """Google Gemini-based analyzer using the native generateContent endpoint.

    Google's OpenAI-compatibility endpoint (/v1beta/openai) rejects the newer
    "AQ."-format API keys with 401, so this analyzer talks to the native
    Gemini REST API which accepts both legacy (AIza...) and new (AQ.) keys.
    """

    NATIVE_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    @property
    def default_model(self) -> str:
        return "gemini-3.1-flash-lite"

    @property
    def base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta/openai"

    def _create_client(self):
        # No SDK client; requests are made directly to the native REST endpoint.
        return None

    def _convert_tools_to_google(self) -> list:
        """Convert OpenAI tool definitions to Google functionDeclarations."""
        declarations = []
        for tool in get_tool_definitions():
            func = tool["function"]
            declarations.append({
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"],
            })
        return [{"functionDeclarations": declarations}] if declarations else []

    def _post(self, contents: list, tools: list) -> dict:
        """Call the native generateContent endpoint and return parsed JSON."""
        import requests

        url = f"{self.NATIVE_BASE_URL}/{self.model}:generateContent"
        payload = {
            "contents": contents,
            "systemInstruction": {"parts": [{"text": ANALYSIS_SYSTEM_PROMPT}]},
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 4000},
        }
        if tools:
            payload["tools"] = tools

        response = requests.post(
            url,
            headers={"Content-Type": "application/json", "x-goog-api-key": self.api_key},
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
        return response.json()

    def analyze(self, ticker: str) -> dict:
        """Google-specific analysis using the native generateContent endpoint."""
        logger.info(f"Starting Google analysis for {ticker}")

        tools = self._convert_tools_to_google()
        gathered_data = {}
        contents = [{
            "role": "user",
            "parts": [{"text": f"Please analyze the stock {ticker} comprehensively. Start by gathering data using the available tools, then provide your complete analysis as JSON."}],
        }]

        max_tool_rounds = 5
        for _ in range(max_tool_rounds):
            result = self._post(contents, tools)
            candidates = result.get("candidates", [])
            if not candidates:
                break

            parts = candidates[0].get("content", {}).get("parts", [])
            function_calls = [p["functionCall"] for p in parts if "functionCall" in p]

            if not function_calls:
                text = next((p["text"] for p in parts if "text" in p), "")
                return self._parse_google_response(ticker, text, gathered_data)

            # Echo the model's function-call turn, then append tool results.
            contents.append({"role": "model", "parts": parts})
            response_parts = []
            for fc in function_calls:
                tool_name = fc["name"]
                tool_args = fc.get("args", {})
                logger.info(f"Executing tool: {tool_name} with args: {tool_args}")
                tool_result = self._tools.execute_tool(tool_name, tool_args)
                if tool_result.success:
                    gathered_data[tool_name] = tool_result.data
                response_parts.append({
                    "functionResponse": {
                        "name": tool_name,
                        "response": {
                            "result": tool_result.data if tool_result.success else {"error": tool_result.error}
                        },
                    }
                })
            contents.append({"role": "user", "parts": response_parts})

        # Final request forcing a textual JSON answer (no further tools).
        contents.append({
            "role": "user",
            "parts": [{"text": "Now provide your complete analysis as a JSON object with keys: technical, fundamental, sentiment, prediction, recommendation."}],
        })
        result = self._post(contents, tools=[])
        candidates = result.get("candidates", [])
        text = ""
        if candidates:
            text = next((p["text"] for p in candidates[0].get("content", {}).get("parts", []) if "text" in p), "")
        return self._parse_google_response(ticker, text, gathered_data)

    def _parse_google_response(self, ticker: str, content: str, gathered_data: dict) -> dict:
        """Parse the Gemini text response into structured analysis."""
        text = content.strip()
        if "```json" in text:
            start = text.find("```json") + 7
            text = text[start:text.find("```", start)].strip()
        elif "```" in text:
            start = text.find("```") + 3
            text = text[start:text.find("```", start)].strip()

        try:
            analysis = json.loads(text)
            analysis["ticker"] = ticker.upper()
            analysis["analysis_timestamp"] = datetime.utcnow().isoformat()
            return {"success": True, "analysis": analysis, "gathered_data": gathered_data}
        except json.JSONDecodeError:
            return {
                "success": True,
                "analysis": {
                    "ticker": ticker.upper(),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                    "raw_analysis": content,
                    "_unstructured": True,
                },
                "gathered_data": gathered_data,
            }


class LLMAnalyzerFactory:
    """Factory for creating LLM analyzer instances."""
    
    _analyzers = {
        "openai": OpenAIAnalyzer,
        "anthropic": AnthropicAnalyzer,
        "google": GoogleAnalyzer,
        "ohmygpt": OHMYGPTAnalyzer,
        "openrouter": OpenRouterAnalyzer,
    }
    
    @classmethod
    def create(cls, provider: str, api_key: str, model: str = None) -> BaseLLMAnalyzer:
        """Create an analyzer instance."""
        provider_lower = provider.lower()
        if provider_lower not in cls._analyzers:
            raise ValueError(f"Unsupported provider: {provider}")
        
        return cls._analyzers[provider_lower](api_key=api_key, model=model)
    
    @classmethod
    def get_supported_providers(cls) -> list:
        return list(cls._analyzers.keys())
