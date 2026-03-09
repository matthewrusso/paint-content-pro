"""
review/server.py — Flask web server for the draft review UI.

Routes:
  GET  /                  — show all pending drafts
  POST /approve/<id>      — approve a draft (optionally with edited text)
  POST /reject/<id>       — reject a draft with optional reason
  GET  /history           — show approved + rejected drafts
"""

import sys
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

# Make parent agent/ directory importable
sys.path.insert(0, str(Path(__file__).parent.parent))

import updater

app = Flask(__name__, template_folder="templates")
app.secret_key = "pcp-review-local-only"


@app.route("/")
def index():
    pending = updater.get_pending_drafts()
    summary = updater.queue_summary()
    return render_template("index.html", drafts=pending, summary=summary, view="pending")


@app.route("/history")
def history():
    all_drafts = updater.get_all_drafts()
    done = [d for d in all_drafts if d.get("status") in ("approved", "rejected")]
    done_sorted = sorted(done, key=lambda d: d.get("approved_at") or d.get("rejected_at") or "", reverse=True)
    summary = updater.queue_summary()
    return render_template("index.html", drafts=done_sorted, summary=summary, view="history")


@app.route("/approve/<draft_id>", methods=["POST"])
def approve(draft_id):
    edited_text = request.form.get("draft_text") or None
    try:
        updater.approve(draft_id, edited_text=edited_text)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return redirect(url_for("index"))


@app.route("/reject/<draft_id>", methods=["POST"])
def reject(draft_id):
    reason = request.form.get("reason") or None
    try:
        updater.reject(draft_id, reason=reason)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    return redirect(url_for("index"))
