import google.generativeai as genai
import os

# Load your Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyCWXLiBfWLIS9kueuIju5BDcWn4Sn-gLc4"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Instantiate model
model = genai.GenerativeModel('gemini-2.0-flash')

# Test prompt
try:
    response = model.generate_content("What is HTML ?")
    print("✅ Gemini API is working!")
    print("Response:", response.text)
except Exception as e:
    print("❌ Gemini API call failed:")
    print(str(e))
