from typing import Dict, List

from agentic_lead_engine.utils.logger import Logger


class ConversionAgentV2:
    def __init__(self):
        self.logger = Logger("ConversionBot")
        self.templates = {
            "real_estate": [
                (
                    "Hi {name}, I noticed your Meerut listings and wanted to share a fast way to convert more inquiries into booked visits. "
                    "Our WhatsApp follow-up system closes leads in 24-48h with a single message flow."
                ),
                (
                    "Quick note, {name}: we help real estate teams in Meerut turn online property views into confirmed site visits using automated WhatsApp replies. "
                    "Would you like a short plan for your current listings?"
                )
            ],
            "gym": [
                (
                    "Hi {name}, we help gyms fill classes faster by turning local search traffic into WhatsApp bookings. "
                    "I can share a proven 2-message flow that delivers more signups."
                ),
                (
                    "Hey {name}, local gym leads often drop off before booking. We keep them engaged with WhatsApp follow-up and appointment prompts. "
                    "Want that for your studio?"
                )
            ],
            "default": [
                (
                    "Hi {name}, we help local businesses convert more enquiries into paying customers using short, high-converting WhatsApp messages. "
                    "If you'd like, I can create a quick conversion plan for {location}."
                ),
                (
                    "Hi {name}, many businesses miss revenue by not following up instantly. Our conversion workflow sends the right message at the right time and captures more sales."
                )
            ]
        }

    def build_conversion_flow(self, leads: List[Dict], niche: str, location: str) -> List[Dict]:
        template_set = self.templates.get(niche, self.templates["default"])
        records = []
        for idx, lead in enumerate(leads):
            name = lead.get("name", "there").split()[0]
            message = template_set[idx % len(template_set)].format(name=name, location=location)
            records.append({
                "lead_id": lead.get("id"),
                "phone": lead.get("phone"),
                "message": message,
                "channel": "whatsapp",
                "stage": "conversion_followup"
            })
        self.logger.info(f"Built conversion flow for {len(records)} leads")
        return records

    def recommend_pricing(self, niche: str, budget: str = None) -> Dict[str, str]:
        pricing = {
            "real_estate": {
                "base_offer": "₹15,000/month",
                "upsell": "premium property funnel + virtual tour support for ₹25,000/month",
                "notes": "High-value listings and developers pay for consistent lead conversion." 
            },
            "gym": {
                "base_offer": "₹20,000/month",
                "upsell": "membership automation + retention flow for ₹30,000/month",
                "notes": "Recurring gym clients make this a strong ROI play."
            }
        }
        return pricing.get(niche, {
            "base_offer": "₹18,000/month",
            "upsell": "add dedicated follow-up and booking workflows",
            "notes": "Target local businesses with repeat customers."
        })
