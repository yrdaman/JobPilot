import os
from groq import Groq

# 1. Initialize the official native Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"), # Looks for your secret gsk_ key
)

try:
    # 2. Fetch the active models list natively
    models_list = client.models.list()
    
    print("--- Active Native Groq Models ---")
    # 3. Loop through and print the exact ID strings
    for model in models_list.data:
        print(f"- {model.id}")
        
except Exception as e:
    print(f"Failed to fetch models: {e}")
