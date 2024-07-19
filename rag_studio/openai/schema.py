from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from openai.types.chat import ChatCompletionMessageParam

from llama_index.llms.vllm import Vllm

import logging

logger = logging.getLogger(__name__)


class ResponseFormat(BaseModel):
    type: Literal["json_object", "text"]


class StreamOptions(BaseModel):
    include_usage: Optional[bool]


class ChatCompletionNamedFunction(BaseModel):
    name: str


class ChatCompletionNamedToolChoiceParam(BaseModel):
    function: ChatCompletionNamedFunction
    type: Literal["function"] = "function"


class FunctionDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None


class ChatCompletionToolsParam(BaseModel):
    type: Literal["function"] = "function"
    function: FunctionDefinition


class CommonRequestFields(BaseModel):
    model: str
    best_of: Optional[int] = None
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    logprobs: Optional[int] = None
    max_tokens: Optional[int] = None
    n: int = 1
    presence_penalty: Optional[float] = 0.0
    stop: Optional[Union[str, List[str]]] = Field(default_factory=list)
    stream: Optional[bool] = False
    stream_options: Optional[StreamOptions] = None
    suffix: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    user: Optional[str] = None

    response_format: Optional[ResponseFormat] = None

    def set_model_params_from_request(self, llm: Vllm):
        """Set the model parameters from the request data."""
        # temperature: float = 1.0,
        # n: int = 1,
        # presence_penalty: float = 0.0,
        # frequency_penalty: float = 0.0,
        # top_p: float = 1.0,
        # stop: Optional[List[str]] = None,
        # max_tokens ->    # max_new_tokens: int = 512,
        # logprobs: Optional[int] = None,
        # NOTE: cannot set model
        if self.model != "rag_model":
            return "No ability to change model from rag_model - this has been baked into the API"
        logger.info(
            "Setting model params from request data: %s",
            self.model_dump(
                exclude_unset=True, exclude={"messages", "prompt", "model"}
            ),
        )
        if self.temperature:
            llm.temperature = self.temperature
        else:
            llm.temperature = 0.7
        if self.n and self.n != 1:
            logger.error("Currently returning n > 1 completions is unsupported")
            # llm.n = self.n
            return "Currently returning n > 1 completions is unsupported"
        if self.presence_penalty:
            llm.presence_penalty = self.presence_penalty
        else:
            llm.presence_penalty = 0.0
        if self.frequency_penalty:
            llm.frequency_penalty = self.frequency_penalty
        else:
            llm.frequency_penalty = 0.0
        if self.top_p:
            llm.top_p = self.top_p
        else:
            llm.top_p = 1.0
        if self.stop:
            llm.stop = self.stop
        else:
            llm.stop = []
        if self.max_tokens:
            llm.max_new_tokens = self.max_tokens
        else:
            llm.max_new_tokens = 512
        if self.logprobs:
            # llm.logprobs = self.logprobs
            logger.error("Currently logprobs output is unsupported")
            return "Currently logprobs output is unsupported"
        if self.response_format and self.response_format.type != "text":
            logger.error("Only text response format is supported")
            return "Only text response format is supported"
        if self.logit_bias:
            logger.error("Currently logit_bias is unsupported")
            return "Currently logit_bias is unsupported"
        if self.stream:
            logger.error("Currently streaming response is unsupported")
            return "Currently streaming response is unsupported"
        # Additionally the old completions API supports:
        # best_of: Optional[int] = None,
        if self.best_of:
            llm.best_of = self.best_of
        else:
            llm.best_of = 1

        logger.info(
            "LLM settings after setting from request: %s",
            {k: v for k, v in llm.__dict__.items() if not k.startswith("_")},
        )
        return None


class ChatCompletionRequest(CommonRequestFields):
    messages: List[ChatCompletionMessageParam]
    top_logprobs: Optional[int] = 0
    tools: Optional[List[ChatCompletionToolsParam]] = None
    tool_choice: Optional[
        Union[Literal["none"], ChatCompletionNamedToolChoiceParam]
    ] = "none"

    def set_model_params_from_request(self, llm: Vllm):
        if self.tools or self.tool_choice != "none":
            logger.error("Currently use of tools / functions is unsupported")
            return "Currently use of tools / functions is unsupported"
        if self.top_logprobs:
            logger.error("Currently logprobs output is unsupported")
            return "Currently logprobs output is unsupported"
        return super().set_model_params_from_request(llm)


class CompletionRequest(CommonRequestFields):
    prompt: Union[List[int], List[List[int]], str, List[str]]
    echo: Optional[bool] = False
