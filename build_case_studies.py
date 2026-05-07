#!/usr/bin/env python3
"""Port cynthiaconcierge case studies into the ARK Partners brand.

Reads each /home/cynthia/firebase-root/public/case-studies/<slug>/index.html,
extracts the structured fields, and writes ARK-branded HTML to
/home/cynthia/ARK Workspace/site/case-studies/<slug>/index.html plus an index.

Run: python3 build-case-studies.py
"""
from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from bs4 import BeautifulSoup

SRC = Path("/home/cynthia/firebase-root/public/case-studies")
OUT = Path("/home/cynthia/ARK Workspace/site/case-studies")

# Tagline overrides that match what the homepage carousel and index card show
# (short result/headline pulled from the cynthia index page). Keyed by slug.
RESULT_OVERRIDES = {
    "conscious-counsel":   "Full AI marketing & sales engine deployed.",
    "affextionate-cuizine": "$48K+ active pipeline · &lt; 60s response time.",
    "legal-intake":        "$17.95 cost per lead · 500+ businesses served.",
    "sereia-official":     "Unprofitable → profitable in 48 hours.",
    "executive-recruiting": "30+ executive candidates in 24 hours.",
    "ai-meeting-coach":    "40% improvement in close rate.",
    "philly-basketball":   "200+ kids enrolled · 562 messages automated.",
    "voice-erp":           "Full marketing stack deployed.",
    "sides-bbq":           "First Google rankings after 40 years.",
    "beverly-hills-wellness": "HIPAA compliant · 10+ hrs/week saved.",
    "allied-exteriors":    "5+ enterprise prospects with personalized outreach.",
}

NAME_OVERRIDES = {
    # Source pages omit .client-name; fall back to the labels used on the
    # cynthia homepage card list.
    "executive-recruiting": "PE Recruiting Firm",
    "ai-meeting-coach": "Cynthia Meet",
}

TAGS = {
    "conscious-counsel":   ["Meta Ads", "AI SDR", "Video Content"],
    "affextionate-cuizine": ["Google SEO", "Pipeline", "AI Proposals"],
    "legal-intake":        ["Website", "Meta Ads", "AI SDR"],
    "sereia-official":     ["Ad Audit", "Targeting", "ROAS"],
    "executive-recruiting": ["AI Sourcing", "Recruiting", "Pipeline"],
    "ai-meeting-coach":    ["Meet", "Coaching", "CRM Sync"],
    "philly-basketball":   ["AI SDR", "Enrollment", "Follow-up"],
    "voice-erp":           ["Paid Ads", "Landing Pages", "Analytics"],
    "sides-bbq":           ["Local SEO", "Lead Auto", "GMB"],
    "beverly-hills-wellness": ["HIPAA", "Intake", "Scheduling"],
    "allied-exteriors":    ["B2B Outreach", "Personalization", "Construction"],
}


