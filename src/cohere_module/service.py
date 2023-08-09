from langchain.llms import Cohere, OpenAI
from typing import TypeVar, Type
from langchain.prompts import PromptTemplate
import os
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel

from src.config import config

T = TypeVar("T", bound=BaseModel)

def generate_parsed(
  pydantic_object: Type[T], 
  prompt_template: str, 
  additional_data: dict) -> T:
  try:
    llm = Cohere(cohere_api_key=config.COHERE_API_KEY)
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

    print("Cohere LLM Result", llm_result)

    parsed_result = output_parser.parse(llm_result)

    return parsed_result
  except Exception as e:
    print("Error at cohere_module.generate_parsed", e)
    
    raise e
    