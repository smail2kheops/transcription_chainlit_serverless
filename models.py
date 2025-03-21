import pydantic

from pydantic_ai.messages import ModelMessage


class Messages(pydantic.BaseModel):
  messages: list[ModelMessage]
