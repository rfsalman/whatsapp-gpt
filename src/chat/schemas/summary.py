from pydantic import BaseModel, Field

class ChatSummarySchema(BaseModel):
  topics: list = Field(
    default=[],
    description="""The topics of the conversation,
      choose at most three topics from: 
      hobbies-interest, relationship-goals, values, partner-hobbies-criteria,
      love-language, partner-physical-criteria, partner-values-criteria
    """,
  )
  summary: str = Field(
    default=None,
    description="The actual summary of the conversation",
  )