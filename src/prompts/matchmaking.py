matchmaking_summary_prompt = """The following is a list of conversation summary between user and a personal matchmaking assistant, 
your job is to summarize those paragraphs into a single one, containing at parts, 
each part should focus on a single topic from hobbies, values/life goals, and partner criteria, 
be SPECIFIC and DETAILED about what the user likes and dislikes.

Conversation Sumamries:
{matchmaking_summary}
"""