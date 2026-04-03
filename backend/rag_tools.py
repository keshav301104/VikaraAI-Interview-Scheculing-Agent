import json

def query_knowledge_base(topic: str) -> str:
    """
    Searches the company knowledge base for information.
    """
    try:
        with open("knowledge.json", "r") as file:
            data = json.load(file)
            
        # We check if the AI's requested topic matches any keys in our JSON
        # In a massive enterprise app, this would be a Vector Database (like Pinecone)
        for key, value in data.items():
            if topic.lower() in key.lower():
                return value
                
        return "I don't have that specific information in my database. Please ask the human recruiter during your next round."
        
    except Exception as e:
        return f"Error accessing knowledge base: {str(e)}"