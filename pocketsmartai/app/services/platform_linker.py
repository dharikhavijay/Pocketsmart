import urllib.parse
from typing import Dict, Any


class PlatformLinker:
    """
    Generates verified search and direct navigation links for e-commerce,
    food delivery, hospitality, and home decor platforms.
    """

    PLATFORM_URL_TEMPLATES: Dict[str, str] = {
        "amazon": "https://www.amazon.in/s?k={query}",
        "flipkart": "https://www.flipkart.com/search?q={query}",
        "ikea": "https://www.ikea.com/in/en/search/?q={query}",
        "swiggy": "https://www.swiggy.com/search?query={query}",
        "zomato": "https://www.zomato.com/search?q={query}",
        "oyo": "https://www.oyorooms.com/",
        "caratlane": "https://www.caratlane.com/search?q={query}",
        "tanishq": "https://www.tanishq.co.in/search?q={query}",
        "myntra": "https://www.myntra.com/{query}",
    }

    PLATFORM_META: Dict[str, Dict[str, str]] = {
        "amazon": {
            "name": "Amazon",
            "badge_class": "badge-amazon",
            "icon": "fa-brands fa-amazon",
            "color": "#FF9900",
        },
        "flipkart": {
            "name": "Flipkart",
            "badge_class": "badge-flipkart",
            "icon": "fa-solid fa-cart-shopping",
            "color": "#2874F0",
        },
        "ikea": {
            "name": "IKEA",
            "badge_class": "badge-ikea",
            "icon": "fa-solid fa-couch",
            "color": "#0058A3",
        },
        "swiggy": {
            "name": "Swiggy",
            "badge_class": "badge-swiggy",
            "icon": "fa-solid fa-utensils",
            "color": "#FC8019",
        },
        "zomato": {
            "name": "Zomato",
            "badge_class": "badge-zomato",
            "icon": "fa-solid fa-bowl-food",
            "color": "#CB202D",
        },
        "oyo": {
            "name": "OYO Rooms",
            "badge_class": "badge-oyo",
            "icon": "fa-solid fa-hotel",
            "color": "#EE2E24",
        },
        "caratlane": {
            "name": "CaratLane",
            "badge_class": "badge-caratlane",
            "icon": "fa-solid fa-gem",
            "color": "#9C27B0",
        },
        "tanishq": {
            "name": "Tanishq",
            "badge_class": "badge-tanishq",
            "icon": "fa-solid fa-ring",
            "color": "#B8860B",
        },
    }

    @classmethod
    def get_search_url(cls, platform: str, query: str) -> str:
        """Construct safe search URL for a given platform and search term."""
        normalized_platform = platform.lower().strip()
        encoded_query = urllib.parse.quote_plus(query.strip())

        for key, template in cls.PLATFORM_URL_TEMPLATES.items():
            if key in normalized_platform:
                return template.format(query=encoded_query)

        # Default fallback to Google Search
        return f"https://www.google.com/search?q={encoded_query}+{urllib.parse.quote_plus(platform)}"

    @classmethod
    def get_platform_info(cls, platform: str) -> Dict[str, str]:
        """Get visual badge styling and icon for a platform."""
        normalized_platform = platform.lower().strip()
        for key, meta in cls.PLATFORM_META.items():
            if key in normalized_platform:
                return meta
        return {
            "name": platform.title(),
            "badge_class": "badge-secondary",
            "icon": "fa-solid fa-bag-shopping",
            "color": "#6c757d",
        }

    @classmethod
    def enrich_recommendation(cls, item_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure item has valid search URL and platform metadata."""
        platform = item_dict.get("suggested_platform", "Amazon")
        name = item_dict.get("item_name", "")
        category = item_dict.get("category", "")
        search_query = f"{name} {category}".strip()

        if not item_dict.get("platform_url"):
            item_dict["platform_url"] = cls.get_search_url(platform, search_query)

        item_dict["platform_meta"] = cls.get_platform_info(platform)
        return item_dict
