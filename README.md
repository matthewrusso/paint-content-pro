# Paint Color Pro — Community Marketing Agent

A human-in-the-loop AI agent that drafts Reddit and Facebook community posts for [Paint Color Pro](https://paintcolorpro.com) — a color visualization widget for painting contractors.

**Workflow:** Agent selects a topic → drafts a post in the right community voice → queues it for review → you approve, edit, or reject → you post manually.

---

## How it works

1. **Topic database** (`content-topics.yaml`) — 88 pre-researched topics across 3 audiences (painting contractors, homeowners, adjacent trades), organized into 15 clusters and 3 funnel stages.

2. **Selector** picks the best available topic for a given community based on:
   - Your tenure in that community (controls funnel stage access)
   - Cluster rotation (avoids posting the same topic type twice in a week)
   - Topic availability (prefers unused; reuses posted topics after 30 days)

3. **Drafter** calls the Claude API (`claude-sonnet-4-6`) with a detailed system prompt that enforces:
   - Peer voice — sounds like a contractor, not a marketer
   - Platform tone — Reddit (informal/skeptical) vs Facebook (warm/supportive)
   - Funnel rules — pure-value posts have zero product mention; soft-mention never names the product

4. **Review UI** — a local web app where you approve, inline-edit, or reject each draft before posting manually.

5. **State tracking** — approved drafts update `content-topics.yaml` (status, times_used, last_used) to enforce rotation.

---

## Funnel stages

| Stage | Rule | When available |
|---|---|---|
| `pure-value` | Zero product mention. Genuinely helpful peer content. | Always |
| `soft-mention` | Reference "a color visualization tool" — never name the product. | After 2 weeks in community |
| `direct-promotion` | Name Paint Color Pro, link to site. | After 4 weeks, SaaS communities only |

---

## Setup

### Prerequisites
- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)

### Install

```bash
cd agent
pip install -r requirements.txt
```

### Configure API key

Create `agent/.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### Set community join dates

Edit `agent/config/communities.yaml`. For each community you've joined, set `join_date`:

```yaml
- platform: reddit
  name: "r/Paintingbusiness"
  audience: OWNER
  join_date: "2026-03-09"   # ← set this when you join
  rules: []
  priority: A
```

The agent uses this date to determine which funnel stage you've earned.

---

## Usage

### Draft a post

```bash
cd agent
python agent.py draft --community "r/Paintingbusiness"
```

Generate multiple drafts at once:
```bash
python agent.py draft --community "Painter Nation" --batch 3
```

### Review drafts

```bash
python agent.py review
# → http://localhost:5000
```

The review UI shows each pending draft with:
- **Approve** — queue it as-is, updates topic status in the database
- **Edit** — modify inline, then approve
- **Reject** — removes from queue with optional reason; topic stays available for retry

### Check queue status

```bash
python agent.py status
```

---

## File structure

```
paint-color-pro-marketing/
├── content-topics.yaml          # Topic database (88 topics, do not delete)
├── content-schema.md            # Schema documentation and agent selection rules
├── community-research.md        # Reddit + Facebook community research
├── facebook-groups-to-join.md   # Facebook groups with direct URLs
│
└── agent/
    ├── agent.py                 # CLI entry point
    ├── selector.py              # Topic selection logic
    ├── drafter.py               # Claude API draft generation
    ├── updater.py               # State management (queue + topic tracking)
    ├── queue.yaml               # Draft queue (generated at runtime)
    ├── requirements.txt
    │
    ├── config/
    │   └── communities.yaml     # Your community join dates + rules
    │
    └── review/
        ├── server.py            # Flask review web server
        └── templates/
            └── index.html       # Review UI
```

---

## OpenClaw integration

Since OpenClaw can execute shell commands, you can trigger the agent directly:

```bash
python /path/to/agent/agent.py draft --community "r/Paintingbusiness"
```

Register this as an OpenClaw skill to trigger drafts from within your chat interface. The queue and topic database are local YAML files, so any runtime on the same machine can read them.

---

## Content database

The topic database (`content-topics.yaml`) contains 88 seed topics:

| Audience | Count | Notes |
|---|---|---|
| OWNER (contractors) | 42 | Pain points: color consultations, lead capture, professionalism, pricing |
| HOMEOWNER (end users) | 33 | Color selection tips, room transformations, hiring advice |
| ADJACENT (trades/SaaS/designers) | 13 | For SaaS and trade communities |

**Distribution:** 73 pure-value (83%) · 12 soft-mention (14%) · 3 direct-promotion (3%)

Topics are organized into 15 clusters. The agent rotates clusters to avoid posting the same topic type twice in the same community within a week.

---

## Posting rules (enforced by selector)

- No automation — always post manually after approving a draft
- Pure-value only in strict no-promo communities (`r/paint`, `r/Housepainting101`)
- One topic cluster per community per week
- Reuse posted topics only after 30 days
- Match format to context (reply-prompt/tip for threads; question/story/guide for new posts)
