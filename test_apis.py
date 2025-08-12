import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai():
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messagges=[{"role": "users", "content": "Hello, this is a test"}],
            max_tokens=100,
        )
        print("✅ OpenAI API: Working")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ OpenAI API: {e}")
        return False
