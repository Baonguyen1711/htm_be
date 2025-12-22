import json
import re
from google import genai
from google.genai import types
import os


API_KEY = os.getenv("GEMINI_API_KEY")
print("API_KEY",API_KEY )
client = genai.Client(api_key=API_KEY)
print("client",client)
    

def prompting(input):
    try:
        print("Đã gọi API")
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=input,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=2
            )
        )
        if not response.candidates:
            return []

        raw_text = response.candidates[0].content.parts[0].text

        # Loại bỏ ```json … ``` nếu có
        clean_text = re.sub(r"^```json|```$", "", raw_text).strip()

        # Parse sang Python object

        print("clean_text", clean_text)
        return clean_text
    except Exception as e:
        print("Error calling Gemini API:", e)
        return ""
    




