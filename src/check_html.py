"""Structural / consistency regression guard for the generated HTML.

Run after build.py:
    cd src && python check_html.py

Exits non-zero on any ERROR (used by CI). WARN/INFO print but don't fail.
Checks each lesson + index:
* balanced tags (div/details/table/pre/summary) and details<->summary
* a <title> + meta description; exactly one <h1> per lesson
* both languages present (lang-zh and lang-en blocks)
* no unescaped '<' inside <pre> code blocks
* cross-references "第 N 课" within 1..MAX_LESSON (forward refs allowed)
* nav prev/next chain matches shell.PAGES order
* index TOC lists every page; '共 N 课 · N 个部分' pill matches PAGES
* registry CONTENT has non-empty zh+en for every PAGES filename (no orphan keys)
* (WARN) every lesson has a key-points card and an analogy card
* (WARN) per-lesson visual-block and SVG floors (>= 6 diagrams, >= 4 SVGs over both langs)

The "第 N 课" cross-ref check matches Chinese-Arabic digits only (e.g. "第 12 课");
English ("Lesson N") or Chinese-numeral references are not range-checked.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)

import shell  # noqa: E402
from registry import CONTENT  # noqa: E402
import quizzes  # noqa: E402

PAGES = shell.PAGES
ORDER = [p[0] for p in PAGES]
TOTAL = len(PAGES)
MAX_LESSON = 61  # planned final lesson count (incl. Part 11 capstone); cross-refs may point forward
MIN_CONTENT = 80  # min chars of zh/en source content per lesson (catch empty translations)

PRE_INLINE = ("span", "strong", "b", "em", "u", "a")
SOFT_EXEMPT = set()  # no glossary lesson in this guide; all lessons held to the full bar

# Visual-block density (soft): containers that count as a "diagram/table".
DIAGRAM_CLASSES = ("layers", "vflow", "flow", "cols", "cellgroup", "timeline", "trace")
MIN_DIAGRAMS = 6  # per lesson, counting BOTH languages (>= 3 per language)
MIN_SVGS = 4  # per lesson, counting BOTH languages (>= 2 hand-drawn .fig SVGs per language)
MIN_CJK = 1800  # per-lesson zh CJK floor; diagram/code-heavy lessons run leaner, prose lessons exceed it

# Index TOC subtitle (SUBTITLES) limits — keep the TOC scannable, not a wall of
# text. The good early lessons (L01-14) sit at ~46-70 zh chars; later ones had
# ballooned to 400-530. The detail lives in the lesson body, not the TOC blurb.
SUB_MAX_ZH = 80       # max Chinese chars per subtitle
SUB_MAX_EN = 125      # max English chars per subtitle (keeps the TOC balanced both langs)
SUB_FORBID = re.compile(r"\.(?:ts|tsx|js|py|sql|prisma|json|yml|md):\d")  # no file:line in TOC

# Every class used in generated HTML must be defined in shell.CSS. Catches
# consolidation artifacts (e.g. a diagram-variant whose CSS was never merged in,
# rendering silently broken). Whitelist intentional no-style hooks.
CSS_DEFINED = set(re.findall(r"\.([A-Za-z][\w-]*)", shell.CSS))
CSS_CLASS_WHITELIST = {"prev"}  # footnav prev link is styled via `.footnav a`; needs no own rule

issues = []


def add(sev, f, msg):
    issues.append((sev, f, msg))


def check_balance(name, html, tag):
    o = len(re.findall(rf"<{tag}[\s>]", html))
    c = len(re.findall(rf"</{tag}>", html))
    if o != c:
        add("ERR", name, f"<{tag}> unbalanced: {o} open / {c} close")


def check_classes(name, html):
    """Every class used in the HTML must have a `.cls` rule in shell.CSS."""
    seen = set()
    for m in re.findall(r'class="([^"]+)"', html):
        for c in m.split():
            if c in seen or c in CSS_CLASS_WHITELIST or c in CSS_DEFINED:
                continue
            seen.add(c)
            add("ERR", name, f"undefined CSS class {c!r} (no .{c} rule in shell.CSS)")


def check_subtitles():
    """Index TOC blurbs must stay short and free of file:line citations."""
    for fname, (sz, se) in shell.SUBTITLES.items():
        if len(sz) > SUB_MAX_ZH:
            add("ERR", fname, f"subtitle zh too long: {len(sz)} > {SUB_MAX_ZH} chars")
        if len(se) > SUB_MAX_EN:
            add("ERR", fname, f"subtitle en too long: {len(se)} > {SUB_MAX_EN} chars")
        for lang, s in (("zh", sz), ("en", se)):
            if SUB_FORBID.search(s):
                add("ERR", fname, f"subtitle {lang} leaks a file:line citation (belongs in the lesson body)")


def check_xrefs(lesson_html_by_name):
    """Inter-lesson references (第N课 / Lesson N) should be auto-linked. Guards
    against the build-time autolink silently regressing. Ranges like 第34、35课
    only link partially, so the bar is a ratio, not 100%."""
    total = linked = 0
    for html in lesson_html_by_name.values():
        total += len(re.findall(r"第\s*\d{1,2}\s*课", html))
        total += len(re.findall(r"\bLesson\s+\d{1,2}\b", html))
        linked += len(re.findall(r'<a class="xref"[^>]*>第\s*\d{1,2}\s*课', html))
        linked += len(re.findall(r'<a class="xref"[^>]*>Lesson\s+\d{1,2}', html))
    if total and linked / total < 0.8:
        add("ERR", "lessons", f"only {linked}/{total} inter-lesson refs auto-linked (<80%); autolink regressed")


def check_glossary():
    """The glossary page must exist, carry enough terms, and only link to real lessons."""
    if len(shell.GLOSSARY) < 50:
        add("ERR", "glossary", f"only {len(shell.GLOSSARY)} terms (want >= 50)")
    for entry in shell.GLOSSARY:
        fname = entry[4]
        if fname not in ORDER:
            add("ERR", "glossary", f"term {entry[0]!r} links to unknown lesson {fname!r}")
    if not os.path.exists(os.path.join(ROOT, "glossary.html")):
        add("ERR", "glossary.html", "missing (run build.py)")


def check_quiz_coverage():
    """Every lesson must ship a non-empty self-test quiz in both languages.
    quizzes.render() returns '' for a missing lesson, which would silently pass
    the structural checks — so assert coverage explicitly."""
    for fname in ORDER:
        for lang in ("zh", "en"):
            if not quizzes.render(fname, lang).strip():
                add("ERR", fname, f"missing {lang} quiz (quizzes.render returned empty)")


def check_subtitle_coverage():
    """Every lesson must have an index TOC subtitle; a missing entry renders a
    blank blurb in the index with no other error."""
    for fname in ORDER:
        if fname not in shell.SUBTITLES:
            add("ERR", fname, "missing SUBTITLES entry (index blurb would be blank)")


# The read-time FINAL dedup over ReplacingMergeTree is taught in L08. Guard against
# an inter-lesson reference attributing that mechanism to the wrong lesson — the exact
# mis-citation class the content audit found in L13/L54. Runs on the lesson SOURCE
# (pre-autolink) so 第N课 / Lesson N / the compact L08 form are all visible, and anchors
# on the ReplacingMergeTree…FINAL co-occurrence (which is unambiguously the L08 mechanism).
_XREF_RMT_FINAL = re.compile(r"ReplacingMergeTree[^。.<]{0,60}?FINAL")
_XREF_LESSON_REF = re.compile(r"第\s*(\d{1,2})\s*课|Lesson\s+(\d{1,2})\b|\bL0?(\d{1,2})\b")
_XREF_EXPECTED_LESSON = 8


def check_xref_semantics():
    """WARN if ReplacingMergeTree+FINAL is cited next to a lesson reference that is
    not L08 (and L08 is absent from the window). Skips windows with no lesson ref
    (a lesson teaching the mechanism without citing one is fine)."""
    for fname in ORDER:
        c = CONTENT.get(fname) or {}
        for lang in ("zh", "en"):
            src = c.get(lang, "")
            for m in _XREF_RMT_FINAL.finditer(src):
                window = src[max(0, m.start() - 110): m.end() + 110]
                nums = {
                    int(next(g for g in nm.groups() if g))
                    for nm in _XREF_LESSON_REF.finditer(window)
                }
                if nums and _XREF_EXPECTED_LESSON not in nums:
                    add("WARN", fname, f"ReplacingMergeTree+FINAL ({lang}) cited near Lesson(s) {sorted(nums)} but it is taught in L{_XREF_EXPECTED_LESSON}")



def check_score_terms(lesson_html):
    """Score terminology stays consistent: the scoring act/entity is 「评分」, the
    numeric value is 「分数」. 「打分」 was unified to 「评分」 and must not reappear
    (checked on rendered output so quiz/chrome sources are covered too)."""
    for fname, html in lesson_html.items():
        if "打分" in html:
            add("ERR", fname, "uses 「打分」 — unify to 「评分」 (scoring act/entity)")
        if re.search(r"\btradeoffs?\b", html):
            add("ERR", fname, "uses 'tradeoff(s)' — unify to the hyphenated 'trade-off'")


def check_prereqs():
    """Every PREREQS key must be a real lesson, and its hint may only reference
    EARLIER lessons (no forward or self references)."""
    for fname, hint in shell.PREREQS.items():
        if fname not in ORDER:
            add("ERR", "prereqs", f"PREREQS key not a lesson: {fname!r}")
            continue
        self_i = ORDER.index(fname)
        for txt in hint:
            for m in re.finditer(r"第\s*(\d+)\s*课|Lesson\s+(\d+)", txt):
                n = int(m.group(1) or m.group(2))
                if n - 1 >= self_i:
                    add("ERR", fname, f"prereq hint references self/later lesson {n}")


def check_part_finales(lesson_html):
    """Every Part's last lesson must carry the wrap-up suffix on its key-points
    card tag (both zh and en); every non-ender must keep the plain tag."""
    for fname, html in lesson_html.items():
        n = shell.PART_ENDERS.get(fname)
        if n:
            is_cap = fname == PAGES[-1][0]
            zh_want = "🎯 本课要点 · 全书终" if is_cap else f"🎯 本课要点 · 第{shell._CN_NUM[n]}部分收官"
            en_want = "🎯 Key points · The end" if is_cap else f"🎯 Key points · Part {n} wrap-up"
            if zh_want not in html:
                add("ERR", fname, f"part-ender missing zh finale {zh_want!r}")
            if en_want not in html:
                add("ERR", fname, f"part-ender missing en finale {en_want!r}")
        else:
            if "🎯 本课要点</div>" not in html:
                add("ERR", fname, "non-ender zh key-points tag is not the plain form")
            if "🎯 Key points</div>" not in html:
                add("ERR", fname, "non-ender en key-points tag is not the plain form")


def check_lesson(fname, html):
    for tag in ("div", "details", "table", "pre", "summary"):
        check_balance(fname, html, tag)
    check_classes(fname, html)
    nd = len(re.findall(r"<details", html))
    ns = len(re.findall(r"<summary", html))
    if nd != ns:
        add("ERR", fname, f"details({nd}) != summary({ns})")
    h1 = len(re.findall(r"<h1", html))
    if h1 == 0:
        add("ERR", fname, "missing <h1>")
    elif h1 > 1:
        add("WARN", fname, f"{h1} <h1> (expected 1)")
    if "<title>" not in html:
        add("ERR", fname, "missing <title>")
    if 'name="description"' not in html:
        add("ERR", fname, "missing meta description")
    if 'class="lang-zh"' not in html:
        add("ERR", fname, "missing lang-zh content")
    if 'class="lang-en"' not in html:
        add("ERR", fname, "missing lang-en content")
    if fname not in SOFT_EXEMPT:
        if "本课要点" not in html and "Key points" not in html:
            add("WARN", fname, "no key-points card")
        if "card analogy" not in html:
            add("WARN", fname, "no analogy card")
        nvis = sum(html.count(f'class="{c}"') for c in DIAGRAM_CLASSES)
        nvis += html.count('<table class="t"')
        if nvis < MIN_DIAGRAMS:
            add("WARN", fname, f"only {nvis} visual blocks (want >= {MIN_DIAGRAMS}; add diagrams)")
        nsvg = html.count("<svg")
        if nsvg < MIN_SVGS:
            add("WARN", fname, f"only {nsvg} SVGs (want >= {MIN_SVGS}; >= 2 hand-drawn .fig SVGs per language)")

    for pre in re.findall(r"<pre[^>]*>(.*?)</pre>", html, re.S):
        cleaned = re.sub(r"</?(?:%s)\b[^>]*>" % "|".join(PRE_INLINE), "", pre)
        if re.search(r"<(?!/)", cleaned):
            m = re.search(r"<(?!/).{0,20}", cleaned)
            add("ERR", fname, f"unescaped '<' in <pre>: {m.group(0)!r}")
            break

    for m in re.finditer(r"第\s*([0-9、,，~\-－\s]+?)\s*课", html):
        nums = [int(x) for x in re.findall(r"[0-9]+", m.group(1))]
        over = [n for n in nums if n == 0 or n > MAX_LESSON]
        if over:
            add("ERR", fname, f"course ref out of range: {m.group(0)!r} -> {over}")

    if fname in ORDER:
        idx = ORDER.index(fname)
        if idx + 1 < TOTAL and f'href="{ORDER[idx + 1]}"' not in html:
            add("ERR", fname, f"next link missing -> {ORDER[idx + 1]}")
        if idx > 0 and f'href="{ORDER[idx - 1]}"' not in html:
            add("ERR", fname, f"prev link missing -> {ORDER[idx - 1]}")


def main():
    lesson_html = {}
    for page in PAGES:
        fname = page[0]
        path = os.path.join(ROOT, "lessons", fname)
        if not os.path.exists(path):
            add("ERR", fname, "lesson file missing (run build.py)")
            continue
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        lesson_html[fname] = html
        check_lesson(fname, html)

    # registry <-> PAGES alignment + non-empty bilingual source content.
    # Checking the source (not the rendered HTML) avoids being fooled by the
    # shell chrome, which always emits lang-zh/lang-en spans.
    for page in PAGES:
        fname = page[0]
        c = CONTENT.get(fname)
        if c is None:
            add("ERR", fname, "no registry CONTENT entry")
            continue
        for lang in ("zh", "en"):
            if len(c.get(lang, "").strip()) < MIN_CONTENT:
                add("ERR", fname, f"{lang} content missing or too short")
        if fname not in SOFT_EXEMPT:
            cjk = len(re.findall(r"[\u4e00-\u9fff]", c.get("zh", "")))
            if cjk < MIN_CJK:
                add("WARN", fname, f"only {cjk} CJK chars in zh (want >= {MIN_CJK})")
    for fname in CONTENT:
        if fname not in ORDER:
            add("ERR", "registry", f"CONTENT key not in PAGES: {fname}")

    check_subtitles()
    check_subtitle_coverage()
    check_quiz_coverage()
    check_xrefs(lesson_html)
    check_xref_semantics()
    check_glossary()
    check_part_finales(lesson_html)
    check_prereqs()
    check_score_terms(lesson_html)

    index_path = os.path.join(ROOT, shell.INDEX_FILE)
    with open(index_path, encoding="utf-8") as fh:
        idx = fh.read()
    check_classes("index.html", idx)
    for page in PAGES:
        fname, tz, te = page[0], page[1], page[2]
        if fname not in idx:
            add("ERR", "index.html", f"TOC missing entry {fname}")
        if shell.esc(tz) not in idx:
            add("WARN", "index.html", f"TOC missing zh title {tz!r}")
        if shell.esc(te) not in idx:
            add("WARN", "index.html", f"TOC missing en title {te!r}")
    m = re.search(r"共 (\d+) 课 · (\d+) 个部分", idx)
    if m:
        if int(m.group(1)) != TOTAL:
            add("ERR", "index.html", f"count says {m.group(1)} but PAGES has {TOTAL}")
        nparts = len({p[3] for p in PAGES})
        if int(m.group(2)) != nparts:
            add("ERR", "index.html", f"parts says {m.group(2)} but PAGES has {nparts}")
    else:
        add("WARN", "index.html", "could not find '共 N 课 · N 个部分' pill")

    errs = [i for i in issues if i[0] == "ERR"]
    warns = [i for i in issues if i[0] == "WARN"]
    rank = {"ERR": 0, "WARN": 1, "INFO": 2}
    for sev, f, msg in sorted(issues, key=lambda x: rank[x[0]]):
        print(f"  [{sev}] {f}: {msg}")
    print(f"\nChecked {TOTAL} lessons + index - {len(errs)} error(s), {len(warns)} warning(s).")
    if errs:
        print("structural check FAILED")
        return 1
    print("structural check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
