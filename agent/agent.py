#!/usr/bin/env python3
"""
agent.py — Paint Color Pro content drafting agent CLI.

Commands:
  draft --community NAME [--batch N]   Draft 1 (or N) posts for a community
  review                               Start the local review web UI
  status                               Print queue summary

Usage:
  python agent.py draft --community "r/Paintingbusiness"
  python agent.py draft --community "Painter Nation" --batch 3
  python agent.py review
  python agent.py status
"""

import argparse
import sys
import uuid
from datetime import date
from pathlib import Path

# Ensure the agent/ directory is on the path when called from anywhere
sys.path.insert(0, str(Path(__file__).parent))

import updater
from drafter import draft_post
from selector import select_topic


def cmd_draft(community: str, batch: int) -> None:
    """Generate one or more drafts for a community and add to the queue."""
    print(f"\nDrafting {batch} post(s) for: {community}\n")

    for i in range(batch):
        if batch > 1:
            print(f"  [{i + 1}/{batch}] Selecting topic...", end=" ", flush=True)
        else:
            print("  Selecting topic...", end=" ", flush=True)

        try:
            topic = select_topic(community)
        except ValueError as e:
            print(f"\nError: {e}")
            sys.exit(1)

        print(f"Found: [{topic.get('funnel')}] {topic.get('title')[:60]}...")
        print("  Calling Claude API...", end=" ", flush=True)

        draft_text = draft_post(topic)
        print("Done.")

        community_config = topic.get("_community_config", {})
        draft_id = f"draft-{uuid.uuid4().hex[:8]}"

        draft_entry = {
            "id": draft_id,
            "generated_at": date.today().isoformat(),
            "topic_id": topic.get("id"),
            "topic_title": topic.get("title"),
            "community": community,
            "platform": community_config.get("platform", "unknown"),
            "audience": topic.get("audience"),
            "cluster": topic.get("cluster"),
            "funnel": topic.get("_funnel_to_use", topic.get("funnel")),
            "format": topic.get("format"),
            "draft": draft_text,
            "status": "pending",
            "rejection_reason": None,
            "approved_at": None,
            "rejected_at": None,
            "edited": False,
        }

        updater.append_draft(draft_entry)
        print(f"  Queued as: {draft_id}\n")

    summary = updater.queue_summary()
    print(f"Queue: {summary['pending']} pending / {summary['approved']} approved / {summary['rejected']} rejected")
    print("\nRun 'python agent.py review' to open the review UI.")


def cmd_review(port: int = 5000) -> None:
    """Start the Flask review server."""
    # Import here so Flask isn't required for draft/status commands
    review_path = Path(__file__).parent / "review"
    sys.path.insert(0, str(review_path))
    from server import app  # noqa: PLC0415

    print(f"\nStarting review UI at http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    app.run(host="127.0.0.1", port=port, debug=False)


def cmd_status() -> None:
    """Print a summary of the draft queue."""
    summary = updater.queue_summary()
    print(f"\nDraft Queue Status")
    print(f"  Total:    {summary['total']}")
    print(f"  Pending:  {summary['pending']}")
    print(f"  Approved: {summary['approved']}")
    print(f"  Rejected: {summary['rejected']}")

    if summary["pending"] > 0:
        print(f"\nRun 'python agent.py review' to review pending drafts.")

    drafts = updater.get_all_drafts()
    if drafts:
        print(f"\nRecent drafts:")
        for d in drafts[-5:]:
            status_symbol = {"pending": "⏳", "approved": "✓", "rejected": "✗"}.get(d.get("status", ""), "?")
            print(f"  {status_symbol} [{d.get('status'):8}] {d.get('community'):30} {d.get('id')}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Paint Color Pro content drafting agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # draft command
    draft_parser = subparsers.add_parser("draft", help="Generate draft posts for a community")
    draft_parser.add_argument(
        "--community", "-c",
        required=True,
        help='Community name, e.g. "r/Paintingbusiness" or "Painter Nation"',
    )
    draft_parser.add_argument(
        "--batch", "-b",
        type=int,
        default=1,
        help="Number of drafts to generate (default: 1)",
    )

    # review command
    review_parser = subparsers.add_parser("review", help="Start the local review web UI")
    review_parser.add_argument(
        "--port", "-p",
        type=int,
        default=5000,
        help="Port for the review server (default: 5000)",
    )

    # status command
    subparsers.add_parser("status", help="Print queue summary")

    args = parser.parse_args()

    if args.command == "draft":
        cmd_draft(args.community, args.batch)
    elif args.command == "review":
        cmd_review(args.port)
    elif args.command == "status":
        cmd_status()


if __name__ == "__main__":
    main()
