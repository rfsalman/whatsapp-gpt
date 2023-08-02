ChatSummaryModel = {
  "class": "ChatSummaries",
  "properties": [
    {
      "name": "topic",
      "dataType": ["text"],
    },
    {
      "name": "summary",
      "dataType": ["text"],
    },
    {
      "name": "batch_id",
      "dataType": "text",
      "moduleConfig": {
        "text2vec-cohere": {
          "skip": True
        }
      }
    },
    {
      "name": "chat_id",
      "dataType": "text",
      "moduleConfig": {
        "text2vec-cohere": {
          "skip": True
        }
      }
    },
    {
      "name": "timestamp",
      "dataType": "date",
      "moduleConfig": {
        "text2vec-cohere": {
          "skip": True
        }
      }
    }
  ],
  "vectorizer": "text2vec-cohere",
  "moduleConfig": {
    "text2vec-cohere": {
      "vectorizeClassName": False
    },
    "generative-openai": {
      "model": "gpt-3.5-turbo"
    }
  }
}