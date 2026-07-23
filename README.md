# Agentic Lead Engine Ecosystem

AI-powered real estate lead generation with enforced commission collection, buyer-intent scoring, and automated outreach.

## What It Does

A modular ecosystem of 7 single-purpose agents that source, score, contact, and convert real estate leads — while automatically tracking commissions, late fees, and agency subscriptions.

## Why We Built It

Real estate agencies lose 40-60% of potential deals because leads are unqualified, follow-up is inconsistent, and commissions are tracked in spreadsheets. We built this to replace gut-feeling lead selection with data-driven scoring and to enforce commission collection programmatically.

## Gaps It Fills

- **No systematic lead scoring** — agencies pick leads randomly; we score 0-100 with 6 measurable factors
- **Manual outreach at scale** — WhatsApp templates and automation replace hours of DMs
- **Commission leakage** — late fees, 60-day suspension, and TDS deduction enforced in code
- **Fragmented tools** — one framework covers sourcing, qualification, outreach, sales, analytics, conversion, and finance
- **No referral routing** — Model Y routing ensures receiving agency pays platform fee for qualified leads

## The Ecosystem

| Repo | Agent | What It Solves |
|------|-------|----------------|
| [Leads Agent](https://github.com/MrHTC/Leads-Agent-System) | `lead_agent_v2` | Fetches leads from CSV, API, and real estate portals (Magicbricks, 99acres, Housing.com) with auto source selection |
| [Qualification Agent](https://github.com/MrHTC/LEAD-QUALIFICATION-SYSTEM-REAL-ESTATE) | `qualification_agent_v2` | 0-100 scoring across contact info, legitimacy, budget, timeline, digital presence, and source quality |
| [Outreach Agent](https://github.com/MrHTC/HTANC-OUTREACH-SYSTEM) | `outreach_agent_v2` | Personalized WhatsApp outreach templates and message composer for agencies |
| [Sales Agent](https://github.com/MrHTC/Sales-Agent) | `sales_agent_v2` + `followup_agent_v2` | Handles objections, parses replies, pushes CTAs, and schedules automated follow-ups |
| [Analytics Agent](https://github.com/MrHTC/Real-Estate-Lead-Analytics-Agent) | `analytics_agent_v2` + `optimization_agent_v2` | Funnel metrics, conversion rates, and AI-driven optimization suggestions |
| [Conversion Agent](https://github.com/MrHTC/Real-Estate-Conversion-System-Agent) | `conversion_agent_v2` | Dynamic pricing engine, deal routing, and referral Model Y activation |
| [Commission Agent](https://github.com/MrHTC/Commission-Agent) | `commission_agent.py` | 10%/3% splits, Net 15 invoicing, 2%/week late fees, 60-day suspension, 1% TDS |

## What More Can Be Done

- Replace mock/scraped leads with **live Meta Lead Ads** and **Google Local Services Ads** integrations
- Add **machine learning** for conversion likelihood prediction based on historical closure data
- Launch **React Native mobile CRM** with swipe-based lead management
- Integrate **Razorpay** for automated invoice generation and payment reconciliation
- Expand to **5+ Indian cities** with localized lead sources and pricing tiers
- Build **agency dashboard** with real-time funnel visualization and agent performance leaderboards

## Quick Start

```bash
git clone https://github.com/MrHTC/AGENTIC-LEAD-ENGINE.git
cd AGENTIC-LEAD-ENGINE
cp .env.example .env
pip install -r requirements.txt
python run.py cycle real_estate Delhi
```

## Demo

![Demo GIF](docs/demo.gif)

## Architecture

```
AGENTIC-LEAD-ENGINE/
├── agents/
│   ├── lead_source_adapter.py       # CSV / API / mock / real-estate portal sources
│   ├── qualification_agent_v2.py    # 6-factor scoring + tiers
│   ├── outreach_agent_v2.py         # WhatsApp templates
│   ├── commission_agent.py          # Splits, late fees, suspension
│   ├── analytics_agent_v2.py        # Metrics
│   ├── conversion_agent_v2.py       # Pricing + referral routing
│   ├── followup_agent_v2.py         # Follow-up scheduling
│   ├── sales_agent_v2.py            # Reply handling
│   ├── lead_agent_v2.py             # Validation
│   └── optimization_agent_v2.py     # Suggestions
├── orchestrator/
│   └── orchestrator.py              # Main pipeline
├── api/
│   ├── mobile_crm.py                # CRM logic
│   └── mobile_crm_server.py         # Flask server
├── utils/
│   ├── csv_memory.py                # Memory tables: leads, contacted, replies, conversions, commissions, invoices
│   ├── logger.py                    # Logging
│   ├── ollama_client.py             # AI classification
│   └── whatsapp_sender.py           # WhatsApp integration
├── config/
│   └── settings.py                  # Environment settings
├── docs/
│   ├── contracts/                   # Service agreement, lead buyer agreement
│   ├── legal/                       # Terms of service, privacy policy
│   └── policies/                    # Commission, late payment, quality SLA
├── requirements.txt
├── .env.example
├── .gitignore
├── LICENSE
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
└── run.py                           # CLI entry point
```

## Lead Scoring Model

Every lead gets a 0-100 score across:

- **Contact info** (0-20): phone, email, location
- **Business legitimacy** (0-20): GMB status, category, team size
- **Financial indicators** (0-15): price range, budget signals
- **Engagement readiness** (0-15): existing score, tags, timeline
- **Market demand** (0-15): location presence, niche match
- **Digital presence** (0-15): email, website

Tiers:

| Tier | Score range |
|------|-------------|
| COLD | 0-59 |
| WARM | 60-84 |
| HOT | 85-100 |

## Commission & Payment Rules

- On deal closure: platform gets 10%, source partner gets 3%
- Invoice due Net 15
- Late fee: 2% per week after 15-day grace
- Suspension: after 60 days overdue
- TDS: 1% under Section 194H (India)

## Mobile CRM API

Run the API server:

```bash
python run.py api
```

Endpoints (all require `X-API-KEY` or `?api_key=` if `MOBILE_CRM_API_KEY` is set):

- `GET /api/health`
- `GET /api/leads`
- `GET /api/leads/<id>`
- `PATCH /api/leads/<id>/status`
- `POST /api/leads/<id>/notes`
- `POST /api/leads/<id>/followups`
- `GET /api/leads/<id>/analytics`
- `GET /api/dashboard`

## Requirements

- Python 3.9+
- Flask (for API mode)
- See `requirements.txt`

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing](CONTRIBUTING.md)
- [License](LICENSE)

## Topics

`real-estate` `lead-generation` `automation` `python` `whatsapp` `sales` `analytics` `conversion` `qualification` `commission` `crm` `buyer-intent` `ai` `flask` `api`
