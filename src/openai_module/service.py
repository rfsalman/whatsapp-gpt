
import openai
from openai.error import RateLimitError
from langchain.chat_models import ChatOpenAI
from langchain.schema import (
  HumanMessage,
  SystemMessage
)
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import (
  SystemMessage,
  HumanMessage,
)

from src.config import config
from src.user.models import UserBioModel, UserModel
from .schemas import ChatCompletionMessageSchema, ChatCompletionOptionsSchema, ChatCompletionResponseSchema
import src.openai_module.prompts as prompts

openai.api_key = config.OPENAI_API_KEY

# def create_full_chat_completion(
#   message_history: list[ChatCompletionMessageSchema],
#   user: UserModel, 
#   options: ChatCompletionOptionsSchema
# ) -> str:
#   chat_openai = ChatOpenAI(temperature=0.5)

#   system_message = SystemMessagePromptTemplate.from_template(
#     prompts.system_message_prompt
#   )

#   bio_information: UserBioModel | None = user.dict().get("bio_information", {})
  
#   if not bio_information:
#     bio_information = {}
  
#   system_message_content=system_message.format(
#     full_name=bio_information.get("full_name", ""),
#     date_of_birth=bio_information.get("date_of_birth", ""),
#     gender=bio_information.get("gender", ""),
#     interests=bio_information.get("interests", ""),
#     relationship_goal=bio_information.get("relationship_goal", "")
#   )

#   human_message_content=message_history.pop().content

#   result = None

#   try:
#     result = chat_openai.predict_messages([
#       SystemMessage(
#         content=system_message_content.content
#       ),
#       HumanMessage(
#         content=human_message_content
#       )
#     ])
#   except Exception as e:
#     print("Error: \n", e)
#     return ""

#   return result.content

def create_chat_completion(messages: list[ChatCompletionMessageSchema], options: ChatCompletionOptionsSchema) -> ChatCompletionResponseSchema:
  chat_completion = openai.ChatCompletion.create(
    messages=[message.dict() for message in messages],
    **options.dict()
  )

  return chat_completion

def create_full_chat_completion(
  message_history: list[ChatCompletionMessageSchema],
  user: UserModel, 
  options: ChatCompletionOptionsSchema
) -> ChatCompletionMessageSchema:
  finish_reason = ""
  chat_completion_text_result = ""
  
  user_bio = user.bio_information.dict() if user.bio_information else {}

  system_message = ChatCompletionMessageSchema(
    role="system",
    content=f"""
      Your name is Serene, An AI Assistant that help me find my ideal partner, you will ask questions about my preference and criteria,
      With your extensive knowledge of compatibility and your warmth, empathetic nature, Serene is passionate for creating meaningful connections.

      This is what you know about me:
      1. Full Name: {user_bio.get("full_name", "")}
      2. Date Of Birth: {user_bio.get("date_of_birth", "")}
      3. Gender: {user_bio.get("gender", "")}
      4. Interests: {user_bio.get("interests", [])}
      5. Relationship Goal: {user_bio.get("relationship+goal", "")}

      You will ask questions to fill the fields with empty value, 
      skip questions for already filled in value.
      
      Don't ask too many details and ask one question at a time, If the answer doesn't make sense
      Try asking again and suggests a proper format.
    """,
    name="Serene"    
  )

  chat_completion = None

  try:
    while finish_reason in ["", "length"]:
      messages = [
        system_message,
        *message_history,
      ]

      if finish_reason == "length":
        continue_message = ChatCompletionMessageSchema(
          role="user",
          content="continue",
          name=user.name.split(" ")[0]
        )

        messages.append(continue_message)

      chat_completion: ChatCompletionResponseSchema = openai.ChatCompletion.create(
        messages=[message.dict() for message in messages],
        **options.dict()
      )

      finish_reason = chat_completion.choices[0].finish_reason
      chat_completion_text_result = chat_completion_text_result + chat_completion.choices[0].message.content
    

    if chat_completion:
      chat_completion.choices[0].message.content = chat_completion_text_result
    
    return chat_completion
  
  except RateLimitError as e:
    print("e", e)
    
    return None
  except Exception as e:
    print("e", e)
    
    return None
  finally:
    return chat_completion
    