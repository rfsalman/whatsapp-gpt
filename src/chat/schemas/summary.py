from pydantic import BaseModel, Field

from src.helpers.chat_summary_topics import ChatSummaryTopics

class ChatSummarySchema(BaseModel):
  topics: list = Field(
    default=[],
    description=f"""The topics of the conversation,
      choose at most three topics and only the most relevant ones and,
      leave empty if there is no matching topic: 
      {", ".join(map(lambda c: c.value, ChatSummaryTopics))}
    """,
  )
  summary: str = Field(
    default=None,
    description="The actual summary of the conversation",
  )