# ───────────────────────────────────────── shared styles + nav ──
SHARED_HEAD = """\
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <meta name="description" content="{description}" />
  <link rel="icon" type="image/png" href="/assets/ark-icon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght,SOFT@9..144,300..600,30..100&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" />
  <style>
    :root {{
      --ink:#141414;--ink-soft:#2a2a2a;--paper:#FAF8F4;--paper-warm:#F4EFE6;
      --teal-deep:#0d4f4a;--teal-light:#3aa89e;--gold:#b8893a;--navy:#2a3f5f;
      --rule:rgba(20,20,20,0.14);--rule-strong:rgba(20,20,20,0.28);--muted:#6b6b6b;--soft:#3d3d3d;
    }}
    *{{box-sizing:border-box;margin:0;padding:0}}
    html{{scroll-behavior:smooth}}
    body{{background:var(--paper);color:var(--ink);font-family:"JetBrains Mono",ui-monospace,monospace;font-size:15px;line-height:1.6;-webkit-font-smoothing:antialiased;}}
    a{{color:inherit;text-decoration:none}}
    img{{max-width:100%;display:block}}
    .container{{max-width:1180px;margin:0 auto;padding:0 40px}}
    .narrow{{max-width:780px;margin:0 auto;padding:0 24px}}
    @media(max-width:720px){{.container{{padding:0 22px}}}}

    /* Nav */
    .nav{{position:sticky;top:0;z-index:50;background:rgba(250,248,244,0.86);backdrop-filter:saturate(160%) blur(10px);-webkit-backdrop-filter:saturate(160%) blur(10px);border-bottom:1px solid var(--rule)}}
    .nav-inner{{max-width:1180px;margin:0 auto;padding:16px 40px;display:flex;align-items:center;justify-content:space-between}}
    .nav .mark{{font-family:"JetBrains Mono",monospace;font-weight:700;font-size:18px;letter-spacing:0.04em;display:flex;align-items:baseline;gap:12px}}
    .nav .mark .br{{color:var(--teal-deep)}}
    .nav .mark .partners{{font-weight:500;font-size:10px;letter-spacing:0.28em;text-transform:uppercase;color:var(--ink)}}
    .nav-links{{display:flex;gap:28px;align-items:center}}
    .nav-links a{{font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:var(--soft);font-weight:500}}
    .nav-links a:hover{{color:var(--teal-deep)}}
    .nav-cta{{padding:9px 16px;border:1px solid var(--ink);font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:500;color:var(--ink);background:transparent;transition:all .2s ease}}
    .nav-cta:hover{{background:var(--ink);color:var(--paper)}}
    @media(max-width:820px){{.nav-inner{{padding:14px 22px}}.nav-links a:not(.nav-cta){{display:none}}}}

    /* Type */
    .eyebrow{{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:0.24em;text-transform:uppercase;color:var(--teal-deep);font-weight:500;display:inline-flex;align-items:center;gap:10px}}
    .eyebrow .br{{color:var(--teal-deep)}}
    .h-display{{font-family:"Fraunces",serif;font-weight:300;font-size:clamp(36px,5.4vw,68px);line-height:1.04;letter-spacing:-0.025em;color:var(--ink)}}
    .lede{{font-family:"Fraunces",serif;font-size:clamp(18px,1.5vw,21px);line-height:1.55;color:var(--soft);max-width:660px}}

    /* Footer */
    footer{{border-top:1px solid var(--ink);padding:36px 40px;margin-top:48px;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:0.22em;text-transform:uppercase;color:var(--muted)}}
    footer .mark{{display:flex;gap:10px;align-items:baseline;color:var(--ink)}}
    footer .mark .br{{color:var(--teal-deep);font-weight:700}}

    /* Buttons */
    .btn{{display:inline-flex;align-items:center;gap:10px;padding:14px 22px;font-family:"JetBrains Mono",monospace;font-size:12px;letter-spacing:0.18em;text-transform:uppercase;font-weight:500;transition:all .2s ease;cursor:pointer;border:1px solid var(--ink)}}
    .btn-primary{{background:var(--ink);color:var(--paper)}}
    .btn-primary:hover{{background:var(--teal-deep);border-color:var(--teal-deep)}}
    .btn-ghost{{background:transparent;color:var(--ink)}}
    .btn-ghost:hover{{background:var(--ink);color:var(--paper)}}
    .arrow{{font-family:"JetBrains Mono",monospace}}
"""

NAV_HTML = """\
  <nav class="nav">
    <div class="nav-inner">
      <a class="mark" href="/" aria-label="ARK Partners home">
        <span><span class="br">[</span>ARK<span class="br">]</span></span>
        <span class="partners">Partners</span>
      </a>
      <div class="nav-links">
        <a href="/#brief">Morning Brief</a>
        <a href="/#cynthia">Cynthia</a>
        <a href="/#stories">Case studies</a>
        <a class="nav-cta" href="/#book">Book a call</a>
      </div>
    </div>
  </nav>
"""

FOOTER_HTML = """\
  <footer>
    <div class="mark">
      <span style="font-weight:700;font-size:14px;letter-spacing:0.04em;"><span class="br">[</span>ARK<span class="br">]</span></span>
      <span>Partners · est. 2026</span>
    </div>
    <div>arkpartners.ai · hello@arkpartners.ai</div>
  </footer>
"""


