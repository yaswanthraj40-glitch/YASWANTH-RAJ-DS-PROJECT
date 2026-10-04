"""
CoolRoute AI Chatbot Engine
Supports both OpenAI API and free local fallback
"""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class ChatbotEngine:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = bool(self.openai_api_key)

        # City knowledge base for RAG (Retrieval Augmented Generation)
        self.city_knowledge = {
            "chennai": {
                "avg_summer_temp": "41-47°C",
                "hotspots": ["T. Nagar", "Anna Nagar", "Guindy", "Velachery"],
                "tree_cover": "6.7% (very low)",
                "heat_deaths_2023": "~15 recorded",
                "best_trees": ["Neem", "Peepal", "Banyan", "Pongamia"],
                "wards": 200
            },
            "urban_heat_island": {
                "definition": "Urban areas significantly warmer than surrounding rural areas due to human activities",
                "causes": ["Concrete and asphalt", "Lack of vegetation", "Vehicle emissions", "Building density", "Industrial activity"],
                "effects": ["Heat stress", "Increased energy consumption", "Air quality degradation", "Health risks", "Reduced comfort"],
                "mitigation": ["Tree planting", "Green roofs", "Cool pavements", "Water bodies", "Urban planning"]
            },
            "tree_cooling": {
                "mechanism": "Transpiration releases water vapor + shade reduces surface temperature",
                "neem": {"cooling_per_tree": "0.08°C", "growth": "Fast", "maintenance": "Low", "best_for": "Roadsides, open areas"},
                "peepal": {"cooling_per_tree": "0.10°C", "growth": "Medium", "maintenance": "Low", "best_for": "Temples, parks"},
                "banyan": {"cooling_per_tree": "0.12°C", "growth": "Slow", "maintenance": "Medium", "best_for": "Large open spaces"},
                "gulmohar": {"cooling_per_tree": "0.06°C", "growth": "Fast", "maintenance": "Low", "best_for": "Aesthetics + shade"}
            }
        }

        # Project-specific knowledge
        self.project_knowledge = """
        CoolRoute is an Urban Heat Island mitigation system that:
        1. Uses Landsat 9 satellite imagery to measure surface temperatures
        2. Uses XGBoost ML to predict heat based on building density, roads, vegetation, population
        3. Uses equity-weighted optimization to prioritize low-income, high-heat zones
        4. Generates 3D interactive maps with specific GPS coordinates for planting
        5. Tracks impact over time using satellite comparison

        Key features:
        - Budget-aware planning (input your budget, get optimal plan)
        - Equity priority mode (prioritizes poor neighborhoods)
        - ROI calculator (shows cost per degree cooled)
        - Real-time chatbot for any questions
        - Before/After temperature simulation
        """

    def search_knowledge(self, query: str) -> str:
        """Search local knowledge base for relevant context"""
        query_lower = query.lower()
        context_parts = []

        # Search city knowledge
        for topic, data in self.city_knowledge.items():
            if topic in query_lower or any(word in query_lower for word in topic.split("_")):
                context_parts.append(f"{topic}: {str(data)}")

        # Always include project knowledge for project-related queries
        project_keywords = ["project", "coolroute", "system", "how", "work", "feature", "model"]
        if any(kw in query_lower for kw in project_keywords):
            context_parts.append(self.project_knowledge)

        return "\n".join(context_parts) if context_parts else ""

    async def generate_response(self, message: str) -> str:
        """Generate AI response using OpenAI or local fallback"""

        # Search local knowledge
        context = self.search_knowledge(message)

        if self.use_openai:
            try:
                import openai
                client = openai.AsyncOpenAI(api_key=self.openai_api_key)

                response = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": f"""You are CoolRoute AI, an expert assistant on urban heat islands, 
                            climate resilience, tree planting optimization, and city planning. 
                            You have access to this project context: {context}

                            Guidelines:
                            - Answer ANY question the user asks, not just project-related ones
                            - For project questions, use the provided context
                            - For general questions, use your knowledge
                            - Be concise but informative (2-4 sentences)
                            - Use Celsius for temperatures and INR for currency
                            - If asked about specific wards, reference the demo data"""
                        },
                        {"role": "user", "content": message}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content

            except Exception as e:
                print(f"OpenAI error: {e}")
                return await self._local_response(message, context)

        return await self._local_response(message, context)

    async def _local_response(self, message: str, context: str) -> str:
        """Local fallback response generator (no API needed)"""
        msg_lower = message.lower()

        # Project-specific responses
        if any(word in msg_lower for word in ["hello", "hi", "hey"]):
            return "👋 Hello! I'm CoolRoute AI. Ask me anything about urban heat, tree planting, your city, or even general topics!"

        elif "heat island" in msg_lower or "uhi" in msg_lower:
            return "Urban Heat Islands make cities 1-7°C hotter than rural areas due to concrete, buildings, and lack of trees. Our project identifies these hotspots using satellite data and recommends targeted tree planting to cool them down."

        elif "tree" in msg_lower and ("best" in msg_lower or "species" in msg_lower or "plant" in msg_lower):
            return "For Indian cities, I recommend: (1) Neem - fast growth, 0.08°C cooling per tree, low maintenance, (2) Peepal - 0.10°C cooling, great for parks, (3) Banyan - 0.12°C cooling but slow growth, ideal for large spaces. Neem is best for roadsides due to pollution tolerance."

        elif "how" in msg_lower and ("work" in msg_lower or "project" in msg_lower):
            return "CoolRoute works in 4 steps: (1) Satellite imagery captures surface temperatures, (2) XGBoost ML predicts heat from building density, roads, and vegetation, (3) Equity-weighted optimization ranks planting spots by need ÷ cost, (4) 3D map shows exact GPS coordinates for planting with before/after simulation."

        elif "budget" in msg_lower or "cost" in msg_lower or "money" in msg_lower or "price" in msg_lower:
            return "With ₹5,00,000, you can plant ~1,000 Neem trees or 1,400 Gulmohar trees. The ROI calculator shows energy savings of ₹15L over 5 years. Cost per degree cooled is approximately ₹1,56,000. Low-income wards get priority in equity mode."

        elif "equity" in msg_lower or "poor" in msg_lower or "income" in msg_lower or "vulnerable" in msg_lower:
            return "Our equity algorithm prioritizes wards with income < 4/10 and temperature > 42°C. Ward 23 (income: 2/10, temp: 46.8°C) and Ward 101 (income: 2/10, temp: 47.2°C) are top priorities. These zones get 40% higher weighting in the optimization score."

        elif "chennai" in msg_lower or "city" in msg_lower:
            return "Chennai faces severe UHI with summer surface temps reaching 47°C. Hotspots include T. Nagar, Anna Nagar, and Guindy. Current tree cover is only 6.7%. Our model recommends 1,247 trees across 18 zones, targeting a 3.2°C average cooling reduction."

        elif "ward" in msg_lower:
            return "Ward 23 is our highest priority: 46.8°C, population 35,000, income level 2/10. Recommended: 150 Neem trees at ₹75,000. Expected cooling: 3.5°C. Ward 101 is second priority at 47.2°C with 180 trees recommended. Check the 3D map for exact locations!"

        elif "satellite" in msg_lower or "data" in msg_lower or "landsat" in msg_lower:
            return "We use Landsat 9 thermal bands (30m resolution) and Sentinel-2 NDVI (10m resolution) from Google Earth Engine. Surface temperature is calibrated against ground IoT sensors. Cloud gaps are filled using weather API interpolation."

        elif "model" in msg_lower or "xgboost" in msg_lower or "ml" in msg_lower or "algorithm" in msg_lower:
            return "The heat predictor uses XGBoost with 9 features: NDVI, building density, road density, population, distance to water, elevation, albedo, income index, and existing tree cover. It achieves 85% accuracy on validation data. Feature importance: buildings (35%), vegetation (25%), roads (15%)."

        elif "optimization" in msg_lower or "optimize" in msg_lower:
            return "The optimizer uses a greedy algorithm with equity weighting. Score = (Heat × Population × IncomeVulnerability) ÷ Cost. It respects budget constraints, land availability, and road width. Outputs ranked list with GPS coordinates, species, and expected cooling per location."

        elif "cooling" in msg_lower or "temperature" in msg_lower or "degree" in msg_lower:
            return "Expected cooling varies by ward: Ward 23 can cool by 3.5°C with 150 trees, Ward 7 by 2.8°C with 120 trees. City-wide average: 3.2°C reduction. This translates to 12 fewer heat-related deaths per year and ₹12L energy savings."

        elif "impact" in msg_lower or "benefit" in msg_lower or "save" in msg_lower:
            return "Projected impacts: 45,230 people benefited, 1.2M kWh energy saved yearly, 450 tons CO₂ absorbed, ~12 heat deaths prevented annually, and ₹2.3L net ROI over 5 years. The equity mode ensures low-income communities benefit first."

        elif "3d" in msg_lower or "map" in msg_lower or "visual" in msg_lower:
            return "The 3D map uses Mapbox GL with extruded polygons — heat zones rise as 3D bars colored from green (cool) to red (hot). Click any zone to see ward details, temperature, population, and tree recommendations. Toggle layers for buildings, heat, and tree plans."

        elif "time" in msg_lower or "when" in msg_lower or "duration" in msg_lower:
            return "Tree planting should happen during monsoon (June-September) for best survival. Cooling effects start within 6 months for fast-growing species (Neem, Gulmohar) and peak at 3-5 years. Full impact is visible in the Before/After timeline on the dashboard."

        elif "maintenance" in msg_lower or "care" in msg_lower or "water" in msg_lower:
            return "Neem needs watering only for first 2 years (₹50/year), then self-sustaining. Banyan needs more care (₹80/year). We factor maintenance into the 5-year ROI calculation. Drip irrigation is recommended for the first year in all zones."

        else:
            return f"That's an interesting question! As CoolRoute AI, I specialize in urban heat mitigation, but I can discuss broader topics too. For your project specifically, we use satellite data + ML to identify hotspots and optimize tree planting with equity considerations. Would you like details on the technical architecture, the optimization formula, or specific ward data?"
