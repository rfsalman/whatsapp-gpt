

import openai
from typing import TypeVar, Type
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
  BaseMessage,
  HumanMessage,
)
from langchain.prompts import (
  SystemMessagePromptTemplate, 
  ChatPromptTemplate,
  PromptTemplate
)
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import (
  AIMessage,
  HumanMessage,
)
from pydantic import BaseModel

from src.config import config
from src.helpers.action_triggers import ActionTriggers
from .schemas import ChatCompletionMessageSchema, ChatCompletionOptionsSchema, ChatCompletionResponseSchema

openai.api_key = config.OPENAI_API_KEY

T = TypeVar("T", bound=BaseModel)

async def create_full_chat_completion(
  message_history: list[AIMessage | HumanMessage],
  prompt: str,
  additional_data: dict = {}
) -> str:
  try:
    chat_openai = ChatOpenAI(
      model="gpt-3.5-turbo", 
      temperature=0.2,
      openai_api_key=config.OPENAI_API_KEY
    )

    system_message_prompt = SystemMessagePromptTemplate.from_template(
      prompt
    )

    messages = [
      system_message_prompt,
      *message_history
    ]

    chat_prompt_template = ChatPromptTemplate.from_messages(messages)

    chat_prompt = chat_prompt_template.format_messages(**additional_data)

    print("System Message", chat_prompt[0].content)

    chat_result = await chat_openai.apredict_messages(chat_prompt)

    return chat_result
  except Exception as e:
    print("Error: ", e)
    return ""
  
async def create_parsed_chat_completion(
  message_history: list[AIMessage | HumanMessage],
  prompt: str,
  pydantic_model: Type[T],
  additional_data: dict = {}
) -> T:
  try:
    chat_openai = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
    output_parser = PydanticOutputParser(
      pydantic_object=pydantic_model
    )
    
    system_message_prompt = SystemMessagePromptTemplate.from_template(
      prompt
    )

    messages = [
      system_message_prompt,
      *message_history
    ]

    chat_prompt_template = ChatPromptTemplate.from_messages(messages)
    chat_prompt = chat_prompt_template.format_messages(
      **additional_data, 
      format_instructions=output_parser.get_format_instructions()
    )

    chat_result = await chat_openai.apredict_messages(chat_prompt)

    parsed_result = output_parser.parse(chat_result.action)

    return AIMessage(content=parsed_result.summary)
  except Exception as e:
    print("Error at create_parsed_chat_completion", e)
    return AIMessage(content="The system has encountered an error")

def create_chat_message(message: ChatCompletionMessageSchema) -> HumanMessage | AIMessage | None:
  if message.role == "assistant":
    return AIMessage(
      content=message.content
    )
  
  if message.role == "user":
    return HumanMessage(
      content=message.content
    )
  
  return None

def create_chat_completion(messages: list[ChatCompletionMessageSchema], options: ChatCompletionOptionsSchema) -> ChatCompletionResponseSchema:
  chat_completion = openai.ChatCompletion.create(
    messages=[message.dict() for message in messages],
    **options.dict()
  )

  return chat_completion

def parse_chat_history(
  chat_history: list[AIMessage | HumanMessage], 
  pydantic_model: Type[T], 
  system_prompt_template: str = ""
) -> T:
  try:
    llm = OpenAI(
      temperature=0.0
    )
    
    chat_parser = PydanticOutputParser(
      pydantic_object=pydantic_model
    )

    chat_parser_prompt = PromptTemplate.from_template(system_prompt_template)

    stringified_chat_history = chat_stringify(chat_history)

    prompt = chat_parser_prompt.format(chat_history=stringified_chat_history, format_instructions=chat_parser.get_format_instructions())

    parse_result = llm.predict(prompt)

    parsed = chat_parser.parse(parse_result)

    return parsed
  except Exception as e:
    print("E", e)

def chat_stringify(chat_history: list[AIMessage | HumanMessage]) -> str:
  chat_history_string = ""

  for message in chat_history:
    if isinstance(message, AIMessage):
      chat_history_string += f"AI: {message.content}\n"
      continue

    if isinstance(message, HumanMessage):
      chat_history_string += f"User: {message.content}"

  return chat_history_string

def generate_parsed(
  pydantic_object: Type[T], 
  prompt_template: str, 
  additional_data: dict) -> T:
  try:
    llm = OpenAI(openai_api_key=config.OPENAI_API_KEY, temperature=0)
    output_parser = PydanticOutputParser(
      pydantic_object=pydantic_object, 
    )

    prompt = PromptTemplate.from_template(prompt_template)

    llm_result = llm.predict(
      prompt.format(
      **{
        **additional_data,
        "format_instructions": output_parser.get_format_instructions()
      })
    )

    print("OpenAI Summary Result", llm_result)

    parsed_result = output_parser.parse(llm_result)

    return parsed_result
  except Exception as e:
    print("Error at openai.service.generate_parsed", e)
    
    raise e
  
async def async_predict(
  prompt_template: str, 
  additional_data: dict) -> T:
  try:
    llm = OpenAI(openai_api_key=config.OPENAI_API_KEY, temperature=0)

    prompt = PromptTemplate.from_template(prompt_template)

    llm_result = await llm.apredict(
      prompt.format(**additional_data),
    )

    return llm_result
  except Exception as e:
    print("Error at openai.service.async_predict", e)
    
    raise e