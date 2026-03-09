"""
selector.py — Topic selection logic for the Paint Color Pro content agent.

Given a target community name, selects the best unused topic from content-topics.yaml
respecting funnel stage rules, cluster rotation, and community constraints.
"""

import random
from datetime import date, datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).parent.parent  # paint-color-pro-marketing/
TOPICS_FILE = ROOT / "content-topics.yaml"
COMMUNITIES_FILE = Path(__file__).parent / "config" / "communities.yaml"
QUEUE_FILE = Path(__file__).parent / "queue.yaml"


def load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_community_config(community_name: str) -> dict:
    """Find the community config entry by name (case-insensitive)."""
    data = load_yaml(COMMUNITIES_FILE)
    name_lower = community_name.lower().strip()
    for c in data.get("communities", []):
        if c["name"].lower().strip() == name_lower:
            return c
    raise ValueError(
        f"Community '{community_name}' not found in config/communities.yaml.\n"
        f"Add it first and set a join_date."
    )


def compute_tenure_weeks(join_date_str: str | None) -> float:
    """Return how many weeks since join_date. None or missing → 0."""
    if not join_date_str:
        return 0.0
    if isinstance(join_date_str, date):
        join = join_date_str
    else:
        join = datetime.strptime(str(join_date_str), "%Y-%m-%d").date()
    delta = date.today() - join
    return delta.days / 7.0


def allowed_funnel_stages(weeks: float, rules: list) -> list[str]:
    """
    Return the list of funnel stages allowed based on tenure and community rules.
    If rules contains 'no-promo', always restrict to pure-value only.
    """
    if "no-promo" in rules:
        return ["pure-value"]
    if weeks < 2:
        return ["pure-value"]
    if weeks < 4:
        return ["pure-value", "soft-mention"]
    return ["pure-value", "soft-mention", "direct-promotion"]


def weighted_funnel_pick(weeks: float, allowed: list[str]) -> str:
    """
    Pick a funnel stage using the defined weighting strategy:
    - Weeks 2-4: 80% pure-value, 20% soft-mention
    - Weeks 4+:  75% pure-value, 20% soft-mention, 5% direct-promotion
    """
    if len(allowed) == 1:
        return allowed[0]
    if weeks < 4:
        return random.choices(["pure-value", "soft-mention"], weights=[80, 20])[0]
    return random.choices(
        ["pure-value", "soft-mention", "direct-promotion"],
        weights=[75, 20, 5]
    )[0]


def get_recent_clusters_for_community(community_name: str, days: int = 7) -> set[str]:
    """
    Return the set of topic clusters that have been drafted or posted
    for this community in the last `days` days. Used to enforce cluster rotation.
    """
    try:
        queue_data = load_yaml(QUEUE_FILE)
    except FileNotFoundError:
        return set()

    recent_clusters: set[str] = set()
    cutoff = date.today().toordinal() - days
    topics_data = load_yaml(TOPICS_FILE)
    topic_cluster_map = {t["id"]: t["cluster"] for t in topics_data.get("topics", [])}

    for draft in queue_data.get("drafts", []):
        if draft.get("community", "").lower() != community_name.lower():
            continue
        if draft.get("status") in ("pending", "approved", "rejected"):
            gen_date_str = draft.get("generated_at")
            if not gen_date_str:
                continue
            gen_date = datetime.strptime(str(gen_date_str), "%Y-%m-%d").date()
            if gen_date.toordinal() >= cutoff:
                cluster = topic_cluster_map.get(draft.get("topic_id", ""))
                if cluster:
                    recent_clusters.add(cluster)

    return recent_clusters


def is_topic_available(topic: dict) -> bool:
    """
    A topic is available if:
    - status is 'unused', OR
    - status is 'posted' AND last_used was more than 30 days ago
    """
    status = topic.get("status", "unused")
    if status == "unused":
        return True
    if status == "posted":
        last_used = topic.get("last_used")
        if not last_used:
            return True
        if isinstance(last_used, date):
            last = last_used
        else:
            last = datetime.strptime(str(last_used), "%Y-%m-%d").date()
        return (date.today() - last).days > 30
    return False


def select_topic(community_name: str) -> dict:
    """
    Main selection function. Returns a topic dict with an extra `_funnel_to_use` key
    indicating the funnel stage to draft for (may differ from topic.funnel if weighted).

    Raises ValueError if no suitable topic is found.
    """
    community = get_community_config(community_name)
    weeks = compute_tenure_weeks(community.get("join_date"))
    rules = community.get("rules", [])
    audience = community.get("audience")

    allowed = allowed_funnel_stages(weeks, rules)
    target_funnel = weighted_funnel_pick(weeks, allowed)
    recent_clusters = get_recent_clusters_for_community(community_name)

    topics_data = load_yaml(TOPICS_FILE)
    all_topics = topics_data.get("topics", [])

    # First pass: strict match — audience + target funnel + available + not recently clustered
    candidates = [
        t for t in all_topics
        if t.get("audience") == audience
        and t.get("funnel") == target_funnel
        and is_topic_available(t)
        and t.get("cluster") not in recent_clusters
    ]

    # Second pass: relax cluster rotation if nothing found
    if not candidates:
        candidates = [
            t for t in all_topics
            if t.get("audience") == audience
            and t.get("funnel") == target_funnel
            and is_topic_available(t)
        ]

    # Third pass: relax funnel to anything in allowed list
    if not candidates:
        candidates = [
            t for t in all_topics
            if t.get("audience") == audience
            and t.get("funnel") in allowed
            and is_topic_available(t)
        ]

    if not candidates:
        raise ValueError(
            f"No available topics found for community '{community_name}' "
            f"(audience={audience}, allowed_funnels={allowed}).\n"
            f"All matching topics may be exhausted or recently used."
        )

    chosen = random.choice(candidates)
    chosen["_funnel_to_use"] = target_funnel
    chosen["_community_config"] = community
    chosen["_tenure_weeks"] = weeks
    return chosen
