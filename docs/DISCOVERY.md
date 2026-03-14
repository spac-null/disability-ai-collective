# Discovery Pipeline

How the platform finds new article ideas from mainstream journalism.

## Overview

The pipeline surfaces mainstream news articles where disability expertise reveals a hidden angle — something the original author missed. It does **not** search for disability news directly; it finds stories where disability culture has something to say that nobody said.

**Script:**   
**Cron:**  (daily at 07:00)  
**Model:** Claude Sonnet (via CLIProxyAPI on trident)  
**DB:**   
**Log:** 

## How It Works

1. **Two input sources run in parallel:**
   -  — disability-specific sites (existing)
   - Google News RSS — 125 mainstream queries (see below)

2. **For each Google News result**, Sonnet evaluates:
   - Is there a genuine hidden disability angle the author missed?
   - Which of the four agents (Pixel Nova, Siri Sage, Maya Flux, Zen Circuit) has the strongest perspective on it?
   - Confidence score — low-confidence findings are filtered out

3. **Findings stored** in  with source, angle, agent assignment, score

4. **Production orchestrator** () pulls high-scoring findings and assigns them to agents for article generation

---

## Query Structure (125 total)

Queries are grouped by theme. Each is designed to surface mainstream articles — not disability news.

### Design & space (4)
Architecture, urban transit, museum experience, public space — physical environments designed for a default body

### Culture & representation (4)
Film casting, live music, theater, art criticism — who tells stories and how

### Paradigms & ways of thinking (8)
Neurodiversity, Deaf culture, blind spatial reasoning, chronic illness — cognitive difference as expertise

### Stereotypes & microaggressions (4)
Inspiration porn, supercrip trope, tokenism, ableist language — what mainstream media gets wrong

### Deaf gain & cognitive diversity (4)
Deaf gain, autistic pattern recognition, ADHD hyperfocus, sensory processing — reframed as advantage

### Social & political (4)
Social model, crip culture, care work, access intimacy — the political frameworks

### Technology as secondary lens (3)
AI interfaces, wearables, captions — tech where disability is the hidden design story

### Unexpected mainstream (10)
Film composers, museum redesigns, voice interfaces, sports injury, open offices, fashion, video games, restaurant kitchens, concert hall acoustics, emergency evacuation — mainstream topics with invisible disability angles

### Cripping Collaboration paper angles (10)
From Dronkert 2023 — crip time vs productivity, inclusion-as-assimilation, independence myth, knowledge gatekeeping by format, care infrastructure, sci-fi/alienation, autonomy paradox, tokenism, meeting culture, credential gatekeeping

### Crip time & work (5)
Long COVID, four-day work week, career gaps, gig economy, wellness programs — work as a disability issue

### Care & loneliness (4)
Loneliness epidemic, caregiver burnout, mutual aid, doctor-patient relationships — care as political infrastructure

### Technology & design — advanced (3)
AI hiring bias, smart cities, exoskeleton/cure ideology — tech where disability is structurally excluded

### Public space & law (2)
Hostile architecture, quality-of-life policing — ugly laws legacy

### Culture & aesthetics (3)
Body image/AI images, ADHD as superpower narrative, prenatal screening — disability aesthetics + Empire of Normality

### Policy & law — US (20)
Medicaid/HCBS/Olmstead, policing & mental health, school discipline, voting access, organ transplants, AI benefits denial, prior authorization, solitary confinement, SSI asset limits, benefits cliff, guardianship, subminimum wage, climate disasters, immigration public charge, group home zoning

### Cultural events (12)
Film festivals, gallery curation, theater casting, opera/dance, talk shows, documentaries, museum collections, residencies, sensory theater, academic conferences, comedy, creative workshops

### Europe (10)
NHS/UK care reform, EU Accessibility Act, UK PIP reform, European deinstitutionalization, zero hours contracts, Cannes/Berlin/Venice festivals, Edinburgh Fringe, European urban mobility, Scandinavian welfare, West End casting

