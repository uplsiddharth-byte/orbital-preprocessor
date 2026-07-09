import os

import google.generativeai as genai

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("No API key. Set GEMINI_API_KEY.")
    exit()

genai.configure(api_key=api_key)
for m in genai.list_models():
    print(m.name)