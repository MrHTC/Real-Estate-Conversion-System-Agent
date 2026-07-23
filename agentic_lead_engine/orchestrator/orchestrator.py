from typing import List, Dict

from agentic_lead_engine.utils.csv_memory import CSVMemory
from agentic_lead_engine.utils.logger import Logger
from agentic_lead_engine.utils.whatsapp_sender import WhatsAppSender
from agentic_lead_engine.utils.ollama_client import OllamaClient
from agentic_lead_engine.config import settings
from agentic_lead_engine.agents.lead_agent_v2 import LeadAgentV2
from agentic_lead_engine.agents.qualification_agent_v2 import QualificationAgentV2
from agentic_lead_engine.agents.outreach_agent_v2 import OutreachAgentV2
from agentic_lead_engine.agents.followup_agent_v2 import FollowupAgentV2
from agentic_lead_engine.agents.analytics_agent_v2 import AnalyticsAgentV2
from agentic_lead_engine.agents.optimization_agent_v2 import OptimizationAgentV2
from agentic_lead_engine.agents.commission_agent import CommissionAgent


class Orchestrator:
    def __init__(self):
        self.logger = Logger("Orchestrator")
        self.memory = CSVMemory(settings.MEMORY_DIR)
        self.ollama = OllamaClient(api_url=settings.OLLAMA_API_URL, model=settings.OLLAMA_MODEL)
        self.whatsapp = WhatsAppSender(api_url=settings.WHATSAPP_API_URL, api_token=settings.WHATSAPP_API_TOKEN)
        self.lead_agent = LeadAgentV2()
        self.qualification_agent = QualificationAgentV2(self.ollama)
        self.outreach_agent = OutreachAgentV2(self.whatsapp)
        self.followup_agent = FollowupAgentV2()
        self.analytics_agent = AnalyticsAgentV2(self.memory)
        self.optimization_agent = OptimizationAgentV2()
        self.commission_agent = CommissionAgent(self.memory)

    def run_cycle(self, niche: str, location: str) -> Dict[str, any]:
        self.logger.info(f"Starting new cycle for {niche} in {location}")

        leads = self.lead_agent.fetch_leads(niche, location, limit=settings.LEAD_BATCH_SIZE)
        validated = self.lead_agent.validate_leads(leads)
        self.memory.save_leads(validated)

        qualified = self.qualification_agent.classify_leads(validated)
        hot_leads = [lead for lead in qualified if lead.get("quality") == "HOT"]
        self.logger.info(f"Qualified {len(hot_leads)} HOT leads")

        contactable = [lead for lead in hot_leads if not self.memory.already_contacted(lead.get("phone", ""))]
        self.logger.info(f"{len(contactable)} HOT leads available for outreach")

        outreach_records = self.outreach_agent.send_outreach(contactable, niche, location)
        for record in outreach_records:
            self.memory.record_contacted(
                lead_id=record.get("lead_id"),
                phone=record.get("phone"),
                message=record.get("message"),
                channel=record.get("channel", "whatsapp")
            )

        followups = self.followup_agent.build_followups(self.memory.get_contacted(), settings.FOLLOWUP_HOURS)
        for followup in followups:
            self.logger.info(f"Follow-up queued for {followup['phone']}: {followup['message']}")

        metrics = self.analytics_agent.compute_metrics()
        self.logger.info(f"Analytics summary: {metrics}")

        conversions = self.memory.get_conversions()
        for conv in conversions[-5:]:
            self.commission_agent.record_commission(
                lead_id=conv.get("lead_id"),
                phone=conv.get("phone"),
                deal_value=float(conv.get("amount", 0)),
                commission_type="conversion"
            )

        suggestions = self.optimization_agent.suggest_improvements(metrics)
        self.logger.info(f"Optimization suggestions: {suggestions}")

        summary = {
            "leads_generated": len(leads),
            "validated_leads": len(validated),
            "hot_leads": len(hot_leads),
            "outreach_sent": len(outreach_records),
            "followups_created": len(followups),
            "analytics": metrics,
            "optimization": suggestions
        }
        self.logger.info("Cycle complete")
        return summary
