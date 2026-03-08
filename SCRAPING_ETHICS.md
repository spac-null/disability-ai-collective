# 🔍 DISABILITY-AI SCRAPING ETHICS GUIDE
## How We Research Without Harming

---

## 🎯 OUR SCRAPING PHILOSOPHY

**"We scrape to understand, not to exploit. We collect to amplify, not to appropriate."**

Every web request we make should:
1. **Respect community boundaries**
2. **Credit creators explicitly**
3. **Question power dynamics**
4. **Prioritize accessibility**

---

## ✅ DO SCRAPE

### **1. Public Accessibility Resources**
- Government accessibility guidelines and reports
- Academic papers on disability and AI (open access)
- Corporate accessibility statements and reports
- Disability organization publications and blogs
- Open source accessibility tools and documentation

### **2. Disability Culture & Innovation**
- Disabled artist and creator portfolios (with attribution)
- Disability tech conference proceedings and talks
- Accessibility-focused GitHub repositories
- Disability-led startup announcements and case studies
- Disability culture publications and zines

### **3. AI Accessibility Developments**
- AI company accessibility documentation
- Research papers on AI and disability (properly cited)
- Accessibility tool release notes and changelogs
- Disability community discussions on AI (public forums)
- Regulatory developments in accessible AI

---

## 🚫 DO NOT SCRAPE

### **1. Private Disability Spaces**
- Closed disability support groups or forums
- Personal disability blogs without clear public intent
- Disability community members' private social media
- Medical or personal disability information
- Any space requiring login or membership

### **2. Exploitative Content**
- "Inspiration porn" disability content
- Ableist AI marketing or promotional material
- Disability tokenization in corporate diversity reports
- Any content that harms or stereotypes disabled people
- Paywalled disability research (respect academic labor)

### **3. Overwhelming Small Communities**
- Low-traffic disability forums (respect their bandwidth)
- Individual disabled creators' sites (check robots.txt)
- Community archives not meant for mass scraping
- Any site that blocks bots in robots.txt
- Sites with clear "no scraping" policies

---

## 🔄 OUR SCRAPING PROTOCOLS

### **Rate Limiting (Always)**
```python
# Minimum 3 seconds between requests
time.sleep(3 + random.uniform(0, 2))

# Respect robots.txt
from urllib.robotparser import RobotFileParser
rp = RobotFileParser()
rp.set_url(f"{base_url}/robots.txt")
rp.read()
if rp.can_fetch("*", url):
    # Proceed with scraping
```

### **Attribution (Always)**
```python
# Every scraped item gets:
metadata = {
    "source_url": url,
    "scraped_date": datetime.now().isoformat(),
    "attribution": "Original creator/source",
    "license": "If known",
    "accessibility_notes": "How accessible was the source?",
    "community_impact": "How does this help disability community?"
}
```

### **Accessibility Checking (Always)**
```python
# Before scraping, check:
# 1. Is the site reasonably accessible?
# 2. Are we making it less accessible by scraping?
# 3. Can we present findings accessibly?

def check_scraping_ethics(url):
    """Return True if ethical to scrape this URL"""
    checks = [
        not is_private_community(url),
        not requires_login(url),
        not blocked_by_robots_txt(url),
        has_clear_public_intent(url),
        not_overwhelming_small_site(url),
        contributes_to_disability_knowledge(url)
    ]
    return all(checks)
```

---

## 📝 OUR CONTENT GUIDELINES

### **When We Share Scraped Content:**
1. **Always link back** to original source
2. **Always credit** disabled creators by name
3. **Always contextualize** - don't just repost
4. **Always add value** - analysis, commentary, synthesis
5. **Always check accessibility** of our presentation

### **Transparency Requirements:**
```markdown
## Research Source Transparency

**Source:** [Original Title](https://original.url)
**Author:** Creator Name (if known)
**Scraped:** YYYY-MM-DD HH:MM UTC
**Accessibility Notes:** [Brief assessment]
**Our Analysis:** [How this contributes to disability-AI knowledge]
**Community Impact:** [How this helps disabled people]
```

---

## 🛡️ OUR SAFETY PROTOCOLS

### **Data Handling:**
- **No personal information** ever stored
- **No medical/disability details** without explicit consent
- **No private community content** even if technically public
- **Regular data audits** to ensure compliance

### **Harm Reduction:**
- **Immediate takedown** if anyone requests their content removed
- **Correction policy** for any errors in attribution or analysis
- **Community feedback loop** - we listen and adjust
- **Transparent opt-out** process for anyone we feature

---

## 🎨 OUR PRESENTATION STANDARDS

### **Accessibility-First Display:**
```html
<!-- Every research finding includes: -->
<div class="research-item" role="article" aria-labelledby="title-123">
  <h2 id="title-123">Clear, Descriptive Title</h2>
  <div class="source-info" aria-label="Source information">
    <p><strong>Source:</strong> <a href="..." aria-label="Original source">Site Name</a></p>
    <p><strong>Author:</strong> Creator Name</p>
    <p><strong>Accessibility:</strong> Screen reader friendly, high contrast</p>
  </div>
  <!-- Content with proper heading structure -->
  <img src="..." alt="Descriptive alt text for disability context">
</div>
```

### **Citation Style:**
```
[Creator Last Name, First Name]. (Year). "Title." 
[Website/Publication]. Retrieved [Date] from [URL].
[Accessibility notes].
```

---

## 🔍 OUR QUALITY CHECKS

### **Before Publishing Any Scraped Content:**
1. ✅ **Ethics check** - Did we follow all protocols?
2. ✅ **Attribution check** - Is credit clear and accurate?
3. ✅ **Accessibility check** - Is our presentation accessible?
4. ✅ **Value check** - Did we add meaningful analysis?
5. ✅ **Community check** - Does this help disabled people?

### **Weekly Audit:**
- Review all scraped content for compliance
- Check for takedown requests or corrections
- Assess community feedback and adjust protocols
- Update blocked sites list based on feedback

---

## 🌟 OUR SCRAPING MANIFESTO

**We scrape to:**
- **Amplify disabled voices** that mainstream media ignores
- **Map disability-AI intersections** that others overlook
- **Build accessible knowledge** that benefits everyone
- **Challenge ableist assumptions** in tech development
- **Document disability innovation** as it happens

**We never scrape to:**
- **Exploit disability for clicks or content**
- **Appropriate disabled creators' work**
- **Overwhelm small disability communities**
- **Reinforce harmful stereotypes**
- **Build without community benefit**

---

## 📞 OUR ACCOUNTABILITY

**If we mess up:**
1. **Acknowledge immediately**
2. **Correct publicly**
3. **Learn and adjust protocols**
4. **Report back to community**

**Contact for corrections/removals:**
- Email: corrections@disability-ai-collective.org
- GitHub Issues: https://github.com/spac-null/disabilityAI/issues
- Transparency log: /transparency/

---

*This guide is living. It evolves with community feedback.*  
*Last updated: 2026-03-08*  
*Next review: 2026-04-08*

**Scrape with care. Credit with clarity. Build with community.** 🔍