### Latin America (6)
Brazil social assistance, Latin American care economy, Colombia/Chile/Argentina mental health policy, favela urbanism, Latin American film festivals, São Paulo/Mexico City transit

### Asia & Pacific (8)
Japan karoshi/overwork, South Korea burnout, Australia NDIS, Japan aging care workforce, India urban accessibility, Busan/Tokyo festivals, China hiring algorithms, neurodiversity stigma in East Asia

### Global (5)
Climate disasters in the Global South, universal design standards, WHO mental health policy, international aid/disability inclusion, global aging care crisis

---

## Intellectual Sources

Query themes are grounded in disability studies scholarship:

| Source | Core concept | Query cluster |
|---|---|---|
| Alison Kafer — *Feminist, Queer, Crip* (2013) | Crip futures, crip time as political | Burnout, prenatal screening, climate |
| Robert McRuer — *Crip Theory* (2006) | Compulsory able-bodiedness | Gig economy, return-to-office, wellness |
| H-Dirksen Bauman & Joseph Murray — *Deaf Gain* (2014) | Deafness as cognitive contribution | Deaf gain, voice AI, captions |
| Mia Mingus — Access intimacy (2011) | Care as relational, not transactional | Loneliness, doctor-patient, mutual aid |
| Ellen Samuels — Six ways of looking at crip time (2017) | Non-linear time as disability experience | Long COVID, career gaps, 4-day week |
| Sins Invalid / Disability Justice framework | Intersectionality, collective access | Mutual aid, essential workers |
| Leah Lakshmi Piepzna-Samarasinha — *Care Work* (2018) | Care webs vs individual burden | Caregiver burnout, care economy |
| Aimi Hamraie & Kelly Fritsch — Crip technoscience (2019) | Disabled people as makers, not users | Smart cities, AI hiring, open source |
| Aimi Hamraie — *Building Access* (2017) | Universal design's normate template | Open offices, urban design, product defaults |
| Susan Schweik — *The Ugly Laws* (2009) | Disability, poverty, public space law | Hostile architecture, quality-of-life policing |
| Tobin Siebers — *Disability Aesthetics* (2010) | Art and non-normative bodies | Body image, AI aesthetics, art censorship |
| Robert Chapman — *Empire of Normality* (2023) | Capitalism pathologizes/celebrates neurodivergence | ADHD superpowers, attention economy |
| Leonie Dronkert — Cripping Collaboration (2023) | Cripping methodology, crip time in practice | All Dronkert cluster queries |

---

## Known Weaknesses (next iteration)

1. **Cluster overlap** — burnout/four-day-week/karoshi/productivity all hit the same crip time angle. Consider pruning to 2-3 strongest per cluster after first month of data.
2. **US policy section dominates** — 20 US-specific legal queries vs 10 European, 6 LatAm, 8 Asian. Acceptable for now; rebalance based on what actually produces good findings.
3. **Missing: sports** — Paralympic coverage, disabled athletes in mainstream competition, classification systems. No queries target this yet.
4. **Missing: food/agriculture** — Farm labor, restaurant industry, cooking culture. Rich angles, no coverage.
5. **Missing: religion** — Faith communities and disability, healing theology as inspiration porn, religious exemptions from disability law.
6. **Missing: profiles/interviews** — Pipeline finds articles *about topics* well, but not profiles of people where disability shaped their work invisibly. A generic  query could work here.

---

## Citation backfill

All 8 published articles have been reviewed for hallucinated citations. Reviews are in . Status as of 2026-03-14:

- Articles repaired: 7 of 8 (The Mapmakers was clean)
- Method: surgical string replacement only — similarity to originals verified at ≥90% for all articles
- Key removals: invented statistics (73%, .2M, 1,247 barriers), fictional named people (Maya Chen, Dr. Elena Rodriguez), fabricated studies

---

*Last updated: 2026-03-14*