# ───────────────────────────────────────── extraction helpers ──
def first_text(node, default=""):
    return node.get_text(strip=True) if node else default


def extract(slug: str, src_html: str) -> dict:
    soup = BeautifulSoup(src_html, "lxml")

    initials = first_text(soup.select_one(".cs-badge-dot"))
    industry = first_text(soup.select_one(".cs-badge-text"))

    client_name_node = soup.select_one(".cs-hero .client-name")
    client_link = client_name_node.find("a") if client_name_node else None
    client_name = first_text(client_link) if client_link else first_text(client_name_node)
    client_url  = client_link["href"] if client_link and client_link.has_attr("href") else ""
    if not client_name and slug in NAME_OVERRIDES:
        client_name = NAME_OVERRIDES[slug]

    title    = first_text(soup.select_one(".cs-hero h1"))
    subtitle = first_text(soup.select_one(".cs-hero .subtitle"))

    metrics = []
    for m in soup.select(".metrics .metric"):
        v = first_text(m.select_one(".metric-value"))
        l = first_text(m.select_one(".metric-label"))
        if v:
            metrics.append({"value": v, "label": l})

    sections = soup.select(".cs-section")
    challenge_text = solution_text = ""
    solution_cards = []
    outcomes = []
    for sec in sections:
        label = first_text(sec.select_one(".cs-section-label")).lower()
        # The body text is the first <p> directly inside the section
        first_p = sec.find("p", recursive=False) or sec.find("p")
        body = first_text(first_p)
        if "challenge" in label:
            challenge_text = body
        elif "built" in label or "solution" in label:
            solution_text = body
            for card in sec.select(".solution-card"):
                solution_cards.append({
                    "h": first_text(card.find("h4")),
                    "p": first_text(card.find("p")),
                })
        elif "result" in label:
            for li in sec.select(".outcomes li"):
                # Strip the leading checkmark span text if present
                check = li.select_one(".outcome-check")
                if check:
                    check.extract()
                outcomes.append(li.get_text(" ", strip=True))

    blockquote = soup.select_one(".cs-quote blockquote")
    attribution = soup.select_one(".cs-quote .attribution")
    quote = first_text(blockquote)
    quote_attr = first_text(attribution).lstrip("—").strip()

    return {
        "slug": slug,
        "initials": initials,
        "industry": industry,
        "client_name": client_name,
        "client_url": client_url,
        "title": title,
        "subtitle": subtitle,
        "metrics": metrics,
        "challenge": challenge_text,
        "solution_intro": solution_text,
        "solution_cards": solution_cards,
        "outcomes": outcomes,
        "quote": quote,
        "quote_attr": quote_attr,
        "result": RESULT_OVERRIDES.get(slug, ""),
        "tags": TAGS.get(slug, []),
    }


