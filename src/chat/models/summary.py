ChatSummaryModel = {
  "class": "ChatSummaries",
  "properties": [
    {
      "name": "topics",
      "dataType": ["text[]"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "summary",
      "dataType": ["text"],
    },
    {
      "name": "batch_id",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "chat_id",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "timestamp",
      "dataType": ["date"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    }
  ],
  "vectorizer": "text2vec-openai",
    "moduleConfig": {
      "text2vec-openai": {
        "vectorizeClassName": False
      },
      "generative-openai": {
        "model": "gpt-3.5-turbo"
      }
  }
}