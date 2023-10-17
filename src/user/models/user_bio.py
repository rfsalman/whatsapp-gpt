UserBioWeaviateModel = {
  "class": "UserBios",
  "properties": [
    {
      "name": "name",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "gender",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "interests",
      "dataType": ["text[]"],
    },
    {
      "name": "date_of_birth",
      "dataType": ["date"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "matchmaking_summary",
      "dataType": ["text"]
    },
    {
      "name": "relationship_goal",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
    {
      "name": "user_id",
      "dataType": ["text"],
      "moduleConfig": {
        "text2vec-openai": {
          "skip": True
        }
      }
    },
  ],
  "vectorizer": "text2vec-openai",
    "moduleConfig": {
      "text2vec-openai": {
        "vectorizeClassName": True
      },
      "generative-openai": {
        "model": "gpt-3.5-turbo"
      }
  }
}