# ───────────────────────────────────────── case-study renderer ──
CASE_TEMPLATE = """\
{head}
    /* Case study page styles */
    .breadcrumb{{padding:24px 0 0;font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted)}}
    .breadcrumb a{{color:var(--soft)}}
    .breadcrumb a:hover{{color:var(--teal-deep)}}
    .breadcrumb .sep{{margin:0 10px;opacity:.5}}

    .cs-hero{{padding:48px 0 24px}}
    .cs-badge{{display:inline-flex;align-items:center;gap:10px;padding:6px 14px 6px 6px;background:var(--paper-warm);border:1px solid var(--rule-strong);margin-bottom:28px}}
    .cs-mark{{flex-shrink:0;width:32px;height:32px;display:flex;align-items:center;justify-content:center;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:12px;letter-spacing:0.04em;color:var(--ink);background:var(--paper);border:1px solid var(--rule-strong)}}
    .cs-mark .br{{color:var(--teal-deep)}}
    .cs-badge-text{{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:var(--soft)}}

    .client-name{{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:var(--teal-deep);margin-bottom:12px}}
    .client-name a{{border-bottom:1px solid rgba(13,79,74,0.25);transition:border-color .2s ease}}
    .client-name a:hover{{border-bottom-color:var(--teal-deep)}}

    .cs-hero h1{{font-family:"Fraunces",serif;font-weight:400;font-size:clamp(32px,4.2vw,52px);line-height:1.08;letter-spacing:-0.025em;color:var(--ink);margin-bottom:18px}}
    .cs-hero .subtitle{{font-family:"Fraunces",serif;font-size:clamp(18px,1.5vw,21px);line-height:1.55;color:var(--soft)}}

    .metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:0;padding:36px 0;border-top:1px solid var(--ink);border-bottom:1px solid var(--ink);margin:48px 0 56px}}
    @media(max-width:720px){{.metrics{{grid-template-columns:1fr}}}}
    .metric{{padding:20px 22px;border-right:1px solid var(--rule)}}
    .metric:last-child{{border-right:0}}
    @media(max-width:720px){{.metric{{border-right:0;border-bottom:1px solid var(--rule)}}.metric:last-child{{border-bottom:0}}}}
    .metric-value{{font-family:"Fraunces",serif;font-weight:400;font-size:42px;letter-spacing:-0.025em;line-height:1;color:var(--teal-deep);margin-bottom:6px}}
    .metric-label{{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.05em;color:var(--soft);line-height:1.5}}

    .cs-section{{margin-bottom:56px}}
    .cs-section-label{{font-family:"JetBrains Mono",monospace;font-size:10px;font-weight:500;text-transform:uppercase;letter-spacing:0.24em;color:var(--teal-deep);margin-bottom:14px;display:inline-flex;align-items:center;gap:10px}}
    .cs-section-label .br{{color:var(--teal-deep)}}
    .cs-section h2{{font-family:"Fraunces",serif;font-weight:400;font-size:clamp(26px,3vw,34px);letter-spacing:-0.02em;color:var(--ink);margin-bottom:16px;line-height:1.15}}
    .cs-section p{{font-size:16px;line-height:1.75;color:var(--soft);margin-bottom:14px;font-family:"Fraunces",serif}}

    .solution-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:24px 0}}
    @media(max-width:720px){{.solution-grid{{grid-template-columns:1fr}}}}
    .solution-card{{background:var(--paper-warm);border:1px solid var(--rule-strong);padding:22px}}
    .solution-card h4{{font-family:"Fraunces",serif;font-weight:500;font-size:18px;letter-spacing:-0.01em;color:var(--ink);margin-bottom:6px}}
    .solution-card p{{font-family:"JetBrains Mono",monospace;font-size:12px;line-height:1.65;color:var(--soft);margin:0}}

    .outcomes{{list-style:none;padding:0;margin:18px 0;border-top:1px solid var(--rule)}}
    .outcomes li{{padding:14px 0 14px 24px;border-bottom:1px solid var(--rule);font-family:"JetBrains Mono",monospace;font-size:13px;line-height:1.65;color:var(--soft);position:relative}}
    .outcomes li::before{{content:'[+]';position:absolute;left:0;top:14px;font-weight:700;color:var(--teal-deep);font-size:12px;letter-spacing:0.05em}}

    .cs-quote{{background:var(--paper-warm);border-left:3px solid var(--teal-deep);padding:36px 40px;margin:48px 0}}
    .cs-quote blockquote{{font-family:"Fraunces",serif;font-style:italic;font-size:22px;line-height:1.5;letter-spacing:-0.015em;color:var(--ink);margin-bottom:14px}}
    .cs-quote .attribution{{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted)}}

    .cs-bottom-cta{{text-align:center;padding:64px 0;border-top:1px solid var(--ink);margin-top:48px}}
    .cs-bottom-cta h3{{font-family:"Fraunces",serif;font-weight:300;font-size:clamp(28px,3.6vw,42px);letter-spacing:-0.025em;color:var(--ink);margin-bottom:14px;line-height:1.1}}
    .cs-bottom-cta>p{{font-family:"Fraunces",serif;font-size:18px;color:var(--soft);margin:0 auto 28px;max-width:540px}}

    .next-study{{padding:24px 0 12px;margin-top:32px}}
    .next-study a{{display:flex;align-items:center;justify-content:space-between;padding:22px 28px;background:var(--paper);border:1px solid var(--ink);transition:background .2s ease}}
    .next-study a:hover{{background:var(--paper-warm)}}
    .next-study .label{{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:0.22em;text-transform:uppercase;color:var(--muted)}}
    .next-study .name{{font-family:"Fraunces",serif;font-weight:400;font-size:20px;letter-spacing:-0.01em;color:var(--ink);margin-top:4px}}
    .next-study .arrow{{font-family:"JetBrains Mono",monospace;font-size:18px;color:var(--teal-deep)}}
  </style>
</head>
<body>

{nav}

  <div class="container narrow">
    <div class="breadcrumb">
      <a href="/">Home</a><span class="sep">/</span><a href="/case-studies/">Case studies</a><span class="sep">/</span><span>{client_name}</span>
    </div>

    <section class="cs-hero">
      <div class="cs-badge">
        <div class="cs-mark"><span class="br">[</span>{initials}<span class="br">]</span></div>
        <span class="cs-badge-text">{industry}</span>
      </div>
      {client_html}
      <h1>{title}</h1>
      <p class="subtitle">{subtitle}</p>
    </section>

    {metrics_html}

    {challenge_html}

    {solution_html}

    {outcomes_html}

    {quote_html}

    <div class="cs-bottom-cta">
      <h3>Want results like this?</h3>
      <p>Tell us about your business. We'll design a custom AI solution and show you exactly what it can do.</p>
      <a href="/#book" class="btn btn-primary">Book a free discovery call <span class="arrow">→</span></a>
    </div>

    {next_study_html}
  </div>

{footer}

</body>
</html>
"""

