summary_parser_prompt_template = (
"""Given a chat history between an "AI" and "User", 
Your job is to summarize the conversation, Highlighting important informations about the "User", such as their hobbies, life goals, values, personality
and partner criterias. Do not make up any additional details besides the ones provided in the dialogue. 
Be Specific about what the user likes and dislikes. Summarize the conversation in ENGLISH regardless of the original language

{format_instructions}

{chat_history}
""")