from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import json
from pydantic import BaseModel
from google import genai
from google.genai import types

class ToolCall(BaseModel):
    name: str
    arguments: dict
    raw_call: Any  # Keep the original provider's tool call object for passing back

class LLMResponse(BaseModel):
    text: str
    function_calls: List[ToolCall] = []
    raw_response: Any  # Keep the original response object

class LLMProvider(ABC):
    @abstractmethod
    def __init__(self, api_key: str):
        pass

    @abstractmethod
    async def generate_content(
        self, 
        model: str, 
        system_instruction: str,
        messages: List[Dict[str, str]], 
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        """Generates content given a history of standard messages [{"role": "user"|"model", "content": "..."}]"""
        pass

    @abstractmethod
    async def generate_with_tool_result(
        self,
        model: str,
        system_instruction: str,
        messages: List[Dict[str, str]],
        previous_response: LLMResponse,
        tool_results: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        """Generates content after a tool call.
        tool_results: [{"name": "tool_name", "result": "string_result"}]
        """
        pass

    @abstractmethod
    async def embed_content(self, model: str, text: str) -> List[float]:
        pass

class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)

    def _format_messages(self, messages: List[Dict[str, str]], new_prompt: Optional[str] = None) -> List[Any]:
        formatted = []
        for msg in messages:
            # Handle standard text messages
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content", msg.get("text", ""))
            formatted.append({"role": role, "parts": [{"text": content}]})
        
        if new_prompt:
            formatted.append({"role": "user", "parts": [{"text": new_prompt}]})
        return formatted

    async def generate_content(
        self, 
        model: str, 
        system_instruction: str,
        messages: List[Dict[str, str]], 
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        
        formatted_history = self._format_messages(messages)
        
        config_dict = {"system_instruction": system_instruction, "max_output_tokens": 1500}
        if tools:
            config_dict["tools"] = tools

        response = self.client.models.generate_content(
            model=model,
            contents=formatted_history,
            config=config_dict
        )
        
        function_calls = []
        if response.function_calls:
            for fc in response.function_calls:
                function_calls.append(ToolCall(name=fc.name, arguments=fc.args, raw_call=fc))
                
        return LLMResponse(
            text=response.text or "",
            function_calls=function_calls,
            raw_response=response
        )

    async def generate_with_tool_result(
        self,
        model: str,
        system_instruction: str,
        messages: List[Dict[str, str]],
        previous_response: LLMResponse,
        tool_results: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        
        formatted_history = self._format_messages(messages)
        
        # Append the previous AI response containing the function call
        formatted_history.append(previous_response.raw_response.candidates[0].content)
        
        # Append the tool results
        parts = []
        for tr in tool_results:
            func_resp_part = types.Part.from_function_response(
                name=tr["name"],
                response={"result": tr["result"]}
            )
            parts.append(func_resp_part)
            
        formatted_history.append({"role": "user", "parts": parts})
        
        # Generate final response
        config_dict = {"system_instruction": system_instruction, "max_output_tokens": 1500}
        if tools:
            config_dict["tools"] = tools

        response = self.client.models.generate_content(
            model=model,
            contents=formatted_history,
            config=config_dict
        )
        
        return LLMResponse(
            text=response.text or "",
            function_calls=[],
            raw_response=response
        )

    async def embed_content(self, model: str, text: str) -> List[float]:
        response = self.client.models.embed_content(
            model=model,
            contents=text
        )
        return response.embeddings[0].values

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _convert_tools(self, tools: Optional[List[Any]]) -> Optional[List[Dict[str, Any]]]:
        if not tools:
            return None

        SCHEMAS: Dict[str, Dict] = {
            "roll_d20": {
                "type": "function",
                "function": {
                    "name": "roll_d20",
                    "description": "Rolls a 20-sided die for a risky player action per the Dice Protocol.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "difficulty_class": {
                                "type": "integer",
                                "description": "Target DC: 8=Very Easy, 10=Easy, 12=Moderate, 15=Hard, 18=Very Hard, 20=Nearly Impossible.",
                            }
                        },
                        "required": ["difficulty_class"],
                    },
                },
            },
            "apply_vitals": {
                "type": "function",
                "function": {
                    "name": "apply_vitals",
                    "description": "Updates Subject 814's health and stress. Call instead of writing [Health: X% | Stress: Y%].",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "health_delta": {"type": "integer", "description": "Health change (-100 to +100). Negative = damage."},
                            "stress_delta": {"type": "integer", "description": "Stress change (-100 to +100). Positive = more stress."},
                        },
                        "required": ["health_delta", "stress_delta"],
                    },
                },
            },
            "add_item": {
                "type": "function",
                "function": {
                    "name": "add_item",
                    "description": "Adds an item to Subject 814's inventory (max 4 slots).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string", "description": "Descriptive item name."},
                        },
                        "required": ["item_name"],
                    },
                },
            },
            "remove_item": {
                "type": "function",
                "function": {
                    "name": "remove_item",
                    "description": "Removes an item from Subject 814's inventory.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item_name": {"type": "string", "description": "Exact item name as in inventory."},
                        },
                        "required": ["item_name"],
                    },
                },
            },
            "move_to_location": {
                "type": "function",
                "function": {
                    "name": "move_to_location",
                    "description": "Updates current location when player moves to a new zone. Use canonical names from institute_map.md.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location_name": {"type": "string", "description": "Canonical zone name."},
                        },
                        "required": ["location_name"],
                    },
                },
            },
            "discover_lore": {
                "type": "function",
                "function": {
                    "name": "discover_lore",
                    "description": "Marks a lore fragment as discovered. Use exact IDs from lore_fragments.md.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "fragment_id": {"type": "string", "description": "Fragment ID (e.g. 'intake_file_814')."},
                        },
                        "required": ["fragment_id"],
                    },
                },
            },
            "advance_escape_stage": {
                "type": "function",
                "function": {
                    "name": "advance_escape_stage",
                    "description": "Advances escape progress by one stage (0→4). Stage 4 = game won.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            },
        }

        result = []
        for t in tools:
            name = getattr(t, "__name__", None)
            if name in SCHEMAS:
                result.append(SCHEMAS[name])
        return result or None


    async def generate_content(
        self, 
        model: str, 
        system_instruction: str,
        messages: List[Dict[str, str]], 
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        
        if model == "gemini-2.5-flash":
            model = "gpt-4o-mini"
            
        formatted_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg.get("content", msg.get("text", ""))
            formatted_messages.append({"role": role, "content": content})

        openai_tools = self._convert_tools(tools)
        
        kwargs = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": 1500,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await self.client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        function_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                if tc.type == "function":
                    args = json.loads(tc.function.arguments)
                    function_calls.append(ToolCall(
                        name=tc.function.name, 
                        arguments=args, 
                        raw_call=tc
                    ))
                    
        return LLMResponse(
            text=message.content or "",
            function_calls=function_calls,
            raw_response=response
        )

    async def generate_with_tool_result(
        self,
        model: str,
        system_instruction: str,
        messages: List[Dict[str, str]],
        previous_response: LLMResponse,
        tool_results: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        
        if model == "gemini-2.5-flash":
            model = "gpt-4o-mini"
            
        formatted_messages = [{"role": "system", "content": system_instruction}]
        for msg in messages:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg.get("content", msg.get("text", ""))
            formatted_messages.append({"role": role, "content": content})
            
        # Append the assistant message that included the tool_calls
        assistant_msg = previous_response.raw_response.choices[0].message
        # Dump the message to a dictionary, ensuring compatibility with OpenAI's API
        formatted_messages.append(assistant_msg.model_dump(exclude_none=True))
        
        # Append the tool results
        for tr in tool_results:
            tool_call_id = None
            for tc in assistant_msg.tool_calls:
                if tc.function.name == tr["name"]:
                    tool_call_id = tc.id
                    break
                    
            if tool_call_id:
                formatted_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tr["name"],
                    "content": tr["result"]
                })

        openai_tools = self._convert_tools(tools)
        kwargs = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": 1500,
        }
        if openai_tools:
            kwargs["tools"] = openai_tools

        response = await self.client.chat.completions.create(**kwargs)
        
        return LLMResponse(
            text=response.choices[0].message.content or "",
            function_calls=[],
            raw_response=response
        )

    async def embed_content(self, model: str, text: str) -> List[float]:
        try:
            # Map generic or google embedding model name to OpenAI
            if model == "text-embedding-004" or model == "gemini-2.5-flash":
                model = "text-embedding-3-small"
                
            response = await self.client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠️ Embeddings failed: {e}. Falling back to zero-vector.")
            return [0.0] * 1536

class OpenRouterProvider(OpenAIProvider):
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    async def generate_content(
        self, 
        model: str, 
        system_instruction: str,
        messages: List[Dict[str, str]], 
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        # Default fallback for OpenRouter
        if model == "gemini-2.5-flash":
            model = "openai/gpt-4o-mini"
        return await super().generate_content(model, system_instruction, messages, tools)

    async def generate_with_tool_result(
        self,
        model: str,
        system_instruction: str,
        messages: List[Dict[str, str]],
        previous_response: LLMResponse,
        tool_results: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None
    ) -> LLMResponse:
        if model == "gemini-2.5-flash":
            model = "openai/gpt-4o-mini"
        return await super().generate_with_tool_result(model, system_instruction, messages, previous_response, tool_results, tools)

    async def embed_content(self, model: str, text: str) -> List[float]:
        try:
            # Map embedding model to OpenRouter syntax
            if model == "text-embedding-004" or model == "gemini-2.5-flash":
                model = "openai/text-embedding-3-small"
            return await super().embed_content(model, text)
        except Exception as e:
            print(f"⚠️ OpenRouter embeddings failed (unsupported): {e}. Falling back to zero-vector.")
            return [0.0] * 1536