INDEX_PAGE_TEMPLATE = """\
{head}
    .stories-page{{padding:80px 0 24px}}
    .stories-page-head{{text-align:center;max-width:760px;margin:0 auto 56px}}
    .stories-page-head .eyebrow{{margin-bottom:18px}}
    .stories-page-head h1{{font-family:"Fraunces",serif;font-weight:300;font-size:clamp(40px,6vw,72px);line-height:1.02;letter-spacing:-0.03em;color:var(--ink);margin-bottom:18px}}
    .stories-page-head .lede{{margin:0 auto}}

    .stories-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;padding:0 0 80px}}
    @media(max-width:980px){{.stories-grid{{grid-template-columns:1fr 1fr}}}}
    @media(max-width:680px){{.stories-grid{{grid-template-columns:1fr}}}}

    .ix-card{{display:flex;flex-direction:column;background:var(--paper);border:1px solid var(--ink);padding:28px 26px 26px;transition:transform .25s ease,box-shadow .25s ease;color:var(--ink)}}
    .ix-card:hover{{transform:translateY(-2px);box-shadow:0 18px 40px rgba(20,20,20,0.08)}}
    .ix-card-head{{display:flex;gap:14px;align-items:center;padding-bottom:18px;margin-bottom:16px;border-bottom:1px solid var(--rule)}}
    .ix-mark{{flex-shrink:0;width:44px;height:44px;display:flex;align-items:center;justify-content:center;font-family:"JetBrains Mono",monospace;font-weight:700;font-size:13px;letter-spacing:0.04em;color:var(--ink);background:var(--paper-warm);border:1px solid var(--rule-strong)}}
    .ix-mark .br{{color:var(--teal-deep)}}
    .ix-name{{font-family:"Fraunces",serif;font-weight:400;font-size:19px;letter-spacing:-0.01em;line-height:1.1}}
    .ix-industry{{font-family:"JetBrains Mono",monospace;font-size:9.5px;letter-spacing:0.18em;text-transform:uppercase;color:var(--muted);margin-top:4px}}
    .ix-desc{{font-family:"Fraunces",serif;font-size:15.5px;line-height:1.55;color:var(--soft);margin-bottom:16px}}
    .ix-result{{font-family:"Fraunces",serif;font-size:15px;color:var(--teal-deep);font-weight:500;letter-spacing:-0.01em;padding:14px 0 4px;border-top:1px solid var(--rule);margin-top:auto}}
    .ix-arrow{{margin-top:14px;font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:0.18em;text-transform:uppercase;font-weight:500;color:var(--teal-deep);align-self:flex-start;border-bottom:1px solid transparent;padding-bottom:4px;transition:border-color .2s ease}}
    .ix-card:hover .ix-arrow{{border-bottom-color:var(--teal-deep)}}
  </style>
</head>
<body>

{nav}

  <main class="stories-page">
    <div class="container">
      <div class="stories-page-head">
        <span class="eyebrow"><span class="br">[</span>Case studies<span class="br">]</span></span>
        <h1>Our success stories.</h1>
        <p class="lede">Real businesses share how we built custom AI solutions that transformed their operations and boosted results.</p>
      </div>

      <div class="stories-grid">
        {cards_html}
      </div>
    </div>
  </main>

  <section style="padding:80px 0;text-align:center;border-top:1px solid var(--rule);background:var(--paper-warm);">
    <div class="container">
      <h2 class="h-display" style="max-width:700px;margin:0 auto 22px;font-size:clamp(32px,4.4vw,54px);">Want a story like this?</h2>
      <p class="lede" style="margin:0 auto 36px;">30 minutes, zero pitch decks. We'll show you exactly where Cynthia hits hardest in your business.</p>
      <a class="btn btn-primary" href="/#book">Book a free discovery call <span class="arrow">→</span></a>
    </div>
  </section>

{footer}

</body>
</html>
"""


