import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import time
from datetime import datetime, timedelta

from agentic_lead_engine.config import settings
from agentic_lead_engine.utils.logger import Logger
from agentic_lead_engine.agents.lead_source_adapter import LeadSourceAdapter
from agentic_lead_engine.utils.ollama_client import OllamaClient
from agentic_lead_engine.utils.whatsapp_sender import WhatsAppSender
from agentic_lead_engine.memory.memory_manager import MemoryManager


class IntegrationManager:
    """
    Unified connector for all external tools and services.
    Handles lead ingestion, qualification, outreach, payments, and analytics.
    """

    def __init__(self):
        self.logger = Logger("IntegrationManager")

        # Core connectors
        self.lead_source = LeadSourceAdapter()
        self.ai_client = OllamaClient()
        self.messenger = WhatsAppSender()
        self.memory = MemoryManager()

        # Analytics for market validation
        self.analytics = {
            'leads_processed': 0,
            'conversions': 0,
            'revenue': 0.0,
            'niche_performance': {},
            'source_performance': {},
            'message_performance': {}
        }

        self.load_analytics()

    def validate_market_demand(self, niche: str, location: str) -> Dict[str, Any]:
        """
        Market demand validation: Analyze lead quality, conversion potential, pricing.
        """
        self.logger.info(f"Validating market demand for {niche} in {location}")

        # Get sample leads
        sample_leads = self.lead_source.fetch_leads(niche, location, limit=10)

        # Analyze lead quality
        quality_score = self._analyze_lead_quality(sample_leads)

        # Estimate conversion potential
        conversion_potential = self._estimate_conversion_potential(niche, sample_leads)

        # Suggest optimal pricing
        pricing_recommendation = self._suggest_pricing(niche, location, quality_score)

        # Competition analysis
        competition = self._analyze_competition(niche, location)

        result = {
            'niche': niche,
            'location': location,
            'lead_quality_score': quality_score,
            'conversion_potential': conversion_potential,
            'recommended_pricing': pricing_recommendation,
            'competition_level': competition,
            'market_readiness': 'High' if quality_score > 7 and conversion_potential > 0.15 else 'Medium' if quality_score > 5 else 'Low',
            'sample_size': len(sample_leads)
        }

        self.logger.info(f"Market validation complete: {result['market_readiness']} readiness")
        return result

    def find_best_lead_sources(self, niches: List[str], locations: List[str]) -> Dict[str, Any]:
        """
        Find best performing lead sources for given niches/locations.
        """
        self.logger.info(f"Finding best lead sources for {len(niches)} niches, {len(locations)} locations")

        results = {}
        for niche in niches:
            for location in locations:
                # Test different sources
                source_performance = {}
                for source_type in ['mock', 'csv', 'api']:
                    try:
                        # Temporarily switch source
                        original_source = os.environ.get('V2_LEAD_SOURCE', 'mock')
                        os.environ['V2_LEAD_SOURCE'] = source_type

                        adapter = LeadSourceAdapter()
                        leads = adapter.fetch_leads(niche, location, limit=20)

                        if leads:
                            quality = self._analyze_lead_quality(leads)
                            source_performance[source_type] = {
                                'leads_found': len(leads),
                                'quality_score': quality,
                                'cost_estimate': self._estimate_source_cost(source_type, len(leads))
                            }

                        # Restore original
                        os.environ['V2_LEAD_SOURCE'] = original_source

                    except Exception as e:
                        self.logger.warn(f"Error testing {source_type} for {niche}: {e}")

                if source_performance:
                    best_source = max(source_performance.items(), key=lambda x: x[1]['quality_score'])
                    results[f"{niche}_{location}"] = {
                        'best_source': best_source[0],
                        'performance': best_source[1],
                        'alternatives': source_performance
                    }

        return results

    def tune_messages_for_conversion(self, niche: str, location: str, iterations: int = 5) -> Dict[str, Any]:
        """
        A/B test message variations for highest conversion rates.
        """
        self.logger.info(f"Tuning messages for {niche} in {location} with {iterations} iterations")

        # Get sample leads
        leads = self.lead_source.fetch_leads(niche, location, limit=20)

        # Generate message variations
        message_templates = self._generate_message_variations(niche, location)

        # Test each variation
        results = {}
        for i, template in enumerate(message_templates):
            conversion_rate = self._test_message_conversion(template, leads[:5])  # Test on subset
            results[f"variation_{i+1}"] = {
                'template': template,
                'conversion_rate': conversion_rate,
                'sample_size': len(leads[:5])
            }

        # Find best performing
        best_variation = max(results.items(), key=lambda x: x[1]['conversion_rate'])

        # Update analytics
        self.analytics['message_performance'][niche] = {
            'best_conversion_rate': best_variation[1]['conversion_rate'],
            'best_template': best_variation[1]['template'],
            'tested_at': datetime.now().isoformat()
        }
        self.save_analytics()

        return {
            'best_message': best_variation[1]['template'],
            'conversion_rate': best_variation[1]['conversion_rate'],
            'all_results': results
        }

    def process_lead_autonomously(self, lead: Dict) -> Dict[str, Any]:
        """
        Full autonomous processing: qualify → message → send → track → convert.
        """
        self.logger.info(f"Processing lead autonomously: {lead.get('name', 'Unknown')}")

        # 1. Qualify lead with AI
        classification = self.ai_client.classify_lead(lead)
        qualified = classification in ['HOT', 'WARM']  # HOT and WARM leads are qualified

        if qualified:
            # 2. Generate conversion-focused message
            message = self.ai_client.generate_outreach_message(lead, {'classification': classification})

            # 3. Send via WhatsApp
            send_result = self.messenger.send_message(lead['phone'], message)

            # 4. Record in memory
            self.memory.record_contact(lead, message, send_result)

            # 5. Schedule follow-up
            followup_time = datetime.now() + timedelta(hours=settings.FOLLOWUP_HOURS)
            self.memory.schedule_followup(lead['id'], followup_time.isoformat())

            # 6. Update analytics
            self.analytics['leads_processed'] += 1
            niche = lead.get('niche', 'unknown')
            if niche not in self.analytics['niche_performance']:
                self.analytics['niche_performance'][niche] = {'processed': 0, 'converted': 0}
            self.analytics['niche_performance'][niche]['processed'] += 1

            self.save_analytics()

            return {
                'status': 'processed',
                'qualified': True,
                'classification': classification,
                'message_sent': send_result.get('success', False),
                'followup_scheduled': followup_time.isoformat()
            }
        else:
            # Not qualified - still record for analytics
            self.memory.record_unqualified_lead(lead)
            return {'status': 'not_qualified', 'qualified': False, 'classification': classification}

    def handle_incoming_message(self, phone: str, message: str) -> Dict[str, Any]:
        """
        Handle incoming replies and objections.
        """
        self.logger.info(f"Handling incoming message from {phone}")

        # Find lead in memory
        lead = self.memory.find_lead_by_phone(phone)
        if not lead:
            return {'status': 'lead_not_found'}

        # Analyze reply with AI
        analysis = self.ai_client.analyze_reply(message, lead)

        # Generate response
        response = self.ai_client.generate_response(analysis, lead)

        # Send response
        send_result = self.messenger.send_message(phone, response)

        # Update memory
        self.memory.record_reply(lead['id'], message, response, analysis)

        # Check for conversion
        if analysis.get('is_conversion', False):
            self.analytics['conversions'] += 1
            revenue = analysis.get('estimated_value', 0)
            self.analytics['revenue'] += revenue

            niche = lead.get('niche', 'unknown')
            if niche in self.analytics['niche_performance']:
                self.analytics['niche_performance'][niche]['converted'] += 1

            self.save_analytics()

        return {
            'status': 'responded',
            'analysis': analysis,
            'response_sent': send_result.get('success', False),
            'is_conversion': analysis.get('is_conversion', False)
        }

    def get_autonomous_operations_status(self) -> Dict[str, Any]:
        """
        Status for autonomous operation monitoring.
        """
        return {
            'analytics': self.analytics,
            'pending_followups': len(self.memory.get_pending_followups()),
            'active_leads': len(self.memory.get_active_leads()),
            'last_updated': datetime.now().isoformat()
        }

    def quick_service_onboarding(self, lead: Dict) -> Dict[str, Any]:
        """
        Quick automated onboarding for converted leads.
        """
        self.logger.info(f"Starting quick service onboarding for {lead.get('name')}")

        # Generate welcome package
        welcome_content = self.ai_client.generate_welcome_package(lead)

        # Send onboarding materials
        self.messenger.send_message(lead['phone'], welcome_content['message'])

        # Schedule onboarding calls/tasks
        tasks = [
            {'type': 'call', 'description': 'Initial consultation call', 'due_hours': 2},
            {'type': 'setup', 'description': 'Account setup and configuration', 'due_hours': 4},
            {'type': 'training', 'description': 'Quick start training session', 'due_hours': 24}
        ]

        for task in tasks:
            due_time = datetime.now() + timedelta(hours=task['due_hours'])
            self.memory.schedule_task(lead['id'], task, due_time.isoformat())

        return {
            'status': 'onboarded',
            'welcome_sent': True,
            'tasks_scheduled': len(tasks),
            'estimated_completion_hours': 24
        }

    # Helper methods
    def _analyze_lead_quality(self, leads: List[Dict]) -> float:
        """Score lead quality 0-10 based on completeness and business indicators."""
        if not leads:
            return 0.0

        total_score = 0
        for lead in leads:
            score = 0
            if lead.get('phone'): score += 2
            if lead.get('email'): score += 1
            if lead.get('gmb_status') == 'Active': score += 2
            if lead.get('price_range'): score += 1
            if lead.get('estimated_members', 0) > 10: score += 1
            if lead.get('location') and 'sector' in lead['location'].lower(): score += 1
            total_score += min(score, 10)  # Cap at 10

        return round(total_score / len(leads), 1)

    def _estimate_conversion_potential(self, niche: str, leads: List[Dict]) -> float:
        """Estimate conversion rate based on niche and lead quality."""
        base_rates = {
            'real_estate': 0.12,
            'gym': 0.08,
            'restaurant': 0.15,
            'retail': 0.10,
            'default': 0.08
        }

        base_rate = base_rates.get(niche, base_rates['default'])
        quality_bonus = self._analyze_lead_quality(leads) / 100  # Small bonus

        return min(base_rate + quality_bonus, 0.25)  # Cap at 25%

    def _suggest_pricing(self, niche: str, location: str, quality_score: float) -> Dict[str, Any]:
        """Suggest optimal pricing based on market factors."""
        base_prices = {
            'real_estate': {'starter': 15000, 'professional': 25000, 'enterprise': 45000},
            'gym': {'starter': 8000, 'professional': 15000, 'enterprise': 25000},
            'restaurant': {'starter': 12000, 'professional': 20000, 'enterprise': 35000},
            'default': {'starter': 10000, 'professional': 18000, 'enterprise': 30000}
        }

        prices = base_prices.get(niche, base_prices['default'])

        # Adjust based on quality and location premium
        location_multiplier = 1.2 if 'meerut' in location.lower() else 1.0
        quality_multiplier = 1.0 + (quality_score / 20)  # Up to 50% premium for high quality

        adjusted_prices = {}
        for tier, price in prices.items():
            adjusted_prices[tier] = int(price * location_multiplier * quality_multiplier)

        return {
            'currency': 'INR',
            'monthly_prices': adjusted_prices,
            'recommended_tier': 'professional' if quality_score > 7 else 'starter',
            'estimated_ltv': adjusted_prices['professional'] * 12  # Annual value
        }

    def _analyze_competition(self, niche: str, location: str) -> str:
        """Simple competition analysis based on lead volume."""
        sample_size = len(self.lead_source.fetch_leads(niche, location, limit=50))

        if sample_size > 30:
            return 'High'
        elif sample_size > 15:
            return 'Medium'
        else:
            return 'Low'

    def _estimate_source_cost(self, source_type: str, leads_count: int) -> float:
        """Estimate cost per lead for different sources."""
        costs = {
            'mock': 0.0,
            'csv': 0.10,  # Manual curation cost
            'api': 0.50   # API service cost
        }
        return costs.get(source_type, 0.0) * leads_count

    def _generate_message_variations(self, niche: str, location: str) -> List[str]:
        """Generate different message templates for A/B testing."""
        templates = [
            f"Hi! I'm helping {niche} businesses in {location} grow their online presence. Interested in a free consultation?",
            f"Hello! We specialize in {niche} marketing for {location} businesses. Ready to increase your leads by 300%?",
            f"Hey there! As a {niche} owner in {location}, are you struggling with customer acquisition? We can help!",
            f"Quick question: How much are you spending monthly on {niche} marketing in {location}? We might save you money.",
            f"Hi {niche} business! We're seeing amazing results for {location} companies. Want to see our case studies?"
        ]
        return templates

    def _test_message_conversion(self, template: str, leads: List[Dict]) -> float:
        """Simulate conversion testing for message templates."""
        # In real implementation, this would send actual messages and track responses
        # For now, use AI to estimate conversion potential
        try:
            analysis = self.ai_client.analyze_message_effectiveness(template, leads[0] if leads else {})
            return analysis.get('estimated_conversion_rate', 0.05)
        except:
            return 0.05  # Default fallback

    def load_analytics(self):
        """Load analytics from persistent storage."""
        analytics_file = Path(settings.MEMORY_DIR) / "analytics.json"
        if analytics_file.exists():
            try:
                with open(analytics_file, 'r') as f:
                    self.analytics.update(json.load(f))
            except Exception as e:
                self.logger.warn(f"Failed to load analytics: {e}")

    def save_analytics(self):
        """Save analytics to persistent storage."""
        analytics_file = Path(settings.MEMORY_DIR) / "analytics.json"
        analytics_file.parent.mkdir(exist_ok=True)
        try:
            with open(analytics_file, 'w') as f:
                json.dump(self.analytics, f, indent=2)
        except Exception as e:
            self.logger.warn(f"Failed to save analytics: {e}")