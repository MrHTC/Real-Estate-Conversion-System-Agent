# Real Estate Conversion System Agent

Conversion flow engine with dynamic pricing and deal routing for real estate leads.

## What it does

- Builds conversion flows based on lead score and agency tier
- Applies dynamic pricing based on lead quality and city
- Routes deals to subscribed agencies via Model Y referral
- Generates invoices and tracks deal status
- Integrates with payment processors (Razorpay, Stripe)

## Pricing tiers

| Tier | Score | Price (INR) | Characteristics |
|------|-------|-------------|-----------------|
| Cold | 0-59 | ₹50-150 | Basic contact, low intent |
| Warm | 60-84 | ₹150-500 | Verified contact, medium intent |
| Hot | 85-100 | ₹500-1,500 | High intent, budget/timeline defined |
| Premium | 86-100 | ₹1,500-5,000+ | Exclusive, verified funds, immediate timeline |

## How it fits in the system

This agent receives scored leads from the `Qualification Agent` and:
- Prices leads for sale to agencies
- Activates referral Model Y routing
- Creates invoices for `Commission Agent`
- Tracks deal status for `Analytics Agent`

## Use independently

```bash
git clone https://github.com/MrHTC/Real-Estate-Conversion-System-Agent.git
cd Real-Estate-Conversion-System-Agent
cp .env.example .env
pip install -e .
python run.py conversion
```

## Requirements

- Python 3.9+
- `python-dotenv`
- `requests`

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `PAYMENT_GATEWAY` | `razorpay` | Payment processor |
| `RAZORPAY_KEY_ID` | — | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | — | Razorpay key secret |
| `V2_DEFAULT_CITY` | `delhi` | Default city |
| `V2_DEFAULT_PROPERTY_TYPE` | `residential_land` | Default niche |
