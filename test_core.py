import random
from lotto_core import parse_lines, count_pairs, count_with_selection

text = "1 2 3 4 5 6\n7,8,9,10,11,12\n\ufeff13\t14\t15\t16\t17\t18\nbad line\n1 2 3 4 5 99\n"
combs, skipped = parse_lines(text)
assert len(combs) == 3 and skipped == 2, (combs, skipped)

random.seed(1)
a = [tuple(sorted(random.sample(range(1, 46), 6))) for _ in range(300)]
b = [tuple(sorted(random.sample(range(1, 46), 6))) for _ in range(250)]
a += a[:20]
brute = {k: 0 for k in range(2, 7)}
for x in a:
    for y in b:
        n = len(set(x) & set(y))
        if n >= 2:
            brute[n] += 1
assert count_pairs(a, b) == brute, (count_pairs(a, b), brute)
assert count_pairs(b, a) == brute
sel = [1, 2, 3, 4, 5, 6, 7]
brute_sel = {k: 0 for k in range(2, 7)}
for x in a:
    n = len(set(x) & set(sel))
    if n >= 2:
        brute_sel[n] += 1
assert count_with_selection(a, sel) == brute_sel
print("ALL TESTS PASSED", brute)
