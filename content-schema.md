# Content Topic Database — Schema & Agent Instructions

This document defines the schema for `content-topics.yaml` and provides rules for how a future drafting agent should select and use topics.

---

## Schema

Each entry in the `topics` list has these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | yes | Unique ID. Pattern: `{audience_short}-{cluster_short}-{number}` (e.g., `owner-ccp-001`) |
| `title` | string | yes | Topic headline or conversation starter. Used as the starting point for drafting. |
| `audience` | enum | yes | Target audience segment. |
| `cluster` | enum | yes | Topic cluster slug. Groups related topics. |
| `format` | enum | yes | Content format/shape. |
| `funnel` | enum | yes | Promotional intensity level. |
| `communities` | list | yes | Where this topic fits. Each entry has `platform`, `name`, and `priority`. |
| `pain_point` | enum | yes | Which product pain point this maps to. |
| `talking_points` | list | yes | Key ideas for the agent to weave into the content. Not a script. |
| `cta_if_any` | string/null | yes | `null` for pure-value. A soft CTA instruction for soft-mention/direct-promotion. |
| `status` | enum | yes | Lifecycle state of this topic. |
| `times_used` | integer | yes | How many times this topic has been posted. |
| `last_used` | date/null | yes | ISO date of last posting, or `null` if never used. |
| `notes` | string/null | no | Freeform notes from Matt after reviewing drafts or results. |

---

## Enum Values

### `audience`
| Value | Description |
|---|---|
| `OWNER` | Painting company owners/operators. The buyer. |
| `HOMEOWNER` | End users who choose paint colors. Demand generation. |
| `ADJACENT` | Related trades, SaaS founders, designers, marketers. |

### `cluster`

**OWNER clusters:**
| Slug | Description |
|---|---|
| `color-consultation-pain` | Time wasted in color meetings, indecisive clients |
| `lead-capture` | Website lead gen, converting visitors to estimates |
| `business-professionalism` | Looking modern, tech-forward, competitive edge |
| `pricing-estimating` | Estimating strategies, scope creep, change orders |
| `hiring-scaling` | Growing a crew, delegation, systems |
| `marketing-general` | SEO, Google Business, social media for painters |

**HOMEOWNER clusters:**
| Slug | Description |
|---|---|
| `color-selection-tips` | How to choose colors, undertones, lighting |
| `room-transformations` | Before/after, dramatic paint makeovers |
| `trending-colors` | Color of the year, palettes, design trends |
| `hiring-a-painter` | Finding/vetting/working with contractors |
| `diy-vs-pro` | When to DIY vs hire, common DIY mistakes |
| `exterior-curb-appeal` | Exterior paint, curb appeal, home value |

**ADJACENT clusters:**
| Slug | Description |
|---|---|
| `tech-for-trades` | SaaS tools, technology adoption in home services |
| `saas-building` | Building PaintColorPro, indie SaaS journey |
| `design-partnership` | Interior designers + painters working together |

### `format`
| Value | When to use |
|---|---|
| `question` | Ask the community a genuine question to spark discussion |
| `tip` | Share a specific, actionable piece of advice |
| `story` | Tell a narrative (personal experience, case study) |
| `case-study` | Data-driven before/after with specific numbers |
| `reply-prompt` | Template for replying to existing threads (not a new post) |
| `guide` | Multi-step how-to or framework |
| `poll` | Community poll or survey question |

### `funnel`
| Value | Rule |
|---|---|
| `pure-value` | Zero mention of PaintColorPro or any tool. Genuinely helpful content only. No links. |
| `soft-mention` | Reference "a color visualization tool" or "we started using a widget" without naming the product. Only when it fits naturally. Never forced. |
| `direct-promotion` | Name PaintColorPro, link to site. ONLY use in SaaS/indie communities (r/SaaS, r/microsaas, r/indiehackers) or when someone explicitly asks for tool recommendations. |

### `pain_point`
| Value | Product connection |
|---|---|
| `time-waste` | Contractors spend 60+ min per estimate on color discussions |
| `no-lead-capture` | No automated lead capture from contractor websites |
| `homeowner-indecision` | Homeowners are indecisive and delay projects |
| `unprofessional-image` | Contractors look outdated without modern tools |
| `general` | Broader business/industry topic, not directly tied to product |

### `status`
| Value | Meaning |
|---|---|
| `unused` | Not yet drafted or posted |
| `drafted` | Agent has written a draft, pending Matt's review |
| `posted` | Published to at least one community |
| `retired` | No longer relevant or overused |

---

## Agent Selection Rules

When selecting a topic to draft content for a specific community:

1. **Filter by audience.** Match the topic's `audience` to the community's audience segment.
2. **Prefer `unused` status.** Only reuse `posted` topics if `last_used` is 30+ days ago AND the topic is evergreen.
3. **Rotate clusters.** Do not pick from the same cluster more than once per week per community.
4. **Respect funnel stage.** Check how long Matt has been active in the community:
   - First 2 weeks: ONLY `pure-value` topics
   - Weeks 2-4: Mix of `pure-value` (80%) and `soft-mention` (20%)
   - After week 4: Can include occasional `direct-promotion` in appropriate communities
5. **Match format to context.** If replying to an existing thread, prefer `reply-prompt` or `tip` format. For new posts, use `question`, `story`, `guide`, or `poll`.
6. **Check community rules.** Some subreddits (r/paint, r/Housepainting101) have strict no-promo rules. Never use `direct-promotion` or `soft-mention` in these communities.

## Agent Drafting Rules

When drafting content from a selected topic:

1. **Use talking points as ingredients, not a script.** Weave them naturally into conversational language.
2. **Match community tone.** Reddit is informal, skeptical of marketing. Facebook groups are warmer and more supportive.
3. **Keep it concise.** Reddit: 2-4 short paragraphs max. Facebook: 3-5 sentences for comments, longer for original posts.
4. **No corporate voice.** Write like a fellow painter/homeowner/builder, not a marketer.
5. **Ask genuine questions.** End posts with a question to invite replies.
6. **Never be the first to mention your own product.** Even in `soft-mention` posts, frame it as something you discovered, not something you built (unless in SaaS communities).

## Database Growth

The database grows through three channels:

1. **Manual additions by Matt** — After engaging in communities, add new entries for recurring questions and pain points.
2. **Agent-suggested topics** — The agent can append suggestions to a `# Suggestions` section at the bottom of the YAML. Matt reviews and promotes them.
3. **Periodic refresh** — Every 4-6 weeks, review which clusters are low on `unused` topics and seed 10-15 new entries.
