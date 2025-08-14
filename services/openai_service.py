import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _detect_query_components(self, query: str) -> List[str]:
        """First pass: detect what components are mentioned in the query"""

        detection_prompt = """
        Analyze this query and identify which components are mentioned or implied.
        Return a JSON array of components found.

        Possible components:
        - "industry" (automotive, fintech, healthcare, etc.)
        - "location" (geographic focus)
        - "ticket_size" (investment amount/range)
        - "company_stage" (startup, growth, late-stage)
        - "source_project" (existing project references)
        - "new_project" (creating new project)
        - "investor_type" (VC, PE, angel, corporate)
        - "requirements" (dry powder, warm leads, etc.)
        - "timeframe" (recent investments, active now)
        - "portfolio_focus" (B2B, B2C, etc.)
        - "exit_strategy" (IPO, acquisition focus)

        Example: ["industry", "location", "ticket_size", "new_project"]
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":detection_prompt},
                    {"role":"user","content": f"Query: {query}"}
                ],
                max_tokens=150
            )

            components = json.loads(response.choices[0].message.content)
            return components

        except Exception as e:
            print(f"Error detecting components: {e}")
            return ["industry","location"] # fallback


    def _build_dynamic_schema(self, components: List[str]) -> Dict[str, str]:
        """Build extraction schema based on detected components"""

        schema_mapping = {
            "industry": "string - industry/sector focus (e.g. 'automotive', 'fintech')",
            "location": "string - geographic location (e.g. 'Germany', 'Silicon Valley')",
            "ticket_size": "object - investment range with min/max numbers",
            "company_stage": "string - startup stage (e.g. 'seed', 'series-a', 'growth')",
            "source_project": "string - existing project name to reference",
            "new_project": "string - new project name to create",
            "investor_type": "string - type of investor (e.g. 'VC', 'PE', 'corporate')",
            "requirements": "array - special requirements (e.g. ['dry powder', 'warm leads'])",
            "timeframe": "string - investment timeframe (e.g. 'last 12 months', 'currently active')",
            "portfolio_focus": "string - business model focus (e.g. 'B2B', 'B2C', 'marketplace')",
            "exit_strategy": "string - preferred exit (e.g. 'IPO', 'acquisition')"
        }

        return {comp: schema_mapping[comp] for comp in components if comp in schema_mapping}


    def parse_investor_query(self, query: str) -> Dict[str, any]:
        """ Main parsing function with dynamic extraction"""

        # Step 1: Detect what's in the query
        print(f"🔍 Analyzing query: {query[:50]}...")
        components = self._detect_query_components(query)
        print(f"📋 Detected components: {components}")

        # Step 2: Build dynamic schema
        schema = self._build_dynamic_schema(components)

        # Step 3: Create dynamic extraction prompt
        schema_description = "\n".join([f"- {field}: {desc}" for field, desc in schema.items()])

        extraction_prompt = f"""
        Extract the following information from the user query and return as JSON:

        {schema_description}

        Rules:
        - Only include fields that have actual values from the query
        - Use null for fields mentioned but without specific values
        - For ticket_size, convert amounts to numbers (e.g. "5-10M" = {{"min":5000000, "max":10000000}})
        - Return valid JSON only, no explanatons


        Example format:
        {{
            "industry":"automotive",
            "location":"Germany
        }}
        """

    # Test the function
    if __name__ == "__main__":
        service = OpenAIService()
        test_query = "Generate a list of investors that invest in automotive space in Germany, I just need companies names, website and LinkedIn URL. Take investors from Project ENIGMA and add additional investors from Apollo. that do tickets between 5-10 million and have a dry powder available."
        result = service.parse_investor_query(test_query)
        print(json.dumps(result, indent=2))
