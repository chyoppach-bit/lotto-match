import re
from collections import Counter
from itertools import combinations, repeat
from math import comb

NUM_RE = re.compile(r"\d+")


def decode_bytes(raw):
    # Try common encodings for text files exported on Windows / Android
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def parse_lines(text):
    # Returns (list of sorted 6-number tuples, number of skipped non-empty lines)
    combs = []
    skipped = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        vals = [int(x) for x in NUM_RE.findall(line)]
        if len(vals) == 6 and len(set(vals)) == 6 and all(1 <= v <= 45 for v in vals):
            combs.append(tuple(sorted(vals)))
        else:
            skipped += 1
    return combs, skipped


def load_file(path):
    with open(path, "rb") as f:
        raw = f.read()
    return parse_lines(decode_bytes(raw))


def count_with_selection(combs, selected):
    # Count lines sharing exactly 2..6 numbers with the selected set
    counts = {k: 0 for k in range(2, 7)}
    sel = frozenset(selected)
    if not sel:
        return counts
    inter = sel.intersection
    for c in combs:
        n = len(inter(c))
        if n >= 2:
            counts[n] += 1
    return counts


def count_pairs(c1, c2, progress=None):
    # Exact number of (line from c1, line from c2) pairs sharing exactly m numbers.
    # T_k = sum over pairs of C(intersection, k) is computed by hashing k-subsets,
    # then inverted with binomial inversion. Avoids the N*M nested loop.
    if len(c1) > len(c2):
        c1, c2 = c2, c1
    totals = {}
    for k in range(2, 7):
        if progress:
            progress(k)
        table = Counter()
        for c in c1:
            table.update(combinations(c, k))
        get = table.get
        t = 0
        for c in c2:
            t += sum(map(get, combinations(c, k), repeat(0)))
        totals[k] = t
        del table
    exact = {}
    for m in range(2, 7):
        exact[m] = sum((-1) ** (k - m) * comb(k, m) * totals[k] for k in range(m, 7))
    return exact
