import re
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai-opening-quality")

STOPWORDS = frozenset({
    "the","a","an","and","or","of","in","on","at","to","for","is","are","was","were",
    "with","this","that","these","those","from","by","as","it","its","not","but","how",
    "why","what","when","who","which","be","been","being","has","have","had","will",
    "would","could","should","can","do","does","did","no","so","than","then","there",
    "their","they","them","he","she","his","her","you","your","i","we","our","if",
    "into","out","up","down","about","still","just","one","also","me","my",
})

def normalize_opening(text, max_words=200):
    body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
    body = re.sub(r"<figure[^>]*>.*?</figure>", "", body, flags=re.DOTALL)
    body = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)
    body = re.sub(r"https?://\S+", "", body)
    body = re.sub(r"<[^>]+>", "", body)
    body = re.sub(r"[*_#`]", "", body)
    words = re.findall(r"[a-z']+", body.lower())
    return words[:max_words]

def shingles(words, k=6):
    content_positions = [i for i, w in enumerate(words) if w not in STOPWORDS and len(w) > 2]
    # shingle over the FULL token stream (including stopwords) for phrase fidelity,
    # but require at least min_content content words within the shingle to count
    result = set()
    for i in range(len(words) - k + 1):
        shingle = tuple(words[i:i+k])
        content_count = sum(1 for w in shingle if w not in STOPWORDS and len(w) > 2)
        if content_count >= 3:
            result.add(shingle)
    return result

def similarity(a, b):
    sa, sb = shingles(a), shingles(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)

if __name__ == "__main__":
    known_family = [
        "2026-03-08-architects-are-designing-buildings-for-the-wrong-sense.md",
        "2026-03-12-the-door-you-can-t-read-is-the-door-that-isn-t-there.md",
        "2026-03-14-the-frequency-you-designed-out.md",
        "2026-03-16-the-map-that-stops-at-the-door.md",
    ]
    openings = {}
    for f in sorted((REPO/"_posts").glob("*.md")):
        text = f.read_text(encoding="utf-8")
        openings[f.name] = normalize_opening(text)

    print("=== known family pairwise similarities ===")
    for i, a in enumerate(known_family):
        for b in known_family[i+1:]:
            s = similarity(openings[a], openings[b])
            print(f"  {s:.3f}  {a} <-> {b}")

    print()
    print("=== corpus-wide sweep: any pair >= 0.15 (excluding known family pairs) ===")
    names = list(openings.keys())
    hits = []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a, b = names[i], names[j]
            if a in known_family and b in known_family:
                continue
            s = similarity(openings[a], openings[b])
            if s >= 0.15:
                hits.append((s, a, b))
    hits.sort(reverse=True)
    print(f"total unrelated-pair hits >= 0.15: {len(hits)}")
    for s, a, b in hits[:20]:
        print(f"  {s:.3f}  {a} <-> {b}")
