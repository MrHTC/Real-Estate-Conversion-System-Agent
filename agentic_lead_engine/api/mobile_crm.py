"""
API Endpoints for Mobile CRM Integration
This module provides REST-like endpoints that mobile apps can consume
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os

from agentic_lead_engine.utils.csv_memory import CSVMemory
from agentic_lead_engine.config import settings
from agentic_lead_engine.utils.logger import Logger


class MobileCRMAPI:
    def __init__(self):
        self.logger = Logger("MobileCRMAPI")
        self.memory = CSVMemory(settings.MEMORY_DIR)
        # In a real implementation, this would connect to actual services
        # For now, we'll use the existing memory system
    
    # Lead Management Endpoints
    def get_leads(self, 
                  limit: int = 50, 
                  offset: int = 0, 
                  min_score: Optional[int] = None,
                  max_score: Optional[int] = None,
                  lead_type: Optional[str] = None,
                  location: Optional[str] = None) -> Dict[str, Any]:
        """Get leads with filtering options"""
        try:
            all_leads = self.memory.get_leads()
            
            # Apply filters
            filtered_leads = []
            for lead in all_leads:
                # Score filters
                try:
                    score = int(lead.get("score", 0))
                except ValueError:
                    score = 0
                if min_score is not None and score < min_score:
                    continue
                if max_score is not None and score > max_score:
                    continue
                
                # Lead type filter (based on score tiers)
                if lead_type == "hot" and score < 85:
                    continue
                elif lead_type == "warm" and (score < 60 or score >= 85):
                    continue
                elif lead_type == "cold" and score >= 60:
                    continue
                
                # Location filter
                if location:
                    lead_location = lead.get("location", "").lower()
                    if location.lower() not in lead_location:
                        continue
                
                filtered_leads.append(lead)
            
            # Apply pagination
            total = len(filtered_leads)
            paginated_leads = filtered_leads[offset:offset + limit]
            
            return {
                "success": True,
                "data": {
                    "leads": paginated_leads,
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "has_next": offset + limit < total,
                        "has_prev": offset > 0
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting leads: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lead_detail(self, lead_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific lead"""
        try:
            lead = self.memory.get_lead(lead_id)
            if not lead:
                return {"success": False, "error": "Lead not found"}
            
            # Get additional context
            contacted = self.memory.get_contacted()
            contact_history = [c for c in contacted if c.get("lead_id") == lead_id]
            
            replies = self.memory.get_replies()
            reply_history = [r for r in replies if r.get("lead_id") == lead_id]
            
            return {
                "success": True,
                "data": {
                    "lead": lead,
                    "contact_history": contact_history,
                    "reply_history": reply_history,
                    "timeline": self._build_lead_timeline(lead, contact_history, reply_history)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting lead detail: {e}")
            return {"success": False, "error": str(e)}
    
    def update_lead_status(self, 
                          lead_id: str, 
                          status: str, 
                          notes: str = "",
                          tags: List[str] = None) -> Dict[str, Any]:
        """Update lead status (for CRM swipe actions)"""
        try:
            # Validate status
            valid_statuses = ["interested", "not_interested", "maybe", "follow_up", "customer"]
            if status not in valid_statuses:
                return {"success": False, "error": f"Invalid status. Must be one of: {valid_statuses}"}
            
            success = self.memory.update_lead_status(lead_id, status, notes, tags or [])
            
            if success:
                # Log the action for analytics
                self._log_crm_action(lead_id, "status_update", {
                    "new_status": status,
                    "notes": notes,
                    "tags": tags or []
                })
                
                return {
                    "success": True,
                    "message": f"Lead status updated to {status}",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to update lead status"}
        except Exception as e:
            self.logger.error(f"Error updating lead status: {e}")
            return {"success": False, "error": str(e)}
    
    def add_lead_note(self, lead_id: str, note: str) -> Dict[str, Any]:
        """Add a note to a lead"""
        try:
            success = self.memory.add_lead_note(lead_id, note)
            
            if success:
                self._log_crm_action(lead_id, "note_added", {"note": note})
                return {
                    "success": True,
                    "message": "Note added successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to add note"}
        except Exception as e:
            self.logger.error(f"Error adding lead note: {e}")
            return {"success": False, "error": str(e)}
    
    def schedule_followup(self, 
                         lead_id: str, 
                         followup_time: str, 
                         notes: str = "") -> Dict[str, Any]:
        """Schedule a follow-up for a lead"""
        try:
            # Validate time format
            try:
                dt = datetime.fromisoformat(followup_time)
                if dt <= datetime.now():
                    return {"success": False, "error": "Follow-up time must be in the future"}
            except ValueError:
                return {"success": False, "error": "Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"}
            
            success = self.memory.schedule_followup(lead_id, followup_time, notes)
            
            if success:
                self._log_crm_action(lead_id, "followup_scheduled", {
                    "followup_time": followup_time,
                    "notes": notes
                })
                
                return {
                    "success": True,
                    "message": "Follow-up scheduled successfully",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {"success": False, "error": "Failed to schedule follow-up"}
        except Exception as e:
            self.logger.error(f"Error scheduling follow-up: {e}")
            return {"success": False, "error": str(e)}
    
    def get_lead_analytics(self, lead_id: str) -> Dict[str, Any]:
        """Get analytics and insights for a specific lead"""
        try:
            lead = self.memory.get_lead(lead_id)
            if not lead:
                return {"success": False, "error": "Lead not found"}
            
            # Get prediction
            from agentic_lead_engine.agents.analytics_agent_v2 import AnalyticsAgentV2
            analytics = AnalyticsAgentV2(self.memory)
            prediction = analytics.get_conversion_prediction(lead)
            
            # Get engagement history
            contacted = self.memory.get_contacted()
            contact_history = [c for c in contacted if c.get("lead_id") == lead_id]
            
            replies = self.memory.get_replies()
            reply_history = [r for r in replies if r.get("lead_id") == lead_id]
            
            return {
                "success": True,
                "data": {
                    "lead": lead,
                    "conversion_prediction": prediction,
                    "engagement_stats": {
                        "total_contacts": len(contact_history),
                        "total_replies": len(reply_history),
                        "last_contact": max([c.get("sent_at") for c in contact_history if c.get("sent_at") is not None], default=None),
                        "last_reply": max([r.get("received_at") for r in reply_history if r.get("received_at") is not None], default=None)
                    },
                    "recommended_actions": self._get_recommended_actions(lead, prediction)
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting lead analytics: {e}")
            return {"success": False, "error": str(e)}
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics for mobile app"""
        try:
            from agentic_lead_engine.agents.analytics_agent_v2 import AnalyticsAgentV2
            analytics = AnalyticsAgentV2(self.memory)
            metrics = analytics.compute_metrics()
            
            # Extract key metrics for dashboard
            dashboard_data = {
                "today_stats": {
                    "new_leads": metrics.get("recent_leads_24h", 0),
                    "new_contacts": 0,  # Would need time-filtered data
                    "new_replies": 0,   # Would need time-filtered data
                    "new_customers": metrics.get("recent_conversions_24h", 0)
                },
                "pipeline": {
                    "total_leads": metrics.get("total_leads", 0),
                    "hot_leads": metrics.get("hot_leads_count", 0),
                    "warm_leads": metrics.get("warm_leads_count", 0),
                    "cold_leads": metrics.get("cold_leads_count", 0),
                    "pipeline_value": metrics.get("weighted_pipeline_value", 0)
                },
                "conversion_rates": {
                    "contact_rate": f"{metrics.get('contact_rate', 0)}%",
                    "reply_rate": f"{metrics.get('reply_rate', 0)}%",
                    "overall_conversion": f"{metrics.get('overall_conversion_rate', 0)}%"
                },
                "lead_quality": {
                    "avg_score": f"{metrics.get('avg_lead_score', 0)}/100",
                    "quality_distribution": metrics.get("lead_quality_distribution", {})
                }
            }
            
            return {
                "success": True,
                "data": dashboard_data,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting dashboard stats: {e}")
            return {"success": False, "error": str(e)}
    
    # Helper methods
    def _build_lead_timeline(self, 
                           lead: Dict, 
                           contact_history: List[Dict], 
                           reply_history: List[Dict]) -> List[Dict]:
        """Build a chronological timeline of lead interactions"""
        timeline = []
        
        # Add lead creation
        timeline.append({
            "timestamp": lead.get("date_added"),
            "type": "lead_created",
            "description": "Lead entered the system",
            "data": {"lead_score": lead.get("score", 0)}
        })
        
        # Add contacts
        for contact in contact_history:
            timeline.append({
                "timestamp": contact.get("timestamp"),
                "type": "contact_made",
                "description": f"Contacted via {contact.get('channel', 'unknown')}",
                "data": {"message": contact.get("message", "")[:100]}
            })
        
        # Add replies
        for reply in reply_history:
            timeline.append({
                "timestamp": reply.get("timestamp"),
                "type": "reply_received",
                "description": "Reply received from lead",
                "data": {"reply": reply.get("reply", "")[:100]}
            })
        
        # Sort by timestamp
        timeline.sort(key=lambda x: x.get("timestamp") or "")
        return timeline
    
    def _log_crm_action(self, lead_id: str, action_type: str, data: Dict):
        """Log CRM actions for analytics and audit"""
        try:
            # In a real implementation, this would write to an audit log
            self.logger.info(f"CRM Action: {action_type} on lead {lead_id} - {data}")
        except:
            pass  # Don't let logging errors break the main flow
    
    def _get_recommended_actions(self, lead: Dict, prediction: Dict) -> List[Dict]:
        """Get recommended actions based on lead score and prediction"""
        recommendations = []
        score = lead.get("score", 0)
        prob = prediction.get("conversion_probability", 0)
        
        # High-value leads
        if score >= 85:
            recommendations.append({
                "action": "immediate_call",
                "priority": "high",
                "description": "Call immediately - high intent lead",
                "estimated_impact": "high"
            })
            recommendations.append({
                "action": "send_detailed_proposal",
                "priority": "high", 
                "description": "Send detailed property portfolio",
                "estimated_impact": "medium"
            })
        
        # Medium-value leads
        elif score >= 60:
            recommendations.append({
                "action": "schedule_followup",
                "priority": "medium",
                "description": "Schedule follow-up within 24 hours",
                "estimated_impact": "medium"
            })
            recommendations.append({
                "action": "share_market_report",
                "priority": "medium",
                "description": "Send relevant market analysis",
                "estimated_impact": "low"
            })
        
        # Lower-value leads
        else:
            recommendations.append({
                "action": "nurture_campaign",
                "priority": "low",
                "description": "Add to nurture sequence",
                "estimated_impact": "low"
            })
        
        # Based on timing
        timeline = lead.get("timeline", "").lower()
        if "immediate" in timeline:
            recommendations.append({
                "action": "expedite_process",
                "priority": "high",
                "description": "Fast-track viewing and documentation",
                "estimated_impact": "high"
            })
        
        return recommendations

# Convenience functions for easy import
def get_mobile_api() -> MobileCRMAPI:
    """Factory function to get API instance"""
    return MobileCRMAPI()

# For direct usage
if __name__ == "__main__":
    api = MobileCRMAPI()
    # Example usage
    print("Mobile CRM API initialized")
    print("Available endpoints:")
    print("- get_leads()")
    print("- get_lead_detail()")
    print("- update_lead_status()")
    print("- add_lead_note()")
    print("- schedule_followup()")
    print("- get_lead_analytics()")
    print("- get_dashboard_stats()")