import os
import json
import urllib.request
import urllib.error
from typing import Dict

from .logger import Logger


class OllamaClient:
    def __init__(self, api_url: str = None, model: str = None, timeout: int = 20):
        self.api_url = api_url or os.getenv("OLLAMA_API_URL", "http://127.0.0.1:11434/v1/outputs")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama2")
        self.timeout = timeout
        self.logger = Logger("Ollama")

    def classify_lead(self, lead: Dict) -> str:
        prompt = self._build_prompt(lead)
        self.logger.info(f"Classifying lead {lead.get('name')} using Ollama")

        if not self.api_url:
            self.logger.warn("OLLAMA_API_URL is not configured, using fallback classifier")
            return self._fallback_quality(lead)

        payload = {
            "model": self.model,
            "input": prompt,
            "temperature": 0.2,
            "max_tokens": 100
        }

        try:
            request = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = response.read().decode("utf-8")
                output = json.loads(data)
                text = self._extract_text(output)
                if text:
                    quality = self._parse_quality(text)
                    self.logger.info(f"Ollama returned quality: {quality}")
                    return quality
        except urllib.error.URLError as exc:
            self.logger.warn(f"Ollama request failed: {exc}")
        except Exception as exc:
            self.logger.warn(f"Ollama parse error: {exc}")

        return self._fallback_quality(lead)

    def _build_prompt(self, lead: Dict) -> str:
        return (
            "Classify this lead as HOT, WARM, or COLD based on the following data. "
            "Return only one of HOT, WARM, COLD.\n\n"
            f"Name: {lead.get('name')}\n"
            f"Location: {lead.get('location')}\n"
            f"Phone: {lead.get('phone')}\n"
            f"GMB status: {lead.get('gmb_status')}\n"
            f"Estimated members: {lead.get('estimated_members', 'unknown')}\n"
            f"Price range: {lead.get('price_range', 'unknown')}\n"
            f"Category: {lead.get('category', 'unknown')}\n"
        )

    def _extract_text(self, response: Dict) -> str:
        if not isinstance(response, dict):
            return ""
        if "result" in response and isinstance(response["result"], str):
            return response["result"].strip()
        if "outputs" in response and isinstance(response["outputs"], list):
            for item in response["outputs"]:
                if isinstance(item, dict):
                    content = item.get("content")
                    if isinstance(content, str):
                        return content.strip()
                    if isinstance(content, list):
                        for piece in content:
                            if isinstance(piece, str):
                                return piece.strip()
                            if isinstance(piece, dict):
                                nested = piece.get("text") or piece.get("content")
                                if isinstance(nested, str):
                                    return nested.strip()
        if "content" in response and isinstance(response["content"], str):
            return response["content"].strip()
        return ""

    def _parse_quality(self, text: str) -> str:
        text = text.strip().upper()
        for option in ["HOT", "WARM", "COLD"]:
            if option in text:
                return option
        return "WARM"

    def _fallback_quality(self, lead: Dict) -> str:
        score = 0
        status = str(lead.get("gmb_status", "")).lower()
        if "active" in status:
            score += 2
        if lead.get("phone"):
            score += 1
        if lead.get("estimated_members", 0) >= 250:
            score += 1
        if score >= 3:
            return "HOT"
        if score == 2:
            return "WARM"
        return "COLD"

    def generate_outreach_message(self, lead: Dict, analysis: Dict) -> str:
        """Generate personalized outreach message for lead."""
        classification = analysis.get('classification', 'WARM')
        niche = lead.get('niche', 'business')
        location = lead.get('location', 'your area')

        if classification == 'HOT':
            return f"Hi {lead.get('name', 'there')}! I noticed your {niche} business in {location} and wanted to connect. Based on your strong online presence, I think we could help you grow significantly. Would you be open to a quick call to discuss your goals?"
        elif classification == 'WARM':
            return f"Hello! I'm reaching out to {niche} businesses in {location} like yours. We help businesses increase their leads and revenue through proven digital marketing strategies. Interested in learning more?"
        else:
            return f"Hi there! We work with {niche} businesses in {location} to improve their online visibility and customer acquisition. Would you like to know how we can help your business grow?"

    def analyze_reply(self, message: str, lead: Dict) -> Dict:
        """Analyze incoming reply for intent and sentiment."""
        message_lower = message.lower()

        # Simple keyword-based analysis
        if any(word in message_lower for word in ['yes', 'interested', 'tell me more', 'sure', 'okay']):
            return {
                'intent': 'interested',
                'sentiment': 'positive',
                'is_conversion': False,
                'next_action': 'schedule_call'
            }
        elif any(word in message_lower for word in ['price', 'cost', 'how much', 'pricing']):
            return {
                'intent': 'pricing_inquiry',
                'sentiment': 'neutral',
                'is_conversion': False,
                'next_action': 'provide_pricing'
            }
        elif any(word in message_lower for word in ['no', 'not interested', 'stop', 'unsubscribe']):
            return {
                'intent': 'not_interested',
                'sentiment': 'negative',
                'is_conversion': False,
                'next_action': 'stop_contact'
            }
        else:
            return {
                'intent': 'neutral',
                'sentiment': 'neutral',
                'is_conversion': False,
                'next_action': 'follow_up'
            }

    def generate_response(self, analysis: Dict, lead: Dict) -> str:
        """Generate response based on reply analysis."""
        intent = analysis.get('intent', 'neutral')

        if intent == 'interested':
            return f"Great! I'd love to discuss how we can help your {lead.get('niche', 'business')} grow. What's a good time for a quick 15-minute call this week?"
        elif intent == 'pricing_inquiry':
            return f"Happy to share our pricing! For {lead.get('niche', 'business')} businesses in {lead.get('location', 'your area')}, our professional package starts at ₹25,000/month. Would you like me to send you a detailed proposal?"
        elif intent == 'not_interested':
            return "No problem at all. If you change your mind in the future, feel free to reach out. Best of luck with your business!"
        else:
            return f"Thanks for your response. Could you tell me a bit more about your current challenges with {lead.get('niche', 'business')} marketing? I'd love to help if I can."

    def generate_followup_message(self, lead: Dict, followup_data: Dict) -> str:
        """Generate follow-up message."""
        return f"Hi {lead.get('name', 'there')}! Just following up on my previous message about helping {lead.get('niche', 'your business')} grow. Have you had a chance to think about it?"

    def generate_welcome_package(self, lead: Dict) -> Dict:
        """Generate welcome package for new conversions."""
        return {
            'message': f"Welcome aboard! 🎉 Here's your quick start guide for {lead.get('niche', 'business')} growth. I'll send you the detailed onboarding materials shortly.",
            'next_steps': [
                'Account setup confirmation',
                'Welcome call scheduling',
                'Initial strategy session'
            ]
        }

    def analyze_message_effectiveness(self, message: str, lead: Dict) -> Dict:
        """Analyze how effective a message might be for conversion."""
        # Simple heuristic-based analysis
        score = 0.05  # Base conversion rate

        if 'free' in message.lower():
            score += 0.02
        if 'consultation' in message.lower():
            score += 0.02
        if 'grow' in message.lower():
            score += 0.01
        if lead.get('niche') and lead['niche'] in message.lower():
            score += 0.02
        if lead.get('location') and lead['location'] in message.lower():
            score += 0.01

        return {
            'estimated_conversion_rate': min(score, 0.15),  # Cap at 15%
            'message_length': len(message),
            'personalization_score': 0.5  # Placeholder
        }