# ───────────────────────────────────────── render helpers ──
def render_metrics(metrics):
    if not metrics:
        return ""
    items = "".join(
        f'<div class="metric"><div class="metric-value">{html.escape(m["value"])}</div>'
        f'<div class="metric-label">{html.escape(m["label"])}</div></div>'
        for m in metrics[:3]
    )
    return f'<div class="metrics">{items}</div>'


def render_challenge(text):
    if not text:
        return ""
    return (
        '<section class="cs-section">'
        '<span class="cs-section-label"><span class="br">[</span>The challenge<span class="br">]</span></span>'
        '<h2>What they were dealing with</h2>'
        f'<p>{html.escape(text)}</p>'
        '</section>'
    )


def render_solution(intro, cards):
    if not intro and not cards:
        return ""
    cards_html = ""
    if cards:
        cards_html = '<div class="solution-grid">' + "".join(
            f'<div class="solution-card"><h4>{html.escape(c["h"])}</h4><p>{html.escape(c["p"])}</p></div>'
            for c in cards
        ) + '</div>'
    intro_html = f'<p>{html.escape(intro)}</p>' if intro else ""
    return (
        '<section class="cs-section">'
        '<span class="cs-section-label"><span class="br">[</span>What we built<span class="br">]</span></span>'
        '<h2>The solution</h2>'
        f'{intro_html}'
        f'{cards_html}'
        '</section>'
    )


def render_outcomes(outcomes):
    if not outcomes:
        return ""
    items = "".join(f'<li>{html.escape(o)}</li>' for o in outcomes)
    return (
        '<section class="cs-section">'
        '<span class="cs-section-label"><span class="br">[</span>The results<span class="br">]</span></span>'
        '<h2>What happened</h2>'
        f'<ul class="outcomes">{items}</ul>'
        '</section>'
    )


def render_quote(quote, attr):
    if not quote:
        return ""
    return (
        '<div class="cs-quote">'
        f'<blockquote>{html.escape(quote)}</blockquote>'
        f'<div class="attribution">— {html.escape(attr) if attr else "Founder"}</div>'
        '</div>'
    )


def render_client_html(name, url):
    if not name:
        return ""
    if url:
        return f'<div class="client-name"><a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(name)}</a></div>'
    return f'<div class="client-name">{html.escape(name)}</div>'


