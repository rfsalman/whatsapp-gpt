from pydantic import BaseModel, Field

from src.helpers.topics import MessageTopics

class ChatSummarySchema(BaseModel):
  topics: list = Field(
    default=[],
    description=f"""The topics of the conversation,
      choose at most three topics and only the most relevant ones and,
      leave empty if there is no matching topic: 
      values-life-goals, love-language, user-personality, partner-personality, partner-criteria,
      {", ".join(map(lambda c: c.value, MessageTopics))}
    """,
  )
  summary: str = Field(
    default=None,
    description="The actual summary of the conversation",
  )