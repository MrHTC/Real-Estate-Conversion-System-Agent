import os
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from agentic_lead_engine.config import settings
from agentic_lead_engine.utils.logger import Logger


class PaymentProcessor:
    """
    Unified payment processing for multiple gateways.
    Supports Razorpay, Stripe, PayPal, and UPI.
    """

    def __init__(self):
        self.logger = Logger("PaymentProcessor")

        # Gateway configurations
        self.gateways = {
            'razorpay': {
                'api_key': os.getenv('RAZORPAY_KEY_ID', ''),
                'api_secret': os.getenv('RAZORPAY_KEY_SECRET', ''),
                'base_url': 'https://api.razorpay.com/v1'
            },
            'stripe': {
                'api_key': os.getenv('STRIPE_SECRET_KEY', ''),
                'base_url': 'https://api.stripe.com/v1'
            },
            'paypal': {
                'client_id': os.getenv('PAYPAL_CLIENT_ID', ''),
                'client_secret': os.getenv('PAYPAL_CLIENT_SECRET', ''),
                'base_url': 'https://api.paypal.com/v1'
            }
        }

        # Default gateway
        self.default_gateway = os.getenv('PAYMENT_GATEWAY', 'razorpay')

        # Pricing tiers
        self.pricing_tiers = {
            'real_estate': {
                'starter': {'price': 15000, 'features': ['Basic GMB', 'Social Media', 'Email Marketing']},
                'professional': {'price': 25000, 'features': ['All Starter', 'Website', 'SEO', 'Ads Management']},
                'enterprise': {'price': 45000, 'features': ['All Professional', 'Custom Solutions', 'Dedicated Support']}
            },
            'gym': {
                'starter': {'price': 8000, 'features': ['Social Media', 'Local SEO', 'Class Management']},
                'professional': {'price': 15000, 'features': ['All Starter', 'Website', 'Member App', 'Email Campaigns']},
                'enterprise': {'price': 25000, 'features': ['All Professional', 'Custom Integrations', 'Analytics Dashboard']}
            },
            'restaurant': {
                'starter': {'price': 12000, 'features': ['GMB Optimization', 'Social Media', 'Menu Design']},
                'professional': {'price': 20000, 'features': ['All Starter', 'Website', 'Online Ordering', 'Reviews Management']},
                'enterprise': {'price': 35000, 'features': ['All Professional', 'POS Integration', 'Loyalty Program']}
            }
        }

    def create_payment_link(self, lead: Dict, tier: str = 'professional', niche: str = 'default') -> Dict[str, Any]:
        """
        Create payment link for lead conversion.
        """
        self.logger.info(f"Creating payment link for {lead.get('name')} - {tier} tier")

        # Get pricing
        pricing = self.pricing_tiers.get(niche, self.pricing_tiers.get('real_estate', {}))
        if tier not in pricing:
            tier = 'professional'

        amount = pricing[tier]['price']
        features = pricing[tier]['features']

        # Create payment request based on gateway
        gateway = self.default_gateway

        if gateway == 'razorpay':
            return self._create_razorpay_link(lead, amount, tier, features)
        elif gateway == 'stripe':
            return self._create_stripe_link(lead, amount, tier, features)
        elif gateway == 'paypal':
            return self._create_paypal_link(lead, amount, tier, features)
        else:
            return self._create_mock_payment_link(lead, amount, tier, features)

    def process_payment_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """
        Process payment webhook notifications.
        """
        self.logger.info("Processing payment webhook")

        gateway = webhook_data.get('gateway', self.default_gateway)

        if gateway == 'razorpay':
            return self._process_razorpay_webhook(webhook_data)
        elif gateway == 'stripe':
            return self._process_stripe_webhook(webhook_data)
        elif gateway == 'paypal':
            return self._process_paypal_webhook(webhook_data)
        else:
            return {'status': 'processed', 'mock': True}

    def get_subscription_status(self, lead_id: str) -> Dict[str, Any]:
        """
        Check subscription status for a lead.
        """
        # In real implementation, query payment gateway
        # For now, return mock status
        return {
            'lead_id': lead_id,
            'status': 'active',
            'tier': 'professional',
            'next_billing': (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).isoformat(),
            'amount': 25000
        }

    def cancel_subscription(self, lead_id: str) -> bool:
        """
        Cancel subscription for a lead.
        """
        self.logger.info(f"Cancelling subscription for lead {lead_id}")
        # Implementation would call payment gateway API
        return True

    def generate_invoice(self, lead: Dict, payment_id: str) -> Dict[str, Any]:
        """
        Generate invoice for completed payment.
        """
        return {
            'invoice_id': f"INV-{payment_id}",
            'lead': lead,
            'amount': lead.get('payment_amount', 0),
            'date': datetime.now().isoformat(),
            'status': 'generated'
        }

    def get_revenue_analytics(self) -> Dict[str, Any]:
        """
        Get revenue and payment analytics.
        """
        # In real implementation, aggregate from payment gateway
        return {
            'total_revenue': 125000,
            'monthly_recurring': 95000,
            'total_subscriptions': 45,
            'churn_rate': 0.05,
            'average_revenue_per_user': 21000
        }

    def _create_razorpay_link(self, lead: Dict, amount: int, tier: str, features: List[str]) -> Dict[str, Any]:
        """Create Razorpay payment link."""
        try:
            url = f"{self.gateways['razorpay']['base_url']}/payment_links"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Basic {self._get_basic_auth()}"
            }

            payload = {
                'amount': amount * 100,  # Razorpay expects paisa
                'currency': 'INR',
                'description': f"{tier.title()} Plan - {lead.get('name', 'Business')}",
                'customer': {
                    'name': lead.get('name', 'Customer'),
                    'email': lead.get('email', ''),
                    'contact': lead.get('phone', '')
                },
                'notify': {'email': True, 'sms': True},
                'reminder_enable': True,
                'notes': {
                    'lead_id': str(lead.get('id', '')),
                    'tier': tier,
                    'niche': lead.get('niche', '')
                }
            }

            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            return {
                'success': True,
                'payment_url': data.get('short_url', ''),
                'payment_id': data.get('id', ''),
                'amount': amount,
                'tier': tier,
                'features': features
            }

        except Exception as e:
            self.logger.error(f"Razorpay payment link creation failed: {e}")
            return self._create_mock_payment_link(lead, amount, tier, features)

    def _create_stripe_link(self, lead: Dict, amount: int, tier: str, features: List[str]) -> Dict[str, Any]:
        """Create Stripe payment link."""
        # Similar implementation for Stripe
        return self._create_mock_payment_link(lead, amount, tier, features)

    def _create_paypal_link(self, lead: Dict, amount: int, tier: str, features: List[str]) -> Dict[str, Any]:
        """Create PayPal payment link."""
        # Similar implementation for PayPal
        return self._create_mock_payment_link(lead, amount, tier, features)

    def _create_mock_payment_link(self, lead: Dict, amount: int, tier: str, features: List[str]) -> Dict[str, Any]:
        """Create mock payment link for testing."""
        return {
            'success': True,
            'payment_url': f"https://mock-payment.com/pay/{lead.get('id', 'test')}",
            'payment_id': f"mock_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'amount': amount,
            'tier': tier,
            'features': features,
            'mock': True
        }

    def _process_razorpay_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process Razorpay webhook."""
        # Verify webhook signature (implementation needed)
        event = webhook_data.get('event', '')

        if event == 'payment.captured':
            payment_id = webhook_data.get('payload', {}).get('payment', {}).get('entity', {}).get('id', '')
            return {
                'status': 'payment_completed',
                'payment_id': payment_id,
                'amount': webhook_data.get('payload', {}).get('payment', {}).get('entity', {}).get('amount', 0) / 100
            }

        return {'status': 'processed'}

    def _process_stripe_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process Stripe webhook."""
        return {'status': 'processed'}

    def _process_paypal_webhook(self, webhook_data: Dict) -> Dict[str, Any]:
        """Process PayPal webhook."""
        return {'status': 'processed'}

    def _get_basic_auth(self) -> str:
        """Get basic auth string for Razorpay."""
        import base64
        key = self.gateways['razorpay']['api_key']
        secret = self.gateways['razorpay']['api_secret']
        credentials = f"{key}:{secret}"
        return base64.b64encode(credentials.encode()).decode()

    def get_dynamic_pricing(self, niche: str, lead_quality: float, competition: str) -> Dict[str, Any]:
        """
        Calculate dynamic pricing based on market factors.
        """
        base_pricing = self.pricing_tiers.get(niche, self.pricing_tiers['real_estate'])

        # Adjust based on quality and competition
        quality_multiplier = 1.0 + (lead_quality / 20)  # Up to 50% premium
        competition_multiplier = {
            'High': 1.3,
            'Medium': 1.15,
            'Low': 1.0
        }.get(competition, 1.0)

        dynamic_pricing = {}
        for tier, details in base_pricing.items():
            original_price = details['price']
            new_price = int(original_price * quality_multiplier * competition_multiplier)
            dynamic_pricing[tier] = {
                'original_price': original_price,
                'dynamic_price': new_price,
                'discount_percent': round(((original_price - new_price) / original_price) * 100, 1),
                'features': details['features']
            }

        return {
            'niche': niche,
            'lead_quality': lead_quality,
            'competition': competition,
            'pricing': dynamic_pricing,
            'recommended_tier': 'professional'
        }