import csv
import os
from pathlib import Path
from typing import Dict, List, Optional

from .logger import Logger


class CSVMemory:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or Path(__file__).resolve().parent.parent / "memory")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logger = Logger("Memory")
        self.files = {
            "leads": ["id", "name", "phone", "location", "category", "niche", "gmb_status", "quality", "price_range", "estimated_members", "date_added", "score", "status", "notes", "tags"],
            "contacted": ["lead_id", "phone", "message", "channel", "status", "sent_at"],
            "replies": ["lead_id", "phone", "message", "response", "received_at"],
            "conversions": ["lead_id", "phone", "amount", "conversion_date", "notes"],
            "commissions": ["lead_id", "phone", "agent_id", "source", "deal_value", "commission_type", "rate", "amount", "currency", "status", "penalty", "due_date", "created_at", "paid_at"],
            "invoices": ["invoice_id", "lead_id", "agent_id", "amount", "tax", "total", "currency", "status", "due_date", "issued_at", "paid_at"]
        }
        self._ensure_files()

    def _ensure_files(self) -> None:
        for name, headers in self.files.items():
            path = self.base_dir / f"{name}.csv"
            if not path.exists():
                with path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                self.logger.info(f"Created memory file: {path}")

    def _read(self, filename: str) -> List[Dict[str, str]]:
        path = self.base_dir / filename
        if not path.exists():
            return []
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    def _append(self, filename: str, row: Dict[str, str]) -> None:
        path = self.base_dir / filename
        with path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.files[filename.replace('.csv','')])
            writer.writerow(row)

    def get_commissions(self) -> List[Dict[str, str]]:
        return self._read("commissions.csv")

    def get_invoices(self) -> List[Dict[str, str]]:
        return self._read("invoices.csv")

    def save_leads(self, leads: List[Dict]) -> None:
        path = self.base_dir / "leads.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.files["leads"])
            writer.writeheader()
            for lead in leads:
                clean = {key: str(lead.get(key, "")) for key in self.files["leads"]}
                writer.writerow(clean)
        self.logger.info(f"Saved {len(leads)} leads to {path}")

    def get_leads(self) -> List[Dict[str, str]]:
        return self._read("leads.csv")

    def get_contacted(self) -> List[Dict[str, str]]:
        return self._read("contacted.csv")

    def get_replies(self) -> List[Dict[str, str]]:
        return self._read("replies.csv")

    def get_conversions(self) -> List[Dict[str, str]]:
        return self._read("conversions.csv")

    def already_contacted(self, phone: str) -> bool:
        phone = self._normalize_phone(phone)
        return any(self._normalize_phone(row.get("phone", "")) == phone for row in self.get_contacted())

    def record_contacted(self, lead_id: str, phone: str, message: str, channel: str = "whatsapp") -> None:
        row = {
            "lead_id": str(lead_id),
            "phone": str(phone),
            "message": message,
            "channel": channel,
            "status": "sent",
            "sent_at": self._now_iso()
        }
        self._append("contacted.csv", row)
        self.logger.info(f"Recorded outreach to {phone}")

    def record_reply(self, lead_id: str, phone: str, response: str) -> None:
        row = {
            "lead_id": str(lead_id),
            "phone": str(phone),
            "message": "",
            "response": response,
            "received_at": self._now_iso()
        }
        self._append("replies.csv", row)
        self.logger.info(f"Recorded reply from {phone}: {response}")

    def record_conversion(self, lead_id: str, phone: str, amount: str, notes: str = "") -> None:
        row = {
            "lead_id": str(lead_id),
            "phone": str(phone),
            "amount": str(amount),
            "conversion_date": self._now_iso(),
            "notes": notes
        }
        self._append("conversions.csv", row)
        self.logger.info(f"Recorded conversion for {phone}")

    def _normalize_phone(self, phone: str) -> str:
        return ''.join(ch for ch in str(phone) if ch.isdigit())

    def _now_iso(self) -> str:
        from datetime import datetime
        return datetime.now().isoformat(timespec="seconds")
