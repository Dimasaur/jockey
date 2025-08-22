"""
OpenAI service for natural language query parsing

Uses a two-step approach:
1) Component detection: identify what fields are mentioned in the query
2) Dynamic extraction: build a schema and extract values for detected fields

This allows flexible parsing without hardcoding field expectations.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class OpenAIService:
    """Parse natural language investor queries into structured data."""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _detect_query_components(self, query: str) -> list[str]:
        """First pass: detect what components are mentioned in the query"""

        detection_prompt = """
        Analyze this query and identify ALL components that are mentioned or implied.
        Be generous - if something could reasonably be extracted, include it!

        Return ONLY a valid JSON array of component strings. Do not include any explanations or additional text.

        Possible components:
        - "industry" (automotive, fintech, healthcare, venture capital, etc.)
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

        IMPORTANT RULES:
        - If the query mentions "venture capital", "VC", or "venture capitals", include BOTH "industry" AND "investor_type"
        - "venture capital" is both an industry sector AND an investor type
        - Be comprehensive - if something could be extracted, include it

        Example response: ["industry", "location", "ticket_size", "new_project"]

        IMPORTANT: Return ONLY the JSON array, no other text.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":detection_prompt},
                    {"role":"user","content": f"Query: {query}"}
                ],
                max_tokens=150,
                temperature=0.1
            )

            content = response.choices[0].message.content.strip()

            # Try to extract JSON if there's extra text
            if content.startswith('[') and content.endswith(']'):
                components = json.loads(content)
            else:
                # Try to find JSON array in the response
                import re
                json_match = re.search(r'\[.*?\]', content)
                if json_match:
                    components = json.loads(json_match.group())
                else:
                    print(f"Could not parse JSON from response: {content}")
                    return ["industry", "location"]  # fallback

            return components

        except Exception as e:
            print(f"Error detecting components: {e}")
            print(f"Response content: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
            return ["industry", "location"]  # fallback


    def _build_dynamic_schema(self, components: list[str]) -> dict[str, str]:
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


    def parse_investor_query(self, query: str) -> dict[str, any]:
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
        Extract the following information from the user query and return as valid JSON:

        {schema_description}

        Rules:
        - Only include fields that have actual values from the query
        - Use null for fields mentioned but without specific values
        - For ticket_size, convert amounts to numbers (e.g. "5-10M" = {{"min":5000000, "max":10000000}})
        - Return ONLY valid JSON, no explanations or additional text
        - Ensure all strings are properly quoted
        - Ensure all brackets and braces are properly closed

        IMPORTANT EXTRACTION RULES:
        - If the query mentions "venture capital", "VC", or "venture capitals", set industry="venture capital"
        - If the query mentions "venture capital", "VC", or "venture capitals", set investor_type="VC"
        - "venture capital" should be extracted as BOTH industry AND investor_type
        - For other industries, extract the specific industry mentioned

        Example format:
        {{
            "industry": "venture capital",
            "location": "Netherlands",
            "investor_type": "VC"
        }}

        IMPORTANT: Return ONLY the JSON object, no other text.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":extraction_prompt},
                    {"role":"user","content":query}
                ],
                max_tokens=400,
                temperature=0.1
            )

            content = response.choices[0].message.content.strip()

            # Try to extract JSON if there's extra text
            if content.startswith('{') and content.endswith('}'):
                result = json.loads(content)
            else:
                # Try to find JSON object in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    print(f"Could not parse JSON from response: {content}")
                    raise ValueError("Invalid JSON response")

            # Add metadata about what was extracted
            result["_metadata"] = {
                "detected_components":components,
                "extraction_schema": list(schema.keys()),
                "query_complexity": len(components)
            }

            return result

        except Exception as e:
            print(f"❌ Extraction error: {e}")
            print(f"Response content: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
            return {
                "error":str(e),
                "_metadata": {
                    "detected_components": components,
                    "query":query
                }
            }

    # Test with various query types
if __name__ == "__main__":
    service = OpenAIService()

    test_queries = [
        # Simple query
        "Find automotive investors in Germany",

        # Complex query with multiple components
        "Generate Series A fintech investors in London with 2-5M tickets who have dry powder and focus on B2B SaaS, create Project LONDON-FINTECH",

        # Project-focused query
        "Get warm leads from Project ENIGMA and add healthcare VCs in California",

        # Investment-focused query
        "Find corporate VCs that invest in AI startups with recent IPO exits",

        # Geographic + stage query
        "Late-stage growth investors in Southeast Asia with 10M+ tickets"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}")
        print(f"{'='*60}")

        result = service.parse_investor_query(query)
        print(f"\n📊 RESULT:")
        print(json.dumps(result, indent=2))

        print(f"\n🎯 EXTRACTED FIELDS: {', '.join(result.get('_metadata', {}).get('extraction_schema', []))}")
