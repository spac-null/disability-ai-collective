import re, sys
from pathlib import Path

REPO = Path("/Users/stargatesgx/code/disability-collective-ai")

STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "of", "in", "on", "at", "to", "for",
    "is", "are", "was", "were", "with", "this", "that", "these", "those",
    "from", "by", "as", "it", "its", "not", "but", "how", "why", "what",
    "when", "who", "which", "be", "been", "being", "has", "have", "had",
    "will", "would", "could", "should", "can", "do", "does", "did", "no",
    "so", "than", "then", "there", "their", "they", "them", "he", "she",
    "his", "her", "you", "your", "i", "we", "our", "if", "into", "out",
    "up", "down", "about", "still", "just", "one", "also",
})

def normalize_paragraphs(text):
    body = re.sub(r'^---.*?\n---\n', '', text, flags=re.DOTALL)
    body = re.sub(r'<figure[^>]*>.*?</figure>', '', body, flags=re.DOTALL)
    body = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', body)
    body = re.sub(r'<[^>]+>', '', body)
    paras = [p.strip() for p in body.split("\n\n") if p.strip()]
    return paras

def content_words(p):
    words = re.findall(r"[a-z']+", p.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}

def jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter/union if union else 0.0

def find_consecutive_run_matches(paras, sim_threshold=0.7, min_content_words=8, min_run=3, min_offset=4):
    word_sets = [content_words(p) for p in paras]
    n = len(paras)
    eligible = [len(ws) >= min_content_words for ws in word_sets]
    # pairwise match matrix (only for eligible, offset >= min_offset)
    matches = {}
    for i in range(n):
        if not eligible[i]:
            continue
        for j in range(i+min_offset, n):
            if not eligible[j]:
                continue
            s = jaccard(word_sets[i], word_sets[j])
            if s >= sim_threshold:
                matches[(i,j)] = s
    # find consecutive runs with fixed offset
    runs = []
    for (i,j), s in sorted(matches.items()):
        offset = j - i
        # try to extend a run starting at i with this offset
        run = [(i,j,s)]
        k = 1
        while (i+k, j+k) in matches:
            run.append((i+k, j+k, matches[(i+k,j+k)]))
            k += 1
        if len(run) >= min_run:
            # avoid re-recording sub-runs starting mid-run
            if not runs or runs[-1][-1][0] != i:
                runs.append(run)
    # dedupe: keep runs not fully contained in a longer one starting earlier
    dedup = []
    seen_starts = set()
    for run in sorted(runs, key=lambda r: -len(r)):
        key = (run[0][0], run[0][1]-run[0][0])
        if run[0][0] in seen_starts:
            continue
        dedup.append(run)
        for (i,j,s) in run:
            seen_starts.add(i)
    return dedup

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "corpus"
    if mode == "floorplan":
        text = (REPO / "_posts/2026-03-31-the-floor-plan-of-disappearance.md").read_text()
        paras = normalize_paragraphs(text)
        print(f"{len(paras)} paragraphs")
        for run in find_consecutive_run_matches(paras):
            print(f"RUN: {[(i,j,round(s,2)) for i,j,s in run]}")
    else:
        total_triggered = 0
        for f in sorted((REPO/"_posts").glob("*.md")):
            text = f.read_text(encoding="utf-8")
            paras = normalize_paragraphs(text)
            runs = find_consecutive_run_matches(paras)
            if runs:
                total_triggered += 1
                print(f"{f.name}: {len(runs)} run(s), longest={max(len(r) for r in runs)}")
        print(f"\nTotal articles triggered: {total_triggered} / 140")
