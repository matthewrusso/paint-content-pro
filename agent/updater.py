"""
updater.py — State management for queue.yaml and content-topics.yaml.

Called by both the CLI agent and the Flask review server after Matt
approves, edits, or rejects a draft.
"""

from datetime import date
from pathlib import Path

import yaml


ROOT = Path(__file__).parent.parent
TOPICS_FILE = ROOT / "content-topics.yaml"
QUEUE_FILE = Path(__file__).parent / "queue.yaml"


def _load_queue() -> dict:
    with open(QUEUE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {"drafts": []}


def _save_queue(data: dict) -> None:
    with open(QUEUE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _load_topics() -> dict:
    with open(TOPICS_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _save_topics(data: dict) -> None:
    with open(TOPICS_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def _find_draft(queue_data: dict, draft_id: str) -> dict | None:
    for d in queue_data.get("drafts", []):
        if d.get("id") == draft_id:
            return d
    return None


def append_draft(draft: dict) -> None:
    """Add a new draft to queue.yaml."""
    data = _load_queue()
    data.setdefault("drafts", []).append(draft)
    _save_queue(data)


def approve(draft_id: str, edited_text: str | None = None) -> dict:
    """
    Mark a draft as approved in queue.yaml.
    Update content-topics.yaml: status→posted, times_used++, last_used→today.
    Returns the updated draft dict.
    """
    queue_data = _load_queue()
    draft = _find_draft(queue_data, draft_id)
    if not draft:
        raise ValueError(f"Draft '{draft_id}' not found in queue.")

    if edited_text is not None:
        draft["draft"] = edited_text
        draft["edited"] = True
    draft["status"] = "approved"
    draft["approved_at"] = date.today().isoformat()
    _save_queue(queue_data)

    # Update the source topic in content-topics.yaml
    topic_id = draft.get("topic_id")
    if topic_id:
        topics_data = _load_topics()
        for topic in topics_data.get("topics", []):
            if topic.get("id") == topic_id:
                topic["status"] = "posted"
                topic["times_used"] = (topic.get("times_used") or 0) + 1
                topic["last_used"] = date.today().isoformat()
                break
        _save_topics(topics_data)

    return draft


def reject(draft_id: str, reason: str | None = None) -> dict:
    """
    Mark a draft as rejected in queue.yaml.
    Does NOT update content-topics.yaml — topic stays 'unused' for a retry.
    Returns the updated draft dict.
    """
    queue_data = _load_queue()
    draft = _find_draft(queue_data, draft_id)
    if not draft:
        raise ValueError(f"Draft '{draft_id}' not found in queue.")

    draft["status"] = "rejected"
    draft["rejection_reason"] = reason or ""
    draft["rejected_at"] = date.today().isoformat()
    _save_queue(queue_data)
    return draft


def get_pending_drafts() -> list[dict]:
    """Return all pending drafts from queue.yaml."""
    data = _load_queue()
    return [d for d in data.get("drafts", []) if d.get("status") == "pending"]


def get_all_drafts() -> list[dict]:
    """Return all drafts from queue.yaml."""
    data = _load_queue()
    return data.get("drafts", [])


def queue_summary() -> dict:
    """Return counts by status."""
    drafts = get_all_drafts()
    summary = {"pending": 0, "approved": 0, "rejected": 0, "total": len(drafts)}
    for d in drafts:
        status = d.get("status", "pending")
        if status in summary:
            summary[status] += 1
    return summary