def render_next(next_data):
    if not next_data:
        return ""
    slug, name = next_data
    return (
        f'<div class="next-study">'
        f'<a href="/case-studies/{slug}/">'
        f'<div><div class="label">Next case study</div>'
        f'<div class="name">{html.escape(name)}</div></div>'
        f'<span class="arrow">→</span>'
        f'</a></div>'
    )


def render_index_card(d):
    return (
        f'<a href="/case-studies/{d["slug"]}/" class="ix-card">'
        f'<div class="ix-card-head">'
        f'<div class="ix-mark"><span class="br">[</span>{html.escape(d["initials"])}<span class="br">]</span></div>'
        f'<div><div class="ix-name">{html.escape(d["client_name"])}</div>'
        f'<div class="ix-industry">{html.escape(d["industry"])}</div></div>'
        f'</div>'
        f'<p class="ix-desc">{html.escape(d["subtitle"])}</p>'
        f'<div class="ix-result">{d["result"]}</div>'
        f'<span class="ix-arrow">Read case study →</span>'
        f'</a>'
    )


# ───────────────────────────────────────── main ──
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    studies = []
    slugs_in_order = [
        "conscious-counsel", "affextionate-cuizine", "legal-intake",
        "sereia-official", "executive-recruiting", "ai-meeting-coach",
        "philly-basketball", "voice-erp", "sides-bbq",
        "beverly-hills-wellness", "allied-exteriors",
    ]

    for slug in slugs_in_order:
        src_path = SRC / slug / "index.html"
        if not src_path.exists():
            print(f"  - skip {slug} (no source)")
            continue
        data = extract(slug, src_path.read_text(encoding="utf-8"))
        studies.append(data)

    for i, d in enumerate(studies):
        next_d = studies[(i + 1) % len(studies)]  # circular
        next_data = (next_d["slug"], next_d["client_name"])
        head = SHARED_HEAD.format(
            title=f'{d["title"]} — ARK Partners case study',
            description=html.escape(d["subtitle"][:170]) if d["subtitle"] else f'{d["client_name"]} case study from ARK Partners.'
        )
        page = CASE_TEMPLATE.format(
            head=head,
            nav=NAV_HTML,
            client_name=html.escape(d["client_name"]),
            initials=html.escape(d["initials"]),
            industry=html.escape(d["industry"]),
            client_html=render_client_html(d["client_name"], d["client_url"]),
            title=html.escape(d["title"]),
            subtitle=html.escape(d["subtitle"]),
            metrics_html=render_metrics(d["metrics"]),
            challenge_html=render_challenge(d["challenge"]),
            solution_html=render_solution(d["solution_intro"], d["solution_cards"]),
            outcomes_html=render_outcomes(d["outcomes"]),
            quote_html=render_quote(d["quote"], d["quote_attr"]),
            next_study_html=render_next(next_data),
            footer=FOOTER_HTML,
        )
        out_dir = OUT / d["slug"]
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "index.html").write_text(page, encoding="utf-8")
        print(f"  ✓ wrote {out_dir}/index.html")

    cards_html = "".join(render_index_card(d) for d in studies)
    head = SHARED_HEAD.format(
        title="Case studies — ARK Partners",
        description="Real businesses share how ARK Partners built custom AI solutions that transformed their operations and boosted results.",
    )
    index_page = INDEX_PAGE_TEMPLATE.format(
        head=head,
        nav=NAV_HTML,
        cards_html=cards_html,
        footer=FOOTER_HTML,
    )
    (OUT / "index.html").write_text(index_page, encoding="utf-8")
    print(f"  ✓ wrote {OUT}/index.html with {len(studies)} cards")

    return studies


if __name__ == "__main__":
    studies = main()
    summary_path = OUT / "_studies.json"
    summary_path.write_text(json.dumps([{
        "slug": s["slug"], "initials": s["initials"], "industry": s["industry"],
        "name": s["client_name"], "subtitle": s["subtitle"], "result": s["result"],
        "tags": s["tags"],
    } for s in studies], indent=2), encoding="utf-8")
    print(f"\nSummary written to {summary_path}")
