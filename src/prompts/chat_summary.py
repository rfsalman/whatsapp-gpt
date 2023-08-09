summary_parser_prompt_template = (
"""Given a chat history between an "AI" and "User", 
Your job is ONLY to summarize the conversation, Highlighting important informations about the "User", such as their hobbies, life goals, values, personality
and partner criterias. Do not add made up any additional conclusion besides the ones inferred from the dialogue. 
Be Specific about what the user likes and dislikes.
Summarize the conversation in ENGLISH regardless of the original language

{format_instructions}

{chat_history}
""")