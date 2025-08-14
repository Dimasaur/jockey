import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def parse_investor_query(self, query: str) -> dict:
        # to be built
        pass

    # Test the function
    if __name__ == "__main__":
        service = OpenAIService()
        test_query = "Generate a list of investors that invest in automotive space in Germany, I just need companies names, website and LinkedIn URL. Take investors from Project ENIGMA and add additional investors from Apollo. that do tickets between 5-10 million and have a dry powder available."
        result = service.parse_investor_query(test_query)
        print(json.dumps(result, indent=2))
