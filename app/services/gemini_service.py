from google import genai
import os


class Gemini_Service:
    def __init__(self):
        API_KEY = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=API_KEY)
        

    def prompting(self, input):
        print("Đã gọi API")
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            contents=input
        )

        return response.text
