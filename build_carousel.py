#!/usr/bin/env python3
"""Emit 11 ARK-brand homepage carousel cards from the cynthia case study sources."""
import html
from pathlib import Path
from build_case_studies import extract, TAGS, RESULT_OVERRIDES, NAME_OVERRIDES

SRC = Path("/home/cynthia/firebase-root/public/case-studies")
SLUGS = [
    "conscious-counsel", "affextionate-cuizine", "legal-intake",
    "sereia-official", "executive-recruiting", "ai-meeting-coach",
    "philly-basketball", "voice-erp", "sides-bbq",
    "beverly-hills-wellness", "allied-exteriors",
]

cards = []
for slug in SLUGS:
    d = extract(slug, (SRC / slug / "index.html").read_text())
    name = d["client_name"] or NAME_OVERRIDES.get(slug, slug)
    raw = d["quote"] if d["quote"] else d["subtitle"]
    if len(raw) > 200:
        cut = raw[:200]
        # back up to last sentence end if any
        for i in range(len(cut) - 1, max(len(cut) - 80, 0), -1):
            if cut[i] in ".!?":
                cut = cut[:i + 1]
                break
        else:
            cut = cut.rsplit(" ", 1)[0] + "…"
        quote = cut
    else:
        quote = raw
    tags = TAGS.get(slug, [])
    tags_html = "".join(f"<li>{t}</li>" for t in tags[:3])
    initials = html.escape(d["initials"])
    industry = html.escape(d["industry"])
    safe_name = html.escape(name)
    safe_quote = html.escape(quote)
    result = RESULT_OVERRIDES.get(slug, "")
    card = f'''<a href="/case-studies/{slug}/" class="story">
            <header class="story-head">
              <div class="story-mark"><span class="br">[</span>{initials}<span class="br">]</span></div>
              <div>
                <div class="story-name">{safe_name}</div>
                <div class="story-role">{industry}</div>
              </div>
            </header>
            <div class="story-stars" aria-label="Five stars">★★★★★</div>
            <ul class="story-tags">{tags_html}</ul>
            <p class="story-quote">"{safe_quote}"</p>
            <div class="story-result">{result}</div>
            <span class="story-link">Read case study <span class="arrow">→</span></span>
          </a>'''
    cards.append(card)

print("\n          ".join(cards))
