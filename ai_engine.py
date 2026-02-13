import requests
import json
import logging
from config import GITHUB_TOKEN, GITHUB_API_URL

def generate_code(prompt: str):
    # 1. Detailed Headers (Crucial for Hosting)
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "AssassinCodarBot/1.0" # GitHub requires this
    }
    
    payload = {
        "messages": [
            {
                "role": "system", 
                "content": "You are an expert programmer. Return ONLY raw source code. No explanations. Use the best language for the task if not specified."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        "model": "gpt-4o-mini", 
        "temperature": 0.2,
        "max_tokens": 4000
    }

    try:
        # 2. Increase timeout for slow server connections
        response = requests.post(GITHUB_API_URL, headers=headers, json=payload, timeout=30)
        
        # 3. Log errors to the server console so you can see them
        if response.status_code != 200:
            logging.error(f"API Failed! Status: {response.status_code}, Response: {response.text}")
            return None
            
        data = response.json()
        content = data['choices'][0]['message']['content']
        
        # Clean markdown
        return content.replace("```", "").strip()

    except Exception as e:
        logging.error(f"Connection Error on Host: {e}")
        return None