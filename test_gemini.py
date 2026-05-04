import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
try:
    client = genai.Client()
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents='Explain Python in 1 sentence.'
    )
    print("SUCCESS")
    print(response.text)
except Exception as e:
    print(f"ERROR: {e}")
