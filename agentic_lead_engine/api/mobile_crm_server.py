"""
Simple Flask server wrapper for MobileCRMAPI
Deploy this to Render.com or any WSGI server
"""

from flask import Flask, request, jsonify
import os

from agentic_lead_engine.api.mobile_crm import MobileCRMAPI

app = Flask(__name__)
api = MobileCRMAPI()
API_KEY = os.getenv("MOBILE_CRM_API_KEY", "")


def _require_api_key():
    if not API_KEY:
        return None
    key = request.headers.get("X-API-KEY") or request.args.get("api_key")
    if not key or key != API_KEY:
        return (
            jsonify({"success": False, "error": "Invalid or missing API key"}),
            401,
        )
    return None


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "mobile-crm-api"}), 200


@app.route("/api/leads", methods=["GET"])
def get_leads():
    err = _require_api_key()
    if err:
        return err
    limit = int(request.args.get("limit", 50))
    offset = int(request.args.get("offset", 0))
    min_score = request.args.get("min_score")
    max_score = request.args.get("max_score")
    lead_type = request.args.get("lead_type")
    location = request.args.get("location")

    result = api.get_leads(
        limit=limit,
        offset=offset,
        min_score=int(min_score) if min_score else None,
        max_score=int(max_score) if max_score else None,
        lead_type=lead_type,
        location=location,
    )
    return jsonify(result), 200 if result.get("success") else 500


@app.route("/api/leads/<lead_id>", methods=["GET"])
def get_lead_detail(lead_id):
    err = _require_api_key()
    if err:
        return err
    result = api.get_lead_detail(lead_id)
    return jsonify(result), 200 if result.get("success") else 404


@app.route("/api/leads/<lead_id>/status", methods=["PATCH"])
def update_lead_status(lead_id):
    err = _require_api_key()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    notes = data.get("notes", "")
    tags = data.get("tags", [])
    if not status:
        return jsonify({"success": False, "error": "status required"}), 400
    result = api.update_lead_status(lead_id, status, notes, tags)
    return jsonify(result), 200 if result.get("success") else 500


@app.route("/api/leads/<lead_id>/notes", methods=["POST"])
def add_lead_note(lead_id):
    err = _require_api_key()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    note = data.get("note", "")
    if not note:
        return jsonify({"success": False, "error": "note required"}), 400
    result = api.add_lead_note(lead_id, note)
    return jsonify(result), 200 if result.get("success") else 500


@app.route("/api/leads/<lead_id>/followups", methods=["POST"])
def schedule_followup(lead_id):
    err = _require_api_key()
    if err:
        return err
    data = request.get_json(silent=True) or {}
    followup_time = data.get("followup_time")
    notes = data.get("notes", "")
    if not followup_time:
        return (
            jsonify({"success": False, "error": "followup_time required"}),
            400,
        )
    result = api.schedule_followup(lead_id, followup_time, notes)
    return jsonify(result), 200 if result.get("success") else 500


@app.route("/api/leads/<lead_id>/analytics", methods=["GET"])
def get_lead_analytics(lead_id):
    err = _require_api_key()
    if err:
        return err
    result = api.get_lead_analytics(lead_id)
    return jsonify(result), 200 if result.get("success") else 404


@app.route("/api/dashboard", methods=["GET"])
def get_dashboard_stats():
    err = _require_api_key()
    if err:
        return err
    result = api.get_dashboard_stats()
    return jsonify(result), 200 if result.get("success") else 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
