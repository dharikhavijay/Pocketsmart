import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image

from app.config import settings
from app.services.platform_linker import PlatformLinker

logger = logging.getLogger("pocketsmartai.gemini")

# Try importing google.generativeai
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class GeminiService:
    """
    Manages Gemini LLM interactions, multimodal vision prompts,
    structured JSON parsing, and robust fallback recommendations.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY.strip() if settings.GEMINI_API_KEY else ""
        self.model_name = settings.GEMINI_MODEL or "gemini-1.5-flash"
        self.is_configured = False

        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.is_configured = True
                logger.info(f"Gemini configured with model {self.model_name}")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}. Fallback mode active.")

    def _call_gemini_json(self, prompt: str, image_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Call Gemini model with system instruction to return raw JSON."""
        if not self.is_configured or not GENAI_AVAILABLE:
            return None

        try:
            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config={"response_mime_type": "application/json"}
            )
            
            contents: List[Any] = []
            if image_path and Path(image_path).exists():
                try:
                    img = Image.open(image_path)
                    contents.append(img)
                except Exception as img_err:
                    logger.warning(f"Could not open image for vision prompt: {img_err}")

            contents.append(prompt)
            response = model.generate_content(contents)

            if not response or not response.text:
                return None

            cleaned_text = response.text.strip()
            # Clean markdown codeblocks if present
            if cleaned_text.startswith("```json"):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.startswith("```"):
                cleaned_text = cleaned_text[3:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]

            data = json.loads(cleaned_text.strip())
            return data
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return None

    # =========================================================================
    # 1. HOME INTERIOR PLANNER
    # =========================================================================
    def generate_home_recommendations(
        self,
        total_budget: float,
        room_type: str,
        items_needed: List[str],
        style_preference: str = "Modern & Minimalist",
        additional_notes: str = ""
    ) -> Dict[str, Any]:
        """Generate budget allocation and product recommendations for Home Interiors."""
        items_str = ", ".join(items_needed) if items_needed else "Lighting, Seating, Storage, Decor"

        prompt = f"""
You are an expert interior designer and budget optimization specialist for PocketSmart AI.
Analyze the following home interior request:
- Total Budget: ₹{total_budget:,.2f}
- Room Type: {room_type}
- Key Items Needed: {items_str}
- Style Preference: {style_preference}
- Additional Notes: {additional_notes}

Generate a strictly valid JSON response adhering to this JSON schema:
{{
  "category": "home",
  "title": "{room_type} Interior Plan ({style_preference})",
  "total_budget": {total_budget},
  "estimated_total_cost": number (must be <= total_budget),
  "remaining_balance": number,
  "currency": "₹",
  "ai_insights": "Detailed 2-3 sentence interior styling advice and budget optimization tips.",
  "budget_allocations": [
    {{"category_name": "Furniture / Seating", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Lighting & Electricals", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Decor & Accents", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Storage / Organization", "allocated_amount": number, "percentage": number}}
  ],
  "recommendations": [
    {{
      "item_name": "Specific product name or model type",
      "category": "Furniture|Lighting|Decor|Storage",
      "estimated_price": number,
      "description": "Short explanation why this fits the style and budget.",
      "suggested_platform": "IKEA|Amazon|Flipkart",
      "key_features": ["Feature 1", "Feature 2"],
      "reasoning": "Value for money rationale"
    }}
  ]
}}
Ensure the recommendations match Indian e-commerce offerings (IKEA, Amazon.in, Flipkart).
Total price of all recommendations must be close to or strictly under the budget ₹{total_budget}.
Provide 4 to 8 realistic item recommendations.
"""
        data = self._call_gemini_json(prompt)
        if not data:
            data = self._generate_mock_home_recommendations(
                total_budget, room_type, items_needed, style_preference
            )
            data["is_mock"] = True
        else:
            data["is_mock"] = False

        # Enrich with URLs and metadata
        for rec in data.get("recommendations", []):
            PlatformLinker.enrich_recommendation(rec)

        return data

    def _generate_mock_home_recommendations(
        self,
        budget: float,
        room: str,
        items: List[str],
        style: str
    ) -> Dict[str, Any]:
        """High-quality contextual fallback for Home Interiors."""
        furniture_budget = round(budget * 0.50, 2)
        lighting_budget = round(budget * 0.20, 2)
        decor_budget = round(budget * 0.18, 2)
        storage_budget = round(budget * 0.12, 2)

        recs = [
            {
                "item_name": f"{style} Compact Modular Sofa / Lounger",
                "category": "Furniture",
                "estimated_price": round(furniture_budget * 0.65, 2),
                "description": f"Ergonomic, modern seating tailored for {room}, offering durable fabric and space efficiency.",
                "suggested_platform": "IKEA",
                "key_features": ["High-density foam", "Removable washable covers", "Compact footprint"],
                "reasoning": "Excellent durability-to-cost ratio for daily living."
            },
            {
                "item_name": f"Minimalist Solid Wood Center / Coffee Table",
                "category": "Furniture",
                "estimated_price": round(furniture_budget * 0.35, 2),
                "description": "Engineered wood with natural grain finish, complementing modern interior aesthetics.",
                "suggested_platform": "Amazon",
                "key_features": ["Scratch-resistant", "Easy assembly", "Lower storage shelf"],
                "reasoning": "Provides functional surface area without visual clutter."
            },
            {
                "item_name": "Warm Ambient Dimmable Ceiling Pendant Light",
                "category": "Lighting",
                "estimated_price": round(lighting_budget * 0.60, 2),
                "description": f"Energy-efficient LED fixture designed to create warm focal illumination in your {room.lower()}.",
                "suggested_platform": "Flipkart",
                "key_features": ["3000K Warm White", "Matte black & brass finish", "Adjustable cord"],
                "reasoning": "Enhances atmosphere while keeping energy consumption low."
            },
            {
                "item_name": "Smart Wi-Fi Floor Standing Lamp",
                "category": "Lighting",
                "estimated_price": round(lighting_budget * 0.40, 2),
                "description": "Adjustable reading light with RGB warm white controls compatible with Google Home & Alexa.",
                "suggested_platform": "Amazon",
                "key_features": ["App-controlled", "Dimmable", "Modern slender neck"],
                "reasoning": "Versatile corner lighting for reading and relaxing."
            },
            {
                "item_name": "Abstract Geometric Wall Canvas Art (Set of 3)",
                "category": "Decor",
                "estimated_price": round(decor_budget * 0.55, 2),
                "description": f"Contemporary canvas prints curated to complement {style.lower()} palettes.",
                "suggested_platform": "Amazon",
                "key_features": ["Framed canvas", "Fade-resistant inks", "Mounting hardware included"],
                "reasoning": "Instantly elevates blank wall space at minimal cost."
            },
            {
                "item_name": "Indoor Ceramic Planters with Metal Stand",
                "category": "Decor",
                "estimated_price": round(decor_budget * 0.45, 2),
                "description": "Textured ceramic pots suitable for snake plants or pothos, adding fresh green accents.",
                "suggested_platform": "IKEA",
                "key_features": ["Drainage holes with plugs", "Rust-proof stand", "Natural textures"],
                "reasoning": "Biophilic design element proven to boost comfort."
            },
            {
                "item_name": "Multi-tier Modular Wall Floating Shelves",
                "category": "Storage",
                "estimated_price": round(storage_budget, 2),
                "description": "Sturdy floating shelves for displaying books, succulents, and decorative objects.",
                "suggested_platform": "Flipkart",
                "key_features": ["Heavy load capacity", "Hidden brackets", "Water-resistant finish"],
                "reasoning": "Maximizes vertical storage without eating up floor area."
            }
        ]

        total_cost = sum(r["estimated_price"] for r in recs)
        remaining = max(0.0, round(budget - total_cost, 2))

        return {
            "category": "home",
            "title": f"{room} Interior Plan ({style})",
            "total_budget": budget,
            "estimated_total_cost": total_cost,
            "remaining_balance": remaining,
            "currency": "₹",
            "ai_insights": f"For your {room.lower()} with a {style.lower()} theme, we balanced 50% of your budget on foundational furniture, while keeping 20% for layered lighting and accents. This ensures longevity, cohesive aesthetics, and maximum utility.",
            "budget_allocations": [
                {"category_name": "Furniture / Seating", "allocated_amount": furniture_budget, "percentage": 50},
                {"category_name": "Lighting & Ambience", "allocated_amount": lighting_budget, "percentage": 20},
                {"category_name": "Decor & Accents", "allocated_amount": decor_budget, "percentage": 18},
                {"category_name": "Storage / Utility", "allocated_amount": storage_budget, "percentage": 12}
            ],
            "recommendations": recs
        }

    # =========================================================================
    # 2. PARTY BUDGET PLANNER
    # =========================================================================
    def generate_party_recommendations(
        self,
        total_budget: float,
        guest_count: int,
        event_type: str,
        venue_type: str = "Home / Apartment",
        food_preference: str = "Buffet / Catering",
        include_entertainment: bool = True,
        additional_notes: str = ""
    ) -> Dict[str, Any]:
        """Generate budget allocation and service/product recommendations for Parties & Events."""
        prompt = f"""
You are an expert event planner and budget optimizer for PocketSmart AI.
Analyze the following event details:
- Total Budget: ₹{total_budget:,.2f}
- Guest Count: {guest_count} attendees
- Event Type: {event_type} (e.g. Birthday, Anniversary, Wedding, Corporate, Reunion)
- Venue Type: {venue_type} (e.g. Home, Banquet, OYO Townhouse / Party Hall, Outdoor)
- Food & Beverage Preference: {food_preference} (Swiggy / Zomato bulk food, Catering)
- Include Entertainment: {include_entertainment}
- Additional Notes: {additional_notes}

Calculate realistic per-guest cost (₹{total_budget/guest_count:,.2f}/guest) and allocate proportionally.
Generate a strictly valid JSON response adhering to this schema:
{{
  "category": "party",
  "title": "{event_type} Celebration Plan for {guest_count} Guests",
  "total_budget": {total_budget},
  "estimated_total_cost": number (<= total_budget),
  "remaining_balance": number,
  "currency": "₹",
  "ai_insights": "2-3 sentences advising on per-person catering portions, venue negotiations, and party flow.",
  "budget_allocations": [
    {{"category_name": "Food & Catering", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Venue & Space", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Decoration & Ambiance", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Entertainment & Music", "allocated_amount": number, "percentage": number}}
  ],
  "recommendations": [
    {{
      "item_name": "Service or product item name",
      "category": "Catering|Venue|Decoration|Entertainment",
      "estimated_price": number,
      "description": "Clear details on how this fulfills the party needs.",
      "suggested_platform": "Swiggy|Zomato|OYO|Amazon|Flipkart",
      "key_features": ["Feature 1", "Feature 2"],
      "reasoning": "Cost efficiency or crowd-pleasing factor"
    }}
  ]
}}
Ensure the recommendations link to Indian platforms (Swiggy, Zomato, OYO, Amazon.in).
Total cost of all recommendations must be <= ₹{total_budget}.
Provide 4 to 8 realistic recommendations.
"""
        data = self._call_gemini_json(prompt)
        if not data:
            data = self._generate_mock_party_recommendations(
                total_budget, guest_count, event_type, venue_type, food_preference, include_entertainment
            )
            data["is_mock"] = True
        else:
            data["is_mock"] = False

        for rec in data.get("recommendations", []):
            PlatformLinker.enrich_recommendation(rec)

        return data

    def _generate_mock_party_recommendations(
        self,
        budget: float,
        guests: int,
        event_type: str,
        venue: str,
        food_pref: str,
        entertainment: bool
    ) -> Dict[str, Any]:
        """High-quality contextual fallback for Party & Event Planning."""
        catering_pct = 45
        venue_pct = 25 if "home" not in venue.lower() else 10
        decor_pct = 20 if "home" not in venue.lower() else 30
        ent_pct = 100 - (catering_pct + venue_pct + decor_pct)

        catering_budget = round(budget * (catering_pct / 100), 2)
        venue_budget = round(budget * (venue_pct / 100), 2)
        decor_budget = round(budget * (decor_pct / 100), 2)
        ent_budget = round(budget * (ent_pct / 100), 2)

        recs = [
            {
                "item_name": f"Gourmet Multi-Cuisine Platter for {guests} Guests",
                "category": "Catering",
                "estimated_price": round(catering_budget * 0.70, 2),
                "description": f"Curated appetizers and main course combo meal packages ordered in bulk via popular cloud kitchens.",
                "suggested_platform": "Zomato",
                "key_features": ["Starters + Mains + Bread", "Bulk discount eligible", "Hygienic catering packaging"],
                "reasoning": f"Ensures generous per-plate portion for {guests} guests at ₹{round((catering_budget*0.70)/guests, 2)}/head."
            },
            {
                "item_name": "Artisanal Dessert & Mocktail / Beverage Station",
                "category": "Catering",
                "estimated_price": round(catering_budget * 0.30, 2),
                "description": "Signature celebration cake and sparkling fruit mocktails delivered fresh.",
                "suggested_platform": "Swiggy",
                "key_features": ["Theme-customized cake", "Assorted cupcakes", "Chilled beverages"],
                "reasoning": "Memorable sweet finale and photo-worthy cake cutting."
            },
            {
                "item_name": f"Event Space Rental / Stay: {venue}",
                "category": "Venue",
                "estimated_price": round(venue_budget, 2),
                "description": f"Private celebration suite or banquet area accommodating {guests} guests comfortably.",
                "suggested_platform": "OYO",
                "key_features": ["Air-conditioned hall", "Dedicated hospitality staff", "Restroom & parking facilities"],
                "reasoning": "Hassle-free venue without long-term contracts or massive security deposits."
            },
            {
                "item_name": f"Theme Balloon Arch & Backdrop Kit ({event_type})",
                "category": "Decoration",
                "estimated_price": round(decor_budget * 0.60, 2),
                "description": "All-in-one metallic balloon arch, fairy fairy lights, party banner, and shimmer foil curtains.",
                "suggested_platform": "Amazon",
                "key_features": ["120-piece balloon garland", "Electric inflator friendly", "Self-standing arch strip"],
                "reasoning": "High visual impact for guest photography and social media."
            },
            {
                "item_name": "Ambient Fairy Lights & LED Neon Signboard",
                "category": "Decoration",
                "estimated_price": round(decor_budget * 0.40, 2),
                "description": "Warm yellow waterproof string lights and glowing neon celebration sign.",
                "suggested_platform": "Flipkart",
                "key_features": ["USB powered", "Multiple light modes", "Reusable for future occasions"],
                "reasoning": "Sets the party mood instantly once the sun sets."
            },
            {
                "item_name": "High-Bass Bluetooth Party Speaker with Wireless Mic",
                "category": "Entertainment",
                "estimated_price": round(ent_budget, 2),
                "description": "Portable 80W party speaker with synced LED ring lights and karaoke microphone.",
                "suggested_platform": "Amazon",
                "key_features": ["10-hour battery life", "Bass boost mode", "Bluetooth 5.3 + AUX"],
                "reasoning": "Keeps the crowd engaged with high-fidelity music and announcements."
            }
        ]

        total_cost = sum(r["estimated_price"] for r in recs)
        remaining = max(0.0, round(budget - total_cost, 2))

        return {
            "category": "party",
            "title": f"{event_type} Celebration Plan for {guests} Guests",
            "total_budget": budget,
            "estimated_total_cost": total_cost,
            "remaining_balance": remaining,
            "currency": "₹",
            "ai_insights": f"For {guests} guests with a budget of ₹{budget:,.2f}, allocating {catering_pct}% to food ensures satisfying portions without overspending. Leveraging cloud-kitchen bulk orders via Swiggy/Zomato saves up to 35% compared to traditional on-site banquets.",
            "budget_allocations": [
                {"category_name": "Food & Catering", "allocated_amount": catering_budget, "percentage": catering_pct},
                {"category_name": "Venue & Space", "allocated_amount": venue_budget, "percentage": venue_pct},
                {"category_name": "Decoration & Ambiance", "allocated_amount": decor_budget, "percentage": decor_pct},
                {"category_name": "Entertainment & Sound", "allocated_amount": ent_budget, "percentage": ent_pct}
            ],
            "recommendations": recs
        }

    # =========================================================================
    # 3. JEWELRY BUDGET PLANNER (MULTIMODAL)
    # =========================================================================
    def generate_jewelry_recommendations(
        self,
        total_budget: float,
        occasion: str,
        style_preference: str = "Contemporary",
        metal_preference: str = "Gold / Brass",
        jewelry_types: Optional[List[str]] = None,
        image_path: Optional[str] = None,
        additional_notes: str = ""
    ) -> Dict[str, Any]:
        """
        Generate jewelry recommendations based on occasion, style, and optional
        multimodal outfit image analysis.
        """
        types_str = ", ".join(jewelry_types) if jewelry_types else "Necklace, Earrings, Bangles, Rings"

        image_instruction = ""
        if image_path and Path(image_path).exists():
            image_instruction = """
An outfit image has been provided!
Carefully inspect the image:
1. Identify primary and secondary outfit fabric colors (e.g. Royal Blue, Emerald Green, Pastel Pink, Crimson Red).
2. Inspect the neckline (e.g. V-neck, sweetheart, boat neck, round neck, high collar) to suggest the ideal necklace length (choker, princess, matinee).
3. Evaluate the embellishment work (zari, sequins, embroidery, minimal print) to match jewelry tones (Antique Gold, Kundan, Polki, Rose Gold, Silver/Zircon).
Fill the 'outfit_analysis' object with color palette, recommended metals, and styling notes.
"""

        prompt = f"""
You are a celebrity fashion stylist and jewelry budget consultant for PocketSmart AI.
Analyze the user's jewelry styling request:
- Total Budget: ₹{total_budget:,.2f}
- Occasion: {occasion} (e.g. Wedding, Festive Diwali, Cocktail Party, Daily Wear, Office)
- Style Preference: {style_preference} (e.g. Traditional Temple, Modern Minimalist, Kundan, Bohemian)
- Metal / Material Preference: {metal_preference}
- Jewelry Pieces Desired: {types_str}
- Additional Notes: {additional_notes}
{image_instruction}

Generate a strictly valid JSON response adhering to this schema:
{{
  "category": "jewelry",
  "title": "{occasion} Jewelry Ensemble ({style_preference})",
  "total_budget": {total_budget},
  "estimated_total_cost": number (<= total_budget),
  "remaining_balance": number,
  "currency": "₹",
  "ai_insights": "Detailed 2-3 sentence jewelry styling guidance tailored to the occasion and budget.",
  "outfit_analysis": {{
    "analyzed": boolean,
    "primary_colors": ["Color 1", "Color 2"],
    "neckline_silhouette": "Description of neckline / garment style",
    "recommended_metals": "Best matching metals / stones",
    "styling_tip": "Specific rule of thumb for this look"
  }},
  "budget_allocations": [
    {{"category_name": "Neckwear / Sets", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Earrings / Jhumkas", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Bangles / Bracelets", "allocated_amount": number, "percentage": number}},
    {{"category_name": "Rings & Hair Accents", "allocated_amount": number, "percentage": number}}
  ],
  "recommendations": [
    {{
      "item_name": "Specific jewelry piece name",
      "category": "Necklace|Earrings|Bangles|Rings",
      "estimated_price": number,
      "description": "How this piece flatters the occasion, metal preference, and outfit.",
      "suggested_platform": "CaratLane|Amazon|Flipkart|Tanishq",
      "key_features": ["Feature 1", "Feature 2"],
      "reasoning": "Craftsmanship and aesthetic harmony"
    }}
  ]
}}
Ensure prices reflect Indian jewelry market platforms (CaratLane, Amazon, Flipkart, Tanishq).
Total cost must be <= ₹{total_budget}.
Provide 3 to 6 curated jewelry recommendations.
"""
        data = self._call_gemini_json(prompt, image_path=image_path)
        if not data:
            data = self._generate_mock_jewelry_recommendations(
                total_budget, occasion, style_preference, metal_preference, image_path
            )
            data["is_mock"] = True
        else:
            data["is_mock"] = False

        for rec in data.get("recommendations", []):
            PlatformLinker.enrich_recommendation(rec)

        return data

    def _generate_mock_jewelry_recommendations(
        self,
        budget: float,
        occasion: str,
        style: str,
        metal: str,
        image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """High-quality contextual fallback for Jewelry Planner with simulated vision insight."""
        neck_budget = round(budget * 0.50, 2)
        earrings_budget = round(budget * 0.25, 2)
        bangles_budget = round(budget * 0.15, 2)
        ring_budget = round(budget * 0.10, 2)

        has_image = bool(image_path and Path(image_path).exists())

        recs = [
            {
                "item_name": f"{style} Statement Choker / Necklace ({metal})",
                "category": "Necklace",
                "estimated_price": neck_budget,
                "description": f"Intricately crafted statement neckpiece designed for {occasion.lower()} celebrations, featuring delicate stone work.",
                "suggested_platform": "CaratLane" if budget > 15000 else "Amazon",
                "key_features": ["Skin-friendly hypoallergenic base", "Adjustable dori clasp", "Micro-plated finish"],
                "reasoning": "Serves as the focal centerpiece of the jewelry ensemble."
            },
            {
                "item_name": f"Matching {style} Chandbali / Drop Earrings",
                "category": "Earrings",
                "estimated_price": earrings_budget,
                "description": "Ergonomically weighted chandelier earrings that highlight jawline aesthetics and complement the neckpiece.",
                "suggested_platform": "Amazon",
                "key_features": ["Lightweight comfort", "Push-back closure", "Intricate filigree work"],
                "reasoning": "Creates visual symmetry without causing ear fatigue."
            },
            {
                "item_name": f"Textured {metal} Openable Kada / Bangle Pair",
                "category": "Bangles",
                "estimated_price": bangles_budget,
                "description": "Dual-tone handcrafted bangles with screw clasp mechanism, blending heritage charm with modern wearability.",
                "suggested_platform": "Flipkart",
                "key_features": ["Universal fit screw clasp", "Anti-tarnish coating", "Smooth inner edges"],
                "reasoning": "Accentuates wrist movements during social greetings."
            },
            {
                "item_name": "Adjustable Solitaire / Kundan Cocktail Ring",
                "category": "Rings",
                "estimated_price": ring_budget,
                "description": "Statement cocktail ring with cushion-cut centerpiece crystal, adding regal elegance to hands.",
                "suggested_platform": "Amazon",
                "key_features": ["Adjustable band", "Prong set stone", "High-polish luster"],
                "reasoning": "Adds subtle sparkle without competing with heavy bangles."
            }
        ]

        total_cost = sum(r["estimated_price"] for r in recs)
        remaining = max(0.0, round(budget - total_cost, 2))

        outfit_info = {
            "analyzed": has_image,
            "primary_colors": ["Warm Burgundy", "Golden Ochre"] if has_image else ["Classic Metallic", "Neutral"],
            "neckline_silhouette": "Deep V-neck / Sweetheart neckline with detailed embroidery" if has_image else "Versatile Festive Cut",
            "recommended_metals": f"{metal} with Warm Toned Gems",
            "styling_tip": "Pair a choker necklace with statement earrings to draw attention to the face while keeping wrists minimalist."
        }

        return {
            "category": "jewelry",
            "title": f"{occasion} Jewelry Ensemble ({style})",
            "total_budget": budget,
            "estimated_total_cost": total_cost,
            "remaining_balance": remaining,
            "currency": "₹",
            "ai_insights": f"For your {occasion.lower()} event with a {style.lower()} look, we prioritized 50% on a statement neckpiece and 25% on complementary earrings. This gives you a balanced, photogenic ensemble while strictly staying within your ₹{budget:,.2f} limit.",
            "outfit_analysis": outfit_info,
            "budget_allocations": [
                {"category_name": "Neckwear / Sets", "allocated_amount": neck_budget, "percentage": 50},
                {"category_name": "Earrings / Jhumkas", "allocated_amount": earrings_budget, "percentage": 25},
                {"category_name": "Bangles & Kadas", "allocated_amount": bangles_budget, "percentage": 15},
                {"category_name": "Statement Rings", "allocated_amount": ring_budget, "percentage": 10}
            ],
            "recommendations": recs
        }


# Singleton instance
gemini_service = GeminiService()
