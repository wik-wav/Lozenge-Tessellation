# -*- coding: utf-8 -*-
"""
Asaxi Vocab Forge — core engine.
Stdlib only. Indexes the vault lexicon, validates candidate words,
generates template-faithful Markdown entries, and updates list files.
"""
import json
import re
import unicodedata
from pathlib import Path

# ---------------------------------------------------------------- config

TOOL_DIR = Path(__file__).resolve().parent


def find_vault_root(start: Path) -> Path:
    p = start
    for _ in range(6):
        if (p / "01_Worldbuilding").is_dir():
            return p
        p = p.parent
    raise RuntimeError("Vault root not found (no 01_Worldbuilding above tool dir)")


def load_config():
    cfg_path = TOOL_DIR / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    root = Path(cfg["vault_root"]) if cfg.get("vault_root") else find_vault_root(TOOL_DIR)
    cfg["_root"] = root
    cfg["_lexicon"] = root / cfg["lexicon_dir"]
    cfg["_fields"] = root / cfg["semantic_fields_dir"]
    cfg["_idioms"] = root / cfg["idioms_dir"] if cfg.get("idioms_dir") else None
    # Grammar_Structure sits beside the lexicon and also holds real lexeme entries
    # (particles, pronouns, connectors, ...). Scan it too; doc pages are filtered
    # out in Lexicon._load via the grammar_concept tag / sort-prefix rules.
    gdir = root / cfg["grammar_dir"] if cfg.get("grammar_dir") else cfg["_lexicon"].parent / "Grammar_Structure"
    cfg["_grammar"] = gdir if gdir.is_dir() else None
    return cfg


def entry_search_dirs(cfg):
    """All dirs that hold entry notes: the lexicon plus the idioms dir."""
    dirs = [cfg["_lexicon"]]
    idi = cfg.get("_idioms")
    if idi and Path(idi).is_dir():
        dirs.append(idi)
    gr = cfg.get("_grammar")
    if gr and Path(gr).is_dir():
        dirs.append(gr)
    return dirs


def all_entry_files(cfg):
    """Every entry .md across all entry dirs."""
    files = []
    for d in entry_search_dirs(cfg):
        files.extend(d.glob("*.md"))
    return files


def dir_for_type(cfg, wtype):
    """Directory a NEW entry of this type should be written to."""
    if wtype == "idiom" and cfg.get("_idioms"):
        return cfg["_idioms"]
    return cfg["_lexicon"]


def entry_file(cfg, stem):
    """Path to entry <stem>.md in whichever entry dir holds it (defaults to the
    lexicon dir when it does not exist yet)."""
    for d in entry_search_dirs(cfg):
        pp = d / (stem + ".md")
        if pp.exists():
            return pp
    return cfg["_lexicon"] / (stem + ".md")


# ------------------------------------------------------------- phonology
# Romanization -> IPA, from "00_Phonemes of the Asaxi Language.md".
# Longest-match tokenization. Best-effort: output is a *suggestion*.

MULTIGRAPHS = [
    ("chx", "tʃʰ"), ("nŋ", "ŋ̍"),
    ("ch", "t̠ʃ"), ("dh", "ð"), ("jh", "d̠ʒ"), ("sh", "ʃ"), ("th", "θ"),
    ("zh", "ʑ"), ("dz", "d̻͡z̪"), ("nn", "n̩"), ("mm", "m̩"),
    ("px", "pʰ"), ("tx", "tʰ"), ("kx", "kʰ"),
]
SINGLE = {
    "b": "b", "c": "t̻͡s̪", "d": "d", "f": "f", "g": "ɡ", "h": "x", "x": "ɦ",
    "j": "j", "k": "k", "l": "l", "m": "m", "n": "n", "p": "p", "r": "ɹ",
    "s": "s", "t": "t", "v": "b̪v", "w": "ʋ", "z": "z̪",
    "ŋ": "ŋ", "ŕ": "ɾ", "ś": "ɕ", "ń": "ɲ", "'": "ʔ",
    "a": "a", "e": "e̞", "i": "i", "o": "o̞",
    "á": "ɑ", "ă": "aɪ", "å": "au̯", "è": "ə", "ë": "e̞ɪ", "ě": "ɚ",
    "ỏ": "ou̯", "ő": "o̞ɪ", "ù": "ɯ", "ů": "uw", "ý": "ɪ",
}
ALLOWED_CHARS = set("abcdefghijklmnoprstvwxz") | set("áăåèëěỏőùůýŋŕśń'.- ")
VOWEL_GRAPHEMES = set("aeioáăåèëěỏőùůý") | {"nn", "mm", "nŋ"}

# ---- Phonotactics (22_Phonotactics & Euphony) ----------------------------
PURE_V = {"a", "e", "i", "o", "ù"}
IMPURE_V = {"ý", "á", "è", "ů", "å", "ă", "ě", "ë", "ỏ", "ő"}
SYLLABIC = {"nn", "mm", "nŋ"}
ALL_V = PURE_V | IMPURE_V | SYLLABIC
PLOSIVES = {"p", "t", "k", "b", "d", "g"}
NASAL_CODAS = {"m", "n", "ŋ"}
R_CLUSTER_OK = {"ch", "jh", "k", "f", "p"}
GLIDES = {"w", "j"}


def check_phonotactics(word, wtype=None, root_noun=""):
    """Static word-level checks from 22_Phonotactics & Euphony.
    Returns (errors, warnings, info)."""
    errors, warnings, info = [], [], []
    toks = [t for t in tokenize(word) if t not in (".", "-", " ")]
    if not toks:
        return errors, warnings, info

    if not any(t in ALL_V for t in toks):
        errors.append("No vowel nucleus: every Asaxi word needs at least one vowel "
                      "or syllabic nasal (mm/nn/nŋ).")

    # a final glottal stop is a legal coda ONLY after a vowel (tomo', chěcho');
    # it never legalises what comes before it — strip it and judge the real coda.
    core_toks = list(toks)
    final_glottal = False
    while core_toks and core_toks[-1] == "'":
        core_toks.pop()
        final_glottal = True
    if not core_toks:
        return errors, warnings, info
    last = core_toks[-1]
    prev = core_toks[-2] if len(core_toks) > 1 else None
    if final_glottal and last not in ALL_V:
        errors.append(f"«{last}ʼ»: the glottal-stop coda may only follow a vowel "
                      "(22_Phonotactics: The Glottal Stop).")
    if last in PLOSIVES:
        errors.append(f"Forbidden coda: words may not end in the plosive «{last}» "
                      "(22_Phonotactics: Forbidden Codas)."
                      + (" A trailing ʼ does not make this legal." if final_glottal else ""))
    elif prev == "l" and last in ("v", "m"):
        errors.append(f"Forbidden coda cluster «l{last}» at word end "
                      "(22_Phonotactics: Complex Clusters).")
    elif last in ALL_V or last in NASAL_CODAS:
        pass
    elif last == "j" and prev == "ý":
        pass  # cold-class adjectival suffix -nýj
    elif not final_glottal:
        warnings.append(f"Unusual final «{last}»: Asaxi words normally end in a vowel, "
                        "syllabic/plain nasal, or ʼ (glottal stop).")

    for i, t in enumerate(toks):
        p_ = toks[i - 1] if i > 0 else None
        n_ = toks[i + 1] if i + 1 < len(toks) else None
        if t == "l" and p_ in IMPURE_V:
            errors.append(f"«{p_}l»: l may not follow an impure vowel "
                          "(22_Phonotactics: The l Rule).")
        if t == "r":
            if p_ is not None and p_ not in ALL_V and p_ != "'" and p_ not in R_CLUSTER_OK:
                errors.append(f"«{p_}r»: r clusters are only allowed after ch, jh, k, f, p "
                              "(22_Phonotactics: The r Rule).")
            if n_ == "i" and p_ != "f":
                errors.append("«ri»: r may never be followed by i (sole exception: fri).")
            if n_ in GLIDES or p_ in GLIDES:
                errors.append("r never appears with glides (w, j).")

    # noun→verb -n- bridge (Rule 22.A), advisory
    if wtype == "verb-u" and root_noun:
        rtoks = [t for t in tokenize(root_noun) if t not in (".", "-", " ")]
        if rtoks and rtoks[-1] in ALL_V and word != root_noun + "nů" and word.endswith("ů"):
            if word == root_noun + "ů":
                warnings.append(f"Rule 22.A: vowel-final noun + ů needs the -n- bridge: "
                                f"expected «{root_noun}nů».")
            else:
                info.append(f"Derivation check: {root_noun} + -ů would regularly give "
                            f"«{root_noun}nů» (n-bridge; haplology may alter this).")
    return errors, warnings, info



def check_charset(word: str):
    """Return list of characters not in the Asaxi romanization alphabet."""
    return sorted({ch for ch in word.lower() if ch not in ALLOWED_CHARS})


def tokenize(word: str):
    """Longest-match grapheme tokenization (lowercased, separators kept)."""
    w = word.lower()
    out, i = [], 0
    while i < len(w):
        for g, _ in MULTIGRAPHS:
            if w.startswith(g, i):
                # 'nn'/'mm' doubling vs gemination: keep simple longest-match
                out.append(g)
                i += len(g)
                break
        else:
            out.append(w[i])
            i += 1
    return out


def suggest_ipa(word: str) -> str:
    """Best-effort IPA from romanization, applying j/w modification rules."""
    toks = tokenize(word)
    ipa = []
    multi = dict(MULTIGRAPHS)
    for idx, t in enumerate(toks):
        if t in (".", "-", " ", "'"):
            ipa.append("." if t in (".", "-") else ("ʔ" if t == "'" else " "))
            continue
        nxt = toks[idx + 1] if idx + 1 < len(toks) else None
        prev_is_cons = idx > 0 and toks[idx - 1] not in VOWEL_GRAPHEMES and toks[idx - 1] not in (".", "-", " ")
        if t == "j" and prev_is_cons:
            ipa.append("ʲ")
            continue
        if t == "w" and prev_is_cons:
            ipa.append("ʷ")
            continue
        if t == "h" and nxt == "j":
            # hj -> /ç/ (consume next j at its turn via marker)
            ipa.append("ç")
            continue
        if t == "j" and idx > 0 and toks[idx - 1] == "h":
            continue  # consumed by hj rule
        seg = multi.get(t) or SINGLE.get(t)
        if seg is None:
            seg = t  # unknown, pass through
        # doubled consonant = geminate
        if ipa and seg and ipa[-1] == seg and t not in VOWEL_GRAPHEMES:
            ipa[-1] = seg + "ː"
            continue
        ipa.append(seg)
    return "/" + "".join(ipa) + "/"


# ------------------------------------------------------------ word types

# section builders below produce template-faithful markdown bodies.

WORD_TYPES = {
    "noun": {
        "label": "Noun",
        "suffix": "noun",
        "list": "01_Asaxi Nouns (List).md",
        "list_link": "01_Asaxi Nouns (List)",
        "tags": ["Asaxi", "language", "noun"],
    },
    "verb-root": {
        "label": "Verb (root)",
        "suffix": "verb",
        "list": "02_Asaxi Verbs_Root (List).md",
        "list_link": "02_Asaxi Verbs_Root (List)",
        "tags": ["Asaxi", "language", "verb"],
    },
    "verb-u": {
        "label": "Verb (-ů)",
        "suffix": "verb",
        "list": "02_Asaxi Verbs_ů (List).md",
        "list_link": "02_Asaxi Verbs_ů (List)",
        "tags": ["Asaxi", "language", "verb"],
    },
    "adjective": {
        "label": "Adjective",
        "suffix": "adjective",
        "list": "03_Asaxi Adjectives (List).md",
        "list_link": "03_Asaxi Adjectives (List)",
        "tags": ["Asaxi", "language", "adjective"],
    },
    "root-word": {
        "label": "Root word",
        "suffix": "root word",
        "list": "03_Asaxi Root Words (List).md",
        "list_link": "03_Asaxi Root Words (List)|root words",
        "tags": ["Asaxi", "language", "grammar"],
    },
    "ga-noun": {
        "label": "Ga-noun compound",
        "suffix": "noun",
        "list": "00_Ga-noun Compounds in Asaxi (list).md",
        "list_link": "00_Ga-noun Compounds in Asaxi (list)",
        "tags": ["Asaxi", "language", "noun", "ga-noun"],
    },
    "particle": {
        "label": "Particle",
        "suffix": "particle",
        "list": None,
        "list_link": "02_Particles in Asaxi",
        "tags": ["Asaxi", "language", "grammar"],
    },
    "number": {
        "label": "Number",
        "suffix": "Number",
        "list": "04_Asaxi Numbers (List).md",
        "list_link": "04_Asaxi Numbers (List)",
        "tags": ["Asaxi", "language", "number"],
    },
    "idiom": {
        "label": "Idiom / expression",
        "suffix": "Idiom",
        "list": None,
        "list_link": "45_Idioms & Fixed Expressions",
        "tags": ["Asaxi", "language", "idiom"],
    },
}

FIELD_SPECS = {
    # field key -> (label, required, applies-to types, kind)
    "word":        ("Asaxi word", True, "all", "text"),
    "gloss_en":    ("English translation(s)", True, "all", "text"),
    "gloss_pl":    ("Polish translation(s)", False, "all", "text"),
    "ipa":         ("IPA (auto-suggested if empty)", False, "all", "text"),
    "noun_class":  ("Noun class", False, ["noun", "ga-noun", "adjective"], "choice:Warm|Cold"),
    "animate":     ("Animate (adjectives)", False, ["adjective"], "choice:yes|no"),
    "transitivity": ("Transitivity", False, ["verb-root", "verb-u"], "choice:intransitive|monotransitive|ditransitive"),
    "lexical_aspect": ("Lexical aspect (root verbs)", False, ["verb-root"], "choice:Punctual (Achievement)|Durative (Activity)|State"),
    "semantic_fields": ("Semantic fields (wiki names)", False, "all", "list"),
    "example":     ("Example sentence (Asaxi)", False, "all", "text"),
    "example_gloss": ("Example translation/gloss", False, "all", "text"),
    "etymology":   ("Etymology", False, "all", "text"),
    "grammatical_function": ("Grammatical function", False, ["root-word", "particle"], "text"),
    "particle_type": ("Particle type", False, ["particle"], "text"),
    "alt_forms":   ("Alternative Forms", False, "all", "text"),
    "synonyms":    ("Synonyms (existing words)", False, "all", "list"),
    "antonyms":    ("Antonyms (existing words)", False, "all", "list"),
    "derived":     ("Derived terms", False, "all", "list"),
    "root_noun":   ("Root noun", False, ["adjective", "verb-u"], "text"),
    "number_value": ("Numeric value", False, ["number"], "text"),
    "usage_note":  ("Usage note (cultural context)", False, "all", "text"),
    "vocab_expansion_tag": ("Add vocab_expansion tag", False, "all", "bool"),
}


# ---------------------------------------------------------------- index

FILENAME_RE = re.compile(r"^(?P<word>.+?) \((?P<type>[^)]+)\)\.md$")


class Lexicon:
    def __init__(self, cfg):
        self.cfg = cfg
        self.entries = []  # dicts: word, type_raw, path, gloss_en, fields(list)
        self._load()

    def _load(self):
        paths = []
        for d in entry_search_dirs(self.cfg):
            paths.extend(sorted(d.glob("*.md")))
        for p in paths:
            m = FILENAME_RE.match(p.name)
            if not m:
                continue
            word = m.group("word")
            # skip list files, sort-prefixed morphemes (06A_-, Z_-), numbered docs
            if m.group("type").lower() in ("list",) or word[0].isdigit() or "_" in word:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                text = ""
            # skip grammar-concept documentation pages (not lexeme entries)
            if re.search(r"(?m)^\s*-\s*grammar_concept\s*$", text):
                continue
            e = {"word": word, "type_raw": m.group("type").lower(),
                 "path": str(p), "gloss_en": "", "gloss_pl": "", "fields": [],
                 "id": None}
            try:
                e["id"] = read_entry_id(text)
                e["freq"] = read_freq(text)
                fm = re.search(r"^trnsltion\. En:\s*(.+)$", text, re.M)
                if fm:
                    e["gloss_en"] = fm.group(1).strip()
                fp = re.search(r"^trnsltion\. Pl:\s*(.+)$", text, re.M)
                e["gloss_pl"] = fp.group(1).strip() if fp else ""
                au = field_audit(self.cfg, p.stem, text)
                e["audit"] = {"missing": au.get("missing_from_template") or [],
                              "nonstandard": au.get("nonstandard") or [],
                              "case": [f["from"] for f in (au.get("case_fixes") or [])]}
                sc = entry_score(text, e["audit"]["missing"])
                e["score"] = sc["pct"]
                e["score_filled"] = sc["filled"]
                e["score_total"] = sc["total"]
                e["fields"] = re.findall(r"\[\[(Smntc?_Field [^\]|]+)", text)
            except Exception:
                pass
            self.entries.append(e)

    def words(self):
        return {e["word"].lower() for e in self.entries}

    def find_exact(self, word):
        wl = word.lower()
        return [e for e in self.entries if e["word"].lower() == wl]

    def search(self, q, limit=12):
        ql = q.lower()
        starts, contains, glosses = [], [], []
        for e in self.entries:
            wl = e["word"].lower()
            if wl.startswith(ql):
                starts.append(e)
            elif ql in wl:
                contains.append(e)
            elif ql in e["gloss_en"].lower():
                glosses.append(e)
        out = (starts + contains + glosses)[:limit]
        return [{"word": e["word"], "type": e["type_raw"], "gloss": e["gloss_en"],
                 "short": short_gloss(e["gloss_en"]),
                 "link": f'{e["word"]} ({e["type_raw"]})'} for e in out]

    def near_duplicates(self, word, max_dist=1):
        wn = strip_marks(word.lower())
        out = []
        for e in self.entries:
            en = strip_marks(e["word"].lower())
            if abs(len(en) - len(wn)) > max_dist:
                continue
            d = levenshtein(wn, en, max_dist)
            if d is not None and d <= max_dist:
                out.append({"word": e["word"], "type": e["type_raw"],
                            "gloss": e["gloss_en"], "distance": d})
        return out

    def semantic_field_names(self):
        return sorted(p.stem for p in self.cfg["_fields"].glob("Smnt*_Field*.md"))


def strip_marks(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def levenshtein(a, b, cap):
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return None
        prev = cur
    return prev[-1]


# ------------------------------------------------------------ validation

def validate(lex: Lexicon, data: dict):
    """Return {"errors": [...], "warnings": [...], "info": [...], "ipa_suggestion": str}"""
    errors, warnings, info = [], [], []
    word = (data.get("word") or "").strip()
    wtype = data.get("type")
    if not word:
        errors.append("Word is empty.")
        return {"errors": errors, "warnings": warnings, "info": info, "ipa_suggestion": ""}
    if wtype not in WORD_TYPES:
        errors.append(f"Unknown word type: {wtype!r}. Valid: {', '.join(WORD_TYPES)}")
        return {"errors": errors, "warnings": warnings, "info": info, "ipa_suggestion": ""}

    if wtype != "idiom":
        bad = check_charset(word)
        if bad:
            errors.append("Characters outside the Asaxi romanization alphabet: "
                          + " ".join(repr(c) for c in bad))

    # exact duplicates
    for e in lex.find_exact(word):
        suffix = WORD_TYPES[wtype]["suffix"].lower()
        if e["type_raw"] == suffix:
            errors.append(f'"{word}" already exists as {e["type_raw"]}: {e["gloss_en"]}')
        else:
            warnings.append(f'"{word}" already exists as a different type '
                            f'({e["type_raw"]}: {e["gloss_en"]}). Allowed, but check intent.')

    # near duplicates
    near = [n for n in lex.near_duplicates(word) if n["word"].lower() != word.lower()]
    if near:
        tops = "; ".join(f'{n["word"]} ({n["type"]}: {n["gloss"]})' for n in near[:6])
        warnings.append(f"Similar existing words: {tops}")

    # homophones via IPA
    ipa = suggest_ipa(word)

    # phonotactics + single-word shape checks (skipped for multi-word idioms)
    if wtype != "idiom":
        ph_e, ph_w, ph_i = check_phonotactics(word, wtype, (data.get("root_noun") or "").strip())
        errors += ph_e
        warnings += ph_w
        info += ph_i
        if wtype == "verb-u" and not word.endswith("ů"):
            warnings.append("Verb (-ů) words normally end in ů.")
        if wtype == "verb-root" and word.endswith("ů"):
            warnings.append("Root verbs normally do NOT end in ů (that's the -ů class).")
        if wtype == "ga-noun" and not word.startswith("ga"):
            warnings.append("Ga-noun compounds normally start with ga-.")
    if not data.get("gloss_en"):
        warnings.append("English translation is empty.")

    # unknown semantic fields
    known_fields = set(lex.semantic_field_names())
    for f in data.get("semantic_fields") or []:
        if f not in known_fields:
            warnings.append(f'Semantic field "{f}" has no file in Semantic_Fields '
                            f"(link will be created but unresolved).")

    # synonyms/antonyms/root noun should exist
    existing = lex.words()
    for key in ("synonyms", "antonyms"):
        for w in data.get(key) or []:
            base = re.sub(r"\s*\([^)]*\)\s*$", "", w).strip()
            if base and base.lower() not in existing:
                info.append(f'{key[:-1].capitalize()} "{base}" is not in the lexicon yet.')

    return {"errors": errors, "warnings": warnings, "info": info, "ipa_suggestion": ipa}


# --------------------------------------------------------- entry builder

def _fm_escape(v):
    return v.replace('"', "'")


def link(word_type_name):
    return f"[[{word_type_name}]]"


def _lines_or(items, empty="x"):
    items = [i for i in (items or []) if i.strip()]
    if not items:
        return empty
    return "\n".join(f"- {i}" for i in items)


def _linkify_words(lex, items):
    """Turn plain word names into [[word (type)|word]] links when they exist."""
    out = []
    for raw in items or []:
        raw = raw.strip()
        if not raw:
            continue
        if raw.startswith("[["):
            out.append(raw)
            continue
        m = re.match(r"^(.*?)(?:\s*[-–—]\s*(.+))?$", raw)
        name, gloss = m.group(1).strip(), (m.group(2) or "").strip()
        matches = lex.find_exact(name)
        if matches:
            e = matches[0]
            l = f'[[{e["word"]} ({e["type_raw"]})|{e["word"]}]]'
            out.append(f"{l} ({gloss})" if gloss else f"{l} ({e['gloss_en']})" if e["gloss_en"] else l)
        else:
            out.append(f"{name} ({gloss})" if gloss else name)
    return out


def _field_links(fields):
    return " / ".join(f"[[{f}]]" for f in fields) if fields else "x"


def build_entry(lex: Lexicon, d: dict):
    """Return (filename, markdown) for the new entry, template-faithful."""
    t = WORD_TYPES[d["type"]]
    word = d["word"].strip()
    gl_en = (d.get("gloss_en") or "").strip()
    gl_pl = (d.get("gloss_pl") or "").strip()
    ipa = (d.get("ipa") or "").strip() or suggest_ipa(word)
    if not ipa.startswith("/"):
        ipa = f"/{ipa.strip('/')}/"
    fields = d.get("semantic_fields") or []
    ex = (d.get("example") or "").strip()
    exg = (d.get("example_gloss") or "").strip()
    example = "x"
    if ex:
        example = f"**{ex}**" + (f"\n_{exg}_" if exg else "")
    ety = (d.get("etymology") or "").strip() or "x"
    alt = (d.get("alt_forms") or "").strip() or "x"
    syn = _lines_or(_linkify_words(lex, d.get("synonyms")))
    ant = _lines_or(_linkify_words(lex, d.get("antonyms")), empty="Null")
    der = _lines_or(_linkify_words(lex, d.get("derived")), empty="Null")
    tags = list(t["tags"])
    if d.get("vocab_expansion_tag"):
        tags.append("vocab_expansion")
    if d["type"] == "ga-noun":
        _gk = (d.get("ga_kind") or "").strip().lower()
        if _gk.startswith("lit"):
            tags.append("ga-literal")
        elif _gk.startswith("idi"):
            tags.append("ga-idiomatic")
    tag_block = "\n".join(f"  - {x}" for x in tags)
    filename = f'{word} ({t["suffix"]}).md'
    title = f"{word} ({t['suffix']}) - {gl_en}" if gl_en else f"{word} ({t['suffix']})"
    head_link = f'# {word} ([[{t["list_link"]}]])' if t["list_link"] else f"# {word}"

    fm_pl = f"\ntrnsltion. Pl: {_fm_escape(gl_pl)}" if gl_pl or d["type"] not in ("root-word", "particle", "number") else ""
    trans_extra = ""
    fm_extra = ""
    if d["type"] in ("verb-root", "verb-u"):
        fm_extra = f"\nTransitivity: {d.get('transitivity') or ''}"

    _fr = d.get("freq")
    freq_val = None
    if _fr is not None and str(_fr).strip() != "":
        try:
            freq_val = max(1, min(100, int(float(_fr))))
        except (ValueError, TypeError):
            freq_val = None
    if freq_val is None:
        freq_val = wordfreq_rating(gl_en, gl_pl)   # auto-rate single-word glosses
    fm_freq = f"freq: {freq_val}\n" if freq_val else ""

    fm = (f"---\n{fm_freq}title: {_fm_escape(title)}\nWord (Asaxi): {word}\n"
          f"trnsltion. En: {_fm_escape(gl_en)}{fm_pl}{fm_extra}\ntags:\n{tag_block}\n---")

    script = (f'<span class="asaxi-script">{word}</span>\n\n'
              f'<span class="asaxi-script-alpha">{word}</span>')
    common_tail = (f"### Alternative Forms\n\n{alt}\n\n### Etymology\n\n{ety}\n\n"
                   f"### Synonyms\n\n{syn}\n\n### Antonyms\n\n{ant}\n\n"
                   f"### Derived terms\n\n{der}")
    trans_block = f"### Translations\n\n- English: {gl_en}\n- Polish: {gl_pl}"

    if d["type"] in ("noun", "ga-noun"):
        ncls = d.get("noun_class") or "x"
        ncls = f"**{ncls}**" if ncls in ("Warm", "Cold") else ncls
        if d["type"] == "ga-noun" and (d.get("etymology") or "").strip() == "":
            ety = f"[[ga (Fusing Particle)|ga]] + x"
            common_tail = (f"### Alternative Forms\n\n{alt}\n\n### Etymology\n\n{ety}\n\n"
                           f"### Synonyms\n\n{syn}\n\n### Antonyms\n\n{ant}\n\n"
                           f"### Derived terms\n\n{der}")
        body = (f"{head_link}\n\n- - -\n\n{script}\n\n"
                f"### Noun class (warm / cold)\n\n{ncls}\n\n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"### Semantic Field\n\n{_field_links(fields)}\n\n"
                f"{trans_block}\n\n"
                f"### Example sentence\n\n{example}\n\n{common_tail}")
    elif d["type"] in ("verb-root", "verb-u"):
        trs = d.get("transitivity") or "x"
        if d["type"] == "verb-root":
            asp = d.get("lexical_aspect") or "Punctual (Achievement)"
            aspect_block = (f"### Lexical Aspect\n\n- **{asp}**\n"
                            f"- **Aspect markers**: **na-** \"do repeatedly\" · **tå-** \"do once\" · "
                            f"**ni-** \"begin to\" · **chå-** \"do fully\" · **-ů** \"make it ongoing\" *(punctual roots)*.\n\n"
                            f"### Grammatical Note\n\n- **[[02_Asaxi Verbs_Root (List)]]:** Closed-class primitive verb, "
                            f"**punctual by default**. It may take **-ů** to derive a durative/processual reading, "
                            f"and `na-`/`tå-`/`ni-`/`chå-` for other aspects.")
            root_noun_block = ""
        else:
            aspect_block = (f"### Lexical Aspect\n\n- **Durative (Activity)** — `-ů` verbs unfold over time.\n"
                            f"- **Aspect markers**: **na-** \"do repeatedly\" · **tå-** \"do once\" · "
                            f"**ni-** \"begin to\" · **chå-** \"do fully\".")
            rn = (d.get("root_noun") or "").strip() or "x"
            rn_links = _linkify_words(lex, [rn]) if rn != "x" else ["x"]
            root_noun_block = f"\n\n### Root Noun\n\n- {rn_links[0]}"
        body = (f"{head_link}\n\n- - -\n\n{script}\n\n"
                f"### Transitivity / Valency\n\n_{trs} verb_\n\n"
                f"{aspect_block}\n\n"
                f"### Semantic Field\n\n{_field_links(fields)}\n\n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"{trans_block}\n\n"
                f"### Example sentence\n\n{example}\n\n"
                f"### Alternative Forms\n\n{alt}\n\n### Etymology\n\n{ety}\n\n"
                f"### Synonyms\n\n{syn}\n\n### Antonyms\n\n{ant}{root_noun_block}\n\n"
                f"### Derived terms\n\n{der}")
    elif d["type"] == "adjective":
        ncls = (d.get("noun_class") or "").lower() or "warm / cold"
        anim = d.get("animate") or "yes / not"
        rn = (d.get("root_noun") or "").strip() or "x"
        rn_links = _linkify_words(lex, [rn]) if rn != "x" else ["x"]
        body = (f"{head_link}\n\n- - -\n\n{script}\n\n"
                f"## Warm/Cold\n\nclass:\n- {ncls}\nanimate?\n- {anim}\nother class equivalent:\n- \n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"### Semantic Field\n\n{_field_links(fields)}\n\n"
                f"### Translations\n\n**As an adjective:**\n- English: {gl_en}\n- Polish: {gl_pl}\n\n"
                f"**As an adverb***:\n- English:\n- Polish:\n\n"
                f"### Example sentence:\n\n**As an adjective:**\n- {ex if ex else 'x'}"
                + (f"\n- _{exg}_" if exg else "") + "\n\n"
                f"### Alternative Forms\n\n{alt}\n\n### Etymology\n\n{ety}\n\n"
                f"### Synonyms\n\n{syn}\n\n### Root Noun\n\n- {rn_links[0]}\n\n### Antonyms\n\n{ant}")
    elif d["type"] == "root-word":
        gf = (d.get("grammatical_function") or "").strip() or f'Adds the "x" meaning to nouns it appears in'
        body = (f"{head_link}\n\n- - -\n\n{script}\n\n"
                f"### Grammatical function\n\n{gf}\n\n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"### Alternative Forms\n\n{alt}\n\n"
                f"### Antonyms\n\n{ant}\n\n"
                f"### Derived terms\n\n{der}")
    elif d["type"] == "particle":
        pt = (d.get("particle_type") or "").strip()
        gf = (d.get("grammatical_function") or "").strip()
        body = (f"# {word} ({gl_en or 'particle'})\n\n- - -\n\n{script}\n\n"
                f"### Grammatical function\n\n- Particle type: {pt}\n- Function: {gf}\n- Meaning: {gl_en}\n\n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"### Example sentence\n\n{example}\n\n"
                f"### Alternative Forms\n\n{alt}\n\n"
                f"### Antonyms\n\n{ant}\n\n"
                f"### Derived terms\n\n{der}")
    elif d["type"] == "number":
        nv = (d.get("number_value") or "").strip() or "x"
        body = (f"# {word} number ([[39_Numerals & Mathematics|Number]])\n\n- - -\n\n{script}\n\n"
                f'"{word}" stands for the number {nv}.\n\n'
                f"### Pronunciation\n\nIPA: {ipa}")
    elif d["type"] == "idiom":
        idx = (d.get("index_page") or "").strip() or t.get("list_link") or "45_Idioms & Fixed Expressions"
        gf = (d.get("grammatical_function") or "").strip() or "Fixed Expression"
        struct = (d.get("structure") or "").strip() or "x"
        body = (f"# {word} ([[{idx}]])\n\n- - -\n\n{script}\n\n"
                f"### Grammatical function\n\n- **Type:** {gf}\n- **Meaning:** {gl_en or 'x'}\n\n"
                f"### Structure\n\n{struct}\n\n"
                f"### Pronunciation\n\nIPA: {ipa}\n\n"
                f"### Example sentence\n\n{example}\n\n"
                f"### Etymology\n\n{ety}\n\n"
                f"### Synonyms\n\n{syn}\n\n"
                f"### Antonyms\n\n{ant}")
    else:
        raise ValueError(d["type"])

    usage = (d.get("usage_note") or "").strip()
    if usage:
        body += f"\n\n### Usage Note\n\n{usage}"

    return filename, fm + "\n" + body + "\n"


# ----------------------------------------------------------- list update

def list_line(d):
    t = WORD_TYPES[d["type"]]
    gloss = (d.get("gloss_en") or "").strip()
    return f'- [[{d["word"].strip()} ({t["suffix"]})]] - {gloss}' if gloss \
        else f'- [[{d["word"].strip()} ({t["suffix"]})]]'


NEW_ADDITIONS_HEADER = "### New additions (unsorted)"


def plan_list_update(lex: Lexicon, d: dict):
    """Plan updates: the type list file + each semantic field file.
    Returns list of {file, strategy, line, insert_after (line text) or None}."""
    plans = []
    t = WORD_TYPES[d["type"]]
    line = list_line(d)
    fields = set(d.get("semantic_fields") or [])

    if t["list"]:
        list_path = lex.cfg["_lexicon"] / t["list"]
        insert_after = None
        if fields and list_path.exists():
            # last list line whose word shares a semantic field with the new word
            by_word = {}
            for e in lex.entries:
                by_word.setdefault(e["word"].lower(), set()).update(e["fields"])
            for l in list_path.read_text(encoding="utf-8").splitlines():
                m = re.match(r"^- \[\[(.+?)(?: \([^)]*\))?(?:\|[^\]]*)?\]\]", l.strip())
                if m and by_word.get(m.group(1).lower(), set()) & fields:
                    insert_after = l
        plans.append({"file": str(list_path), "line": line,
                      "strategy": "after_semantic_sibling" if insert_after else "new_additions_section",
                      "insert_after": insert_after})

    for f in fields:
        fp = lex.cfg["_fields"] / f"{f}.md"
        if fp.exists():
            plans.append({"file": str(fp), "line": line, "strategy": "append_end",
                          "insert_after": None})
    return plans


def apply_list_update(plan):
    p = Path(plan["file"])
    if not p.exists():
        return f"SKIPPED (missing): {p.name}"
    text = p.read_text(encoding="utf-8")
    if plan["line"] in text:
        return f"SKIPPED (already listed): {p.name}"
    lines = text.splitlines()
    if plan["strategy"] == "after_semantic_sibling" and plan["insert_after"] in lines:
        idx = len(lines) - 1 - lines[::-1].index(plan["insert_after"])
        lines.insert(idx + 1, plan["line"])
    elif plan["strategy"] == "append_end":
        while lines and not lines[-1].strip():
            lines.pop()
        lines.append(plan["line"])
    else:  # new_additions_section
        if NEW_ADDITIONS_HEADER in lines:
            idx = lines.index(NEW_ADDITIONS_HEADER)
            end = idx + 1
            while end < len(lines) and (lines[end].startswith("- ") or not lines[end].strip()):
                end += 1
            while end > idx + 1 and not lines[end - 1].strip():
                end -= 1
            lines.insert(end, plan["line"])
        else:
            while lines and not lines[-1].strip():
                lines.pop()
            lines += ["", NEW_ADDITIONS_HEADER, "", plan["line"]]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"UPDATED: {p.name}"


# ----------------------------------------------------------------- API

def preview(lex: Lexicon, d: dict, force=False):
    v = validate(lex, d)
    if v["errors"] and not force:
        return {"ok": False, "validation": v}
    filename, md = build_entry(lex, d)
    plans = plan_list_update(lex, d) + plan_derived_updates(lex, d)
    return {"ok": True, "validation": v,
            "entry": {"filename": filename,
                      "path": str(dir_for_type(lex.cfg, d["type"]) / filename),
                      "markdown": md},
            "list_updates": plans}


def commit(lex: Lexicon, d: dict, force=False):
    pv = preview(lex, d, force=force)
    if not pv["ok"] and not force:
        return pv
    if not pv.get("entry"):
        return pv
    path = Path(pv["entry"]["path"])
    if path.exists():
        return {"ok": False, "validation": {"errors": [f"File already exists: {path.name}"],
                                            "warnings": [], "info": []}}
    path.write_text(pv["entry"]["markdown"], encoding="utf-8")
    results = []
    for pl in pv["list_updates"]:
        if pl["strategy"] == "derived_terms":
            results.append(apply_derived_update(pl, child_word=d["word"].strip()))
        else:
            results.append(apply_list_update(pl))
    pv["committed"] = True
    pv["list_results"] = results
    return pv


# ------------------------------------------------- thesaurus suggestions

_THES = None


def _load_thesaurus():
    global _THES
    if _THES is None:
        tp = TOOL_DIR / "thesaurus.json"
        _THES = json.loads(tp.read_text(encoding="utf-8")) if tp.exists() else {}
    return _THES


_WORD_RE = re.compile(r"[a-ząćęłńóśźż]+(?:[-'][a-ząćęłńóśźż]+)*", re.I)


def _gloss_tokens(gloss):
    g = re.sub(r"\([^)]*\)", " ", gloss or "")
    return {w.lower() for w in _WORD_RE.findall(g) if len(w) > 2}


def _expand(tokens, groups):
    """tokens -> (expansion set, {expanded_word: via_word})"""
    exp, via = set(), {}
    for grp in groups:
        gl = [g.lower() for g in grp]
        hit = tokens & set(gl)
        if hit:
            for g in gl:
                if g not in tokens:
                    exp.add(g)
                    via.setdefault(g, sorted(hit)[0])
    return exp, via


def _expand_antonyms(tokens, pairs):
    exp, via = set(), {}
    for a, b in pairs:
        al, bl = a.lower(), b.lower()
        if al in tokens:
            exp.add(bl); via.setdefault(bl, al)
        if bl in tokens:
            exp.add(al); via.setdefault(al, bl)
    return exp, via


def suggest_related(lex, d):
    """Thesaurus-driven synonym/antonym candidates from the existing corpus."""
    th = _load_thesaurus()
    tok_en = _gloss_tokens(d.get("gloss_en"))
    tok_pl = _gloss_tokens(d.get("gloss_pl"))
    syn_en, via_se = _expand(tok_en, th.get("synonyms_en", []))
    syn_pl, via_sp = _expand(tok_pl, th.get("synonyms_pl", []))
    ant_en, via_ae = _expand_antonyms(tok_en, th.get("antonyms_en", []))
    ant_pl, via_ap = _expand_antonyms(tok_pl, th.get("antonyms_pl", []))
    self_l = (d.get("word") or "").lower()
    syns, ants = [], []
    for e in lex.entries:
        if e["word"].lower() == self_l:
            continue
        ten = _gloss_tokens(e["gloss_en"])
        tpl = _gloss_tokens(e["gloss_pl"])
        rec = {"word": e["word"], "type": e["type_raw"], "gloss": e["gloss_en"]}
        # direct gloss overlap = strongest synonym signal
        d_en = ten & tok_en
        d_pl = tpl & tok_pl
        s_en = ten & syn_en
        s_pl = tpl & syn_pl
        if d_en or d_pl:
            syns.append({**rec, "via": f"shared gloss: {sorted(d_en or d_pl)[0]}"})
        elif s_en:
            w = sorted(s_en)[0]
            syns.append({**rec, "via": f"{via_se.get(w, w)} ≈ {w}"})
        elif s_pl:
            w = sorted(s_pl)[0]
            syns.append({**rec, "via": f"{via_sp.get(w, w)} ≈ {w} (pl)"})
        a_en = ten & ant_en
        a_pl = tpl & ant_pl
        if a_en:
            w = sorted(a_en)[0]
            ants.append({**rec, "via": f"{via_ae.get(w, w)} ↔ {w}"})
        elif a_pl:
            w = sorted(a_pl)[0]
            ants.append({**rec, "via": f"{via_ap.get(w, w)} ↔ {w} (pl)"})
    return {"synonyms": syns[:15], "antonyms": ants[:15]}


# --------------------------------------------- derived terms (etymology)

DERIVED_HEADER_RE = re.compile(r"^###\s+Derived [Tt]erms\s*$", re.M)
LINK_RE = re.compile(r"\[\[([^\]|#]+)")


def _section(text, header_re):
    m = header_re.search(text)
    if not m:
        return None, None
    start = m.end()
    nxt = re.search(r"^#{1,6}\s", text[start:], re.M)
    end = start + nxt.start() if nxt else len(text)
    return start, end


def _etymology_links(lex, text):
    """Lexicon entries referenced by [[links]] in the Etymology / Root Noun sections.
    Returns [(name, path, section)]."""
    out = []
    for section, hdr in (("etymology", re.compile(r"^###\s+Etymology\s*$", re.M)),
                         ("root_noun", re.compile(r"^###\s+Root Noun\s*$", re.M))):
        s, e = _section(text, hdr)
        if s is None:
            continue
        for name in LINK_RE.findall(text[s:e]):
            name = name.strip()
            fp = entry_file(lex.cfg, name)
            if fp.exists():
                out.append((name, fp, section))
    return out


def _is_derivational(base_name, child_word):
    """Heuristic: a link is a derivation source only if the base word is
    morphologically contained in the child (filters out 'contrasts with' links)."""
    base_word = re.sub(r"\s*\([^)]*\)\s*$", "", base_name).strip().lower()
    if len(base_word) < 2:
        return False  # single-grapheme affixes (ů, o...) would match everything
    return base_word in child_word.lower() and base_word != child_word.lower()


def derived_line(word, suffix, gloss):
    base = f"- [[{word} ({suffix})|{word}]]"
    return f"{base} - {gloss}" if gloss else base


def plan_derived_updates(lex, d):
    """When the new word's etymology/root noun references existing entries,
    plan adding it to their Derived terms sections."""
    plans = []
    t = WORD_TYPES[d["type"]]
    ety = d.get("etymology") or ""
    pseudo = f"### Etymology\n{ety}\n"
    rn = (d.get("root_noun") or "").strip()
    child = d["word"].strip()
    refs = {}
    for name, fp, section in _etymology_links(lex, pseudo):
        if _is_derivational(name, child):
            refs[name] = fp
    if rn:
        for e in lex.find_exact(rn):
            refs[f'{e["word"]} ({e["type_raw"]})'] = Path(e["path"])
    line = derived_line(d["word"].strip(), t["suffix"], (d.get("gloss_en") or "").strip())
    for name, fp in refs.items():
        if name.lower().startswith(d["word"].strip().lower() + " ("):
            continue  # self
        plans.append({"file": str(fp), "line": line, "strategy": "derived_terms",
                      "insert_after": None})
    return plans


def apply_derived_update(plan, child_word=None):
    p = Path(plan["file"])
    if not p.exists():
        return f"SKIPPED (missing): {p.name}"
    text = p.read_text(encoding="utf-8")
    word_key = child_word or plan["line"].split("[[")[1].split(" (")[0]
    s, e = _section(text, DERIVED_HEADER_RE)
    if s is None:
        text = text.rstrip() + f"\n\n### Derived terms\n\n{plan['line']}\n"
        p.write_text(text, encoding="utf-8")
        return f"UPDATED (new section): {p.name}"
    block = text[s:e]
    if f"[[{word_key} (" in block or f"[[{word_key}]]" in block or \
       re.search(r"(?<![\w])" + re.escape(word_key) + r"(?![\w])", block):
        return f"SKIPPED (already listed): {p.name}"
    stripped = block.strip()
    if stripped.lower() in ("null", "x", "-", "- x", "- null", ""):
        new_block = f"\n\n{plan['line']}\n"
        text = text[:s] + new_block + text[e:]
    else:
        insert = block.rstrip() + f"\n{plan['line']}\n"
        text = text[:s] + insert + text[e:]
    p.write_text(text, encoding="utf-8")
    return f"UPDATED: {p.name}"


def backfill_derived(lex):
    """Retroactive pass: every entry whose Etymology/Root Noun links to a base
    entry gets listed under that base's Derived terms. Returns plans."""
    plans = []
    for e in lex.entries:
        try:
            text = Path(e["path"]).read_text(encoding="utf-8")
        except Exception:
            continue
        gloss = e["gloss_en"]
        seen = set()
        for name, fp, section in _etymology_links(lex, text):
            if name.lower() == f'{e["word"].lower()} ({e["type_raw"]})':
                continue
            if (str(fp), e["word"]) in seen:
                continue
            if section == "etymology" and not _is_derivational(name, e["word"]):
                continue
            seen.add((str(fp), e["word"]))
            base_text = fp.read_text(encoding="utf-8")
            s2, e2 = _section(base_text, DERIVED_HEADER_RE)
            block = base_text[s2:e2] if s2 is not None else ""
            if f'[[{e["word"]} (' in block or \
               re.search(r"(?<![\w])" + re.escape(e["word"]) + r"(?![\w])", block):
                continue
            plans.append({"file": str(fp), "base": fp.stem,
                          "line": derived_line(e["word"], e["type_raw"], gloss),
                          "strategy": "derived_terms", "insert_after": None,
                          "child": e["word"]})
    return plans


# ------------------------------------------------------ vault note index

def all_note_names(cfg, q="", limit=20):
    """Vault-wide note stems for Obsidian-style [[link]] completion."""
    root = cfg["_root"]
    ql = q.lower()
    starts, contains = [], []
    for p in root.rglob("*.md"):
        sp = str(p)
        if ".obsidian" in sp or "99_Tools" in sp:
            continue
        stem = p.stem
        sl = stem.lower()
        if not ql or sl.startswith(ql):
            starts.append(stem)
        elif ql in sl:
            contains.append(stem)
        if len(starts) >= limit:
            break
    return (starts + contains)[:limit]


# --------------------------------------------- etymology builder support

def short_gloss(gloss):
    """First 1-2 senses of a gloss, cleaned: 'pain, sorrow, grief (felt)' -> 'Pain/Sorrow'."""
    g = re.sub(r"\([^)]*\)", " ", gloss or "")
    out = []
    for part in re.split(r"[,;·]| / ", g):
        part = re.sub(r"^[\s\"'`„“”‘’\-–—*_]+|[\s\"'`„“”‘’\-–—*_]+$", "", part)
        if not part:
            continue
        words = part.split()
        part = " ".join(w if w.isupper() else w[:1].upper() + w[1:] for w in words[:4])
        out.append(part)
        if len(out) == 2:
            break
    return "/".join(out)


def infix_inventory(cfg):
    """Morphological infixes mined from Grammar_Structure/06A_ notes."""
    gdir = cfg["_lexicon"].parent / "Grammar_Structure"
    out = []
    for p in sorted(gdir.glob("06A_*.md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        w = re.search(r"^Word \(Asaxi\):\s*(.+)$", text, re.M)
        g = re.search(r"^trnsltion\. En:\s*(.+)$", text, re.M)
        if w:
            out.append({"form": w.group(1).strip(),
                        "meaning": (g.group(1).strip() if g else ""),
                        "stem": p.stem})
    return out


# ---- morphological composition check (22_Phonotactics & Euphony rules) ----

_COAL = {"a": "ă", "e": "ë", "o": "ő", "è": "ë"}
_VOWELS_STR = "aeioùáăåèëěỏőůý"


def _join_pair(left, right):
    """All plausible fusions of two morphemes under the documented rules."""
    if not left:
        return {right}
    out = {left + right}
    lv, rv = left[-1], right[0] if right else ""
    # Rule 22.A: vowel-final noun + ů  ->  -n- bridge
    if right == "ů" and lv in _VOWELS_STR:
        out.add(left + "nů")
    # x-/w- epenthetic bridges (verb roots, locatives, ga-compounds)
    if lv in _VOWELS_STR and rv in _VOWELS_STR:
        out.add(left + "x" + right)
        out.add(left + "w" + right)
    # glide formation: ů + V -> w
    if lv == "ů" and rv in _VOWELS_STR:
        base = left[:-1] + "w"
        out.add(base + right)
        if right.startswith("ai"):
            out.add(base + "ă" + right[2:])  # fů+ai -> fwă
    # coalescence: prefix-final a/e/o/è + i- root -> diphthong
    if rv == "i" and lv in _COAL:
        out.add(left[:-1] + _COAL[lv] + right[1:])
    # haplology: identical adjacent morae reduce
    for k in (1, 2, 3):
        if len(left) >= k and len(right) > k and left[-k:] == right[:k]:
            out.add(left + right[k:])
    # haplology on a reduplicated left root: vivi+gavi -> vigavi
    if len(left) >= 4 and left[-2:] == left[-4:-2]:
        out.add(left[:-2] + right)
    return out


def _dissimilate(w):
    """Back-vowel + aa dissimilation: no+maka -> nomáka."""
    return re.sub(r"([eioùáåèëěỏőůý][^" + _VOWELS_STR + r"']*)a([^" + _VOWELS_STR + r"']+a)",
                  r"\1á\2", w)


def compose_check(word, parts):
    """Can `parts` (morphemes, hyphens allowed) compose into `word` under the rules?"""
    parts = [re.sub(r"^-+|-+$", "", (p or "").strip().lower()) for p in parts]
    parts = [p for p in parts if p]
    if not parts:
        return {"match": False, "candidates": 0, "closest": []}
    cands = {""}
    for part in parts:
        nxt = set()
        for left in cands:
            nxt |= _join_pair(left, part)
        cands = nxt
        if len(cands) > 4000:
            break
    cands |= {_dissimilate(w) for w in list(cands)}
    wl = (word or "").strip().lower()
    if wl in cands:
        return {"match": True, "candidates": len(cands), "closest": []}
    scored = sorted(cands, key=lambda c: (levenshtein(wl, c, 3) is None,
                                          levenshtein(wl, c, 3) or 9, len(c)))
    return {"match": False, "candidates": len(cands), "closest": scored[:3]}


# ----------------------------------------- entry scoring / browse / edit

EMPTY_VALUES = {"", "x", "null", "-", "- x", "- null", "//", "ipa: //", "n/a", "tbd", "?"}
SEC_RE = re.compile(r"(?m)^###\s+(.+?)\s*$")


def _filled(content):
    c = (content or "").strip()
    cl = c.lower().rstrip(".")
    if cl in EMPTY_VALUES:
        return False
    if re.fullmatch(r"ipa:\s*/?\s*/?", cl):
        return False
    return bool(c)


def split_sections(text):
    """All '### Header' sections with content and char spans."""
    out = []
    ms = list(SEC_RE.finditer(text))
    for i, m in enumerate(ms):
        start = m.end()
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        out.append({"header": m.group(1).strip(),
                    "content": text[start:end].strip("\n").rstrip(),
                    "span": (start, end)})
    return out


def entry_score(text, absent=()):
    """Completion: how many fields hold real content (not x/Null/empty).
    `absent` = template sections the entry lacks entirely — they count
    against the score too."""
    total, filled = 0, 0
    detail = []
    for key, label in (("trnsltion\. En", "English translation"),
                       ("trnsltion\. Pl", "Polish translation")):
        m = re.search(r"^" + key + r":\s*(.*)$", text, re.M)
        total += 1
        ok = bool(m and _filled(m.group(1)))
        filled += ok
        detail.append((label, ok))
    total += 1                              # frequency rating counts toward completion
    _fr_ok = read_freq(text) is not None
    filled += _fr_ok
    detail.append(("Frequency", _fr_ok))
    for s in split_sections(text):
        total += 1
        ok = _filled(s["content"])
        filled += ok
        detail.append((s["header"], ok))
    missing = [d[0] for d in detail if not d[1]]
    for h in absent:
        total += 1
        missing.append(f"{h} (absent)")
    pct = round(100 * filled / total) if total else 0
    return {"filled": filled, "total": total, "pct": pct, "missing": missing}


def _anki_index(cfg):
    """One directory scan -> {entry-id: {'image','a1','a2'}}.
    Filenames are <id>-asaxi-<word>-<slot>.<ext>; the id is the first token and
    the slot is read from the tail, so the cosmetic word never matters."""
    d = cfg["_root"] / "anki-assets"
    idx = {}
    if d.is_dir():
        for f in d.iterdir():
            if not f.is_file():
                continue
            m = re.match(r"^([A-Za-z0-9]+)-.*-(image|a1|a2)\.[A-Za-z0-9]+$", f.name)
            if m:
                idx.setdefault(m.group(1), set()).add(m.group(2))
    return idx


def browse(lex, q="", type_f="", field_f=""):
    """Filtered corpus listing with completion scores. Sorting is client-side."""
    ql = (q or "").lower()
    anki = _anki_index(lex.cfg)
    out = []
    for e in lex.entries:
        if type_f and e["type_raw"] != type_f:
            continue
        if field_f and field_f not in e["fields"]:
            continue
        if ql and ql not in e["word"].lower() and ql not in e["gloss_en"].lower() \
           and ql not in e.get("gloss_pl", "").lower():
            continue
        parts = anki.get(e.get("id"), set()) if e.get("id") else set()
        au = e.get("audit") or {"missing": [], "nonstandard": [], "case": []}
        out.append({"word": e["word"], "type": e["type_raw"], "audit": au,
                    "gloss": e["gloss_en"], "stem": Path(e["path"]).stem,
                    "freq": e.get("freq") or 0,
                    "score": e.get("score", 0), "filled": e.get("score_filled", 0),
                    "total": e.get("score_total", 0), "fields": e["fields"],
                    "anki": {"image": "image" in parts, "a1": "a1" in parts,
                             "a2": "a2" in parts, "n": len(parts)}})
    return out


def get_entry(cfg, name):
    """Load an entry for editing: frontmatter glosses + raw sections."""
    fp = entry_file(cfg, name)
    if not fp.exists():
        return {"ok": False, "error": f"No such entry: {name}"}
    text = fp.read_text(encoding="utf-8")
    def fmval(key):
        m = re.search(r"^" + key + r":\s*(.*)$", text, re.M)
        return m.group(1).strip() if m else None
    audit = field_audit(cfg, name, text)
    sc = entry_score(text, audit.get("missing_from_template") or [])
    return {"ok": True, "name": name, "audit": audit,
            "id": read_entry_id(text),
            "freq": read_freq(text),
            "ga_kind": ga_kind_of(text),
            "is_ga": "Ga-noun Compounds" in text,
            "gloss_en": fmval(r"trnsltion\. En") or "",
            "gloss_pl": fmval(r"trnsltion\. Pl"),
            "word_asaxi": fmval(r"Word \(Asaxi\)") or "",
            "sections": [{"header": s["header"], "content": s["content"]}
                         for s in split_sections(text)],
            "score": sc}


def _template_position_insert(cfg, name, text, hdr, block):
    """Insert a new section block at its template position (fallback: end)."""
    key = template_key_for(name, text)
    tpl = (_template_headers(cfg, key) or []) if key else []
    tpl = tpl + ["Usage Note"]  # convention: usage notes go last
    if hdr not in tpl:
        return text.rstrip() + "\n\n" + block + "\n"
    idx = tpl.index(hdr)
    secs = split_sections(text)
    # after the last existing section that precedes hdr in the template
    prev_end = None
    for s in secs:
        if s["header"] in tpl and tpl.index(s["header"]) < idx:
            prev_end = s["span"][1]
    if prev_end is not None:
        return text[:prev_end].rstrip() + "\n\n" + block + "\n\n" + text[prev_end:].lstrip("\n")
    # else before the first existing section that follows hdr in the template
    for s in secs:
        if s["header"] in tpl and tpl.index(s["header"]) > idx:
            hm = re.search(r"(?m)^###\s+" + re.escape(s["header"]) + r"\s*$", text)
            return text[:hm.start()].rstrip() + "\n\n" + block + "\n\n" + text[hm.start():]
    return text.rstrip() + "\n\n" + block + "\n"


def _reorder_sections(text, order):
    """Rebuild the section region of the note in the given header order."""
    ms = list(SEC_RE.finditer(text))
    if not ms:
        return text, "no sections"
    headers = [m.group(1).strip() for m in ms]
    if sorted(headers) != sorted(order):
        return text, "order list does not match the entry's sections"
    blocks = {}
    for i, m in enumerate(ms):
        end = ms[i + 1].start() if i + 1 < len(ms) else len(text)
        blocks.setdefault(m.group(1).strip(), text[m.start():end].rstrip())
    pre = text[:ms[0].start()].rstrip()
    return pre + "\n\n" + "\n\n".join(blocks[h] for h in order) + "\n", None


def update_entry(cfg, name, fm_updates=None, section_updates=None, dry_run=False,
                 order=None):
    """Surgical edit: replace only the given frontmatter values / section bodies.
    Unknown sections are appended at the end. Gloss changes sync list lines."""
    fp = entry_file(cfg, name)
    if not fp.exists():
        return {"ok": False, "error": f"No such entry: {name}"}
    text = fp.read_text(encoding="utf-8")
    changes = []

    _gk = (fm_updates or {}).get("ga_kind")
    if _gk:
        _tag = "ga-literal" if _gk.strip().lower().startswith("lit") else \
               ("ga-idiomatic" if _gk.strip().lower().startswith("idi") else None)
        if _tag:
            t2 = re.sub(r"(?m)^[ \t]*-[ \t]*ga-(?:literal|idiomatic)[ \t]*\n", "", text)
            if not re.search(r"(?m)^[ \t]*-[ \t]*" + _tag + r"[ \t]*$", t2):
                if re.search(r"(?m)^([ \t]*-[ \t]*ga-noun[ \t]*)$", t2):
                    t2 = re.sub(r"(?m)^([ \t]*-[ \t]*ga-noun[ \t]*)$", r"\1\n  - " + _tag, t2, count=1)
                else:
                    t2 = re.sub(r"(?s)^(---.*?\n)(---)", r"\1  - " + _tag + r"\n\2", t2, count=1)
            if t2 != text:
                text = t2
                changes.append("frontmatter: ga_kind")

    _freq = (fm_updates or {}).get("freq")
    if _freq is not None and str(_freq).strip() != "":
        try:
            nt = set_freq_text(text, int(float(_freq)))
            if nt != text:
                text = nt
                changes.append("frontmatter: freq")
        except (ValueError, TypeError):
            pass

    old_gloss = None
    for key, val in (fm_updates or {}).items():
        if key not in ("gloss_en", "gloss_pl"):
            continue
        fmkey = "trnsltion. En" if key == "gloss_en" else "trnsltion. Pl"
        pat = re.compile(r"^(" + re.escape(fmkey) + r":\s*)(.*)$", re.M)
        m = pat.search(text)
        if m:
            if m.group(2).strip() != val.strip():
                if key == "gloss_en":
                    old_gloss = m.group(2).strip()
                text = pat.sub(lambda mm: mm.group(1) + val, text, count=1)
                changes.append(f"frontmatter: {fmkey}")
        elif val.strip():
            # insert after the En line (or after Word line)
            anchor = re.search(r"^trnsltion\. En:.*$", text, re.M)
            if anchor:
                text = text[:anchor.end()] + f"\n{fmkey}: {val}" + text[anchor.end():]
                changes.append(f"frontmatter: {fmkey} (added)")
        if key == "gloss_en" and old_gloss is not None:
            # title line carries the gloss too
            tpat = re.compile(r"^(title:\s*.+? - ).*$", re.M)
            if tpat.search(text):
                text = tpat.sub(lambda mm: mm.group(1) + val, text, count=1)

    for upd in (section_updates or []):
        hdr = upd["header"].strip()
        secs = split_sections(text)
        hit = next((s for s in secs if s["header"] == hdr), None)
        if upd.get("rename_to"):
            new_hdr = upd["rename_to"].strip()
            if hit and new_hdr and new_hdr != hdr:
                if any(s["header"] == new_hdr for s in secs):
                    changes.append(f"rename skipped (target exists): {hdr}")
                    continue
                hm = re.search(r"(?m)^(###\s+)" + re.escape(hdr) + r"(\s*)$", text)
                text = text[:hm.start()] + hm.group(1) + new_hdr + text[hm.end():]
                changes.append(f"section renamed: {hdr} → {new_hdr}")
            continue
        if upd.get("delete"):
            if hit:
                hm = re.search(r"(?m)^###\s+" + re.escape(hdr) + r"\s*$", text)
                start = hm.start()
                text = text[:start].rstrip() + "\n\n" + text[hit["span"][1]:].lstrip("\n")
                text = text.rstrip() + "\n"
                changes.append(f"section deleted: {hdr}")
            continue
        new_content = upd["content"].rstrip()
        if hit:
            if hit["content"].strip() == new_content.strip():
                continue
            s, e = hit["span"]
            text = text[:s] + "\n\n" + new_content + "\n\n" + text[e:] \
                if e < len(text) else text[:s] + "\n\n" + new_content + "\n"
            changes.append(f"section: {hdr}")
        elif new_content.strip():
            text = _template_position_insert(cfg, name, text,
                                             hdr, f"### {hdr}\n\n{new_content}")
            changes.append(f"section: {hdr} (added)")

    if order:
        current = [s["header"] for s in split_sections(text)]
        if current != list(order):
            text2, err = _reorder_sections(text, list(order))
            if err:
                changes.append(f"reorder skipped: {err}")
            else:
                text = text2
                changes.append("sections reordered")

    list_syncs = []
    if old_gloss is not None and fm_updates.get("gloss_en", "").strip():
        new_gloss = fm_updates["gloss_en"].strip()
        line_pat = re.compile(r"^(-\s*\[\[" + re.escape(name) +
                              r"(?:\|[^\]]*)?\]\]\s*-\s*).*$", re.M)
        targets = all_entry_files(cfg) + list(cfg["_fields"].glob("*.md"))
        for lf in targets:
            if lf.name == f"{name}.md":
                continue
            lt = lf.read_text(encoding="utf-8")
            if f"[[{name}" not in lt:
                continue
            nt = line_pat.sub(lambda mm: mm.group(1) + new_gloss, lt)
            if nt != lt:
                if not dry_run:
                    lf.write_text(nt, encoding="utf-8")
                list_syncs.append(lf.name)

    def _score(t):
        au = field_audit(cfg, name, t)
        return entry_score(t, au.get("missing_from_template") or [])

    if not changes and not list_syncs:
        return {"ok": True, "changed": [], "list_synced": [], "text": text,
                "score": _score(text), "note": "nothing to change"}
    if not dry_run:
        fp.write_text(text, encoding="utf-8")
    return {"ok": True, "changed": changes, "list_synced": list_syncs,
            "score": _score(text), "text": text}


# --------------------------------------------- link check / anki / delete

def check_links(cfg, names):
    """{link target -> exists?} against every note stem in the vault."""
    stems = set()
    for q in cfg["_root"].rglob("*.md"):
        sq = str(q)
        if ".obsidian" in sq or "99_Tools" in sq:
            continue
        stems.add(q.stem)
    out = {}
    for n in names:
        base = n.split("|")[0].split("#")[0].strip()
        out[n] = base in stems
    return out


# --------------------------------------------- stable entry IDs
# Each entry gets a permanent, filename-safe id the FIRST time an Anki asset is
# attached to it (see ensure_entry_id). Assets are named  <id>-asaxi-<word>-<slot>.<ext>
# so the link survives renaming the word / the entry file. The id lives in the
# entry's front matter as  `id: <id>`  and never changes once assigned.

ID_PREFIX = "ax"                       # marks these as Asaxi vocab ids; guarantees non-numeric
ID_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
ID_BODY_LEN = 7                        # 36**7 ~ 78 billion, plus an explicit collision check
_ID_RE = re.compile(r"(?m)^id:[ \t]*([A-Za-z0-9][A-Za-z0-9_-]*)[ \t]*$")
SLOTS = ("image", "a1", "a2")


def read_entry_id(text):
    """The `id:` value from an entry's front matter, or None."""
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _gen_id():
    import secrets
    return ID_PREFIX + "".join(secrets.choice(ID_ALPHABET) for _ in range(ID_BODY_LEN))


def entry_ids_in_use(cfg):
    """Every id currently claimed anywhere - front matter and asset filenames -
    so a freshly minted id can never collide."""
    used = set()
    for p in all_entry_files(cfg):
        try:
            i = read_entry_id(p.read_text(encoding="utf-8"))
            if i:
                used.add(i)
        except Exception:
            pass
    d = cfg["_root"] / "anki-assets"
    if d.is_dir():
        for f in d.iterdir():
            if f.is_file() and "-" in f.name:
                used.add(f.name.split("-", 1)[0])
    return used


def new_unique_id(cfg):
    used = entry_ids_in_use(cfg)
    while True:
        i = _gen_id()
        if i not in used:
            return i


def _insert_entry_id(text, idval):
    """Put `id: <idval>` as the first key inside the opening front-matter block.
    If the note has no front matter, create a minimal one."""
    m = re.match(r"^---[ \t]*\r?\n", text)
    if m:
        return text[:m.end()] + f"id: {idval}\n" + text[m.end():]
    return f"---\nid: {idval}\n---\n\n" + text


def word_from_stem(stem):
    """'ai (noun)' -> 'ai'  (strip the trailing ' (type)')."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", stem).strip()


def resolve_entry(cfg, name="", word=""):
    """Locate an entry file. Prefer an explicit stem ('ai (noun)'); otherwise
    look it up by headword. Returns {'ok', 'stem'} or an error (assets can only
    attach to a SAVED entry, since the id lives in its front matter)."""
    name = (name or "").strip()
    word = (word or "").strip()
    dirs = entry_search_dirs(cfg)
    if name:
        if any((d / f"{name}.md").exists() for d in dirs):
            return {"ok": True, "stem": name}
        return {"ok": False, "error": f"No such entry: {name}"}
    if word:
        hits = sorted({p.stem for d in dirs for p in d.glob("*.md")
                       if word_from_stem(p.stem).lower() == word.lower()})
        if not hits:
            return {"ok": False,
                    "error": f"No saved entry for '{word}' - "
                             "save the entry first, then attach assets from the Edit tab."}
        if len(hits) > 1:
            return {"ok": False, "stems": sorted(hits),
                    "error": "Several entries share this word - open the one you "
                             "want from the Edit tab so the right file gets the asset."}
        return {"ok": True, "stem": hits[0]}
    return {"ok": False, "error": "no entry specified"}


def ensure_entry_id(cfg, stem):
    """Return the entry's id, minting + writing one into its front matter the
    first time (this is the ONLY place an id is created)."""
    fp = entry_file(cfg, stem)
    if not fp.exists():
        return {"ok": False, "error": f"No such entry: {stem}"}
    text = fp.read_text(encoding="utf-8")
    cur = read_entry_id(text)
    if cur:
        return {"ok": True, "id": cur, "stem": stem, "created": False}
    idval = new_unique_id(cfg)
    fp.write_text(_insert_entry_id(text, idval), encoding="utf-8")
    return {"ok": True, "id": idval, "stem": stem, "created": True}


# --------------------------------------------- anki assets (keyed by entry id)

def anki_dir(cfg):
    d = cfg["_root"] / "anki-assets"
    d.mkdir(exist_ok=True)
    return d


def safe_word(word):
    return re.sub(r"[\\/:*?\"<>|]", "", (word or "").strip())


def asset_name(idval, word, slot, ext):
    """<id>-asaxi-<word>-<slot>.<ext>  (word is cosmetic; matching is by id+slot)."""
    ext = (ext or "").lstrip(".") or "bin"
    return f"{idval}-asaxi-{safe_word(word)}-{slot}.{ext}"


def _assets_for_id(cfg, idval):
    """{slot: filename} present on disk for an id (ignores the cosmetic word)."""
    out = {s: None for s in SLOTS}
    if not idval:
        return out
    d = anki_dir(cfg)
    for slot in SLOTS:
        hits = sorted(d.glob(f"{idval}-*-{slot}.*"))
        if hits:
            out[slot] = hits[0].name
    return out


def anki_status(cfg, name="", word=""):
    """Asset presence for an entry, looked up by its stable id."""
    r = resolve_entry(cfg, name=name, word=word)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "stems": r.get("stems"),
                "id": None, "image": None, "a1": None, "a2": None}
    stem = r["stem"]
    idval = read_entry_id((entry_file(cfg, stem)).read_text(encoding="utf-8"))
    return {"ok": True, "stem": stem, "id": idval, **_assets_for_id(cfg, idval)}


def save_asset(cfg, name="", word="", slot="", ext="", data=b""):
    """Attach an asset to an entry. Mints the entry's id if it doesn't have one
    yet, then writes  <id>-asaxi-<word>-<slot>.<ext>  (replacing any prior file in
    that id+slot, even if the word has since changed)."""
    if slot not in SLOTS:
        return {"ok": False, "error": f"bad slot: {slot!r} (expected one of {SLOTS})"}
    r = resolve_entry(cfg, name=name, word=word)
    if not r.get("ok"):
        return {"ok": False, "error": r.get("error"), "stems": r.get("stems")}
    stem = r["stem"]
    idr = ensure_entry_id(cfg, stem)
    if not idr.get("ok"):
        return idr
    idval = idr["id"]
    hw = word_from_stem(stem)          # always name after the current headword
    d = anki_dir(cfg)
    for old in d.glob(f"{idval}-*-{slot}.*"):   # one file per id+slot
        old.unlink()
    fname = asset_name(idval, hw, slot, ext)
    (d / fname).write_bytes(data)
    return {"ok": True, "saved": fname, "bytes": len(data),
            "id": idval, "id_created": idr["created"], "stem": stem}


def delete_asset(cfg, filename):
    """Remove one asset slot (any extension of the same stem). The entry keeps
    its id, so re-adding an asset reuses the same stable id."""
    filename = re.sub(r"[\\/:*?\"<>|]", "", filename)
    if not re.match(r"^[A-Za-z0-9]+-asaxi-.*-(?:image|a1|a2)\.[A-Za-z0-9]+$", filename):
        return {"ok": False, "error": "not a recognized anki asset filename"}
    stem = filename.rsplit(".", 1)[0]
    removed = []
    for f in anki_dir(cfg).glob(stem + ".*"):
        f.unlink()
        removed.append(f.name)
    return {"ok": True, "removed": removed}


def delete_entry(cfg, name, dry_run=True):
    """Delete an entry file and scrub its '- [[name...]]' lines from list and
    semantic-field files. Other inline links are left (they'll show as broken)."""
    fp = entry_file(cfg, name)
    if not fp.exists():
        return {"ok": False, "error": f"No such entry: {name}"}
    line_pat = re.compile(r"^[ \t]*-\s*\[\[" + re.escape(name) +
                          r"(?:\|[^\]]*)?\]\].*$\n?", re.M)
    scrubbed = []
    targets = all_entry_files(cfg) + list(cfg["_fields"].glob("*.md"))
    for lf in targets:
        if lf.name == f"{name}.md":
            continue
        lt = lf.read_text(encoding="utf-8")
        nt, n = line_pat.subn("", lt)
        if n:
            scrubbed.append(f"{lf.name} ({n} line{'s' if n>1 else ''})")
            if not dry_run:
                lf.write_text(nt, encoding="utf-8")
    refs = []
    for q in all_entry_files(cfg):
        if q.name != f"{name}.md" and f"[[{name}" in q.read_text(encoding="utf-8"):
            refs.append(q.stem)
    if not dry_run:
        fp.unlink()
    return {"ok": True, "deleted": name, "dry_run": dry_run,
            "list_lines_removed": scrubbed,
            "remaining_references": refs[:20]}



def _vault_note_files(cfg):
    """Every .md in the vault except the tool/obsidian dirs (vault-wide link ops)."""
    out = []
    for q in cfg["_root"].rglob("*.md"):
        sq = str(q)
        if ".obsidian" in sq or "99_Tools" in sq:
            continue
        out.append(q)
    return out


_STEM_RE = re.compile(r"^(?P<word>.+?) \((?P<type>[^)]+)\)$")


def rename_entry(cfg, old_name, new_name, dry_run=True):
    """Rename an entry file and repoint every [[backlink]] to it across the vault
    (Obsidian-style), keeping the note itself consistent. Always dry_run first."""
    old_name = (old_name or "").strip()
    new_name = (new_name or "").strip()
    if not new_name:
        return {"ok": False, "error": "New name is empty."}
    if re.search(r'[\\/:*?"<>|]', new_name):
        return {"ok": False, "error": "New name has an illegal filename character."}
    old_fp = entry_file(cfg, old_name)
    if not old_fp.exists():
        return {"ok": False, "error": f"No such entry: {old_name}"}
    if new_name == old_name:
        return {"ok": False, "error": "New name is the same as the current name."}
    mn = _STEM_RE.match(new_name)
    if not mn:
        return {"ok": False, "error": "New name must look like  word (type)  - e.g. 'ai (noun)'."}
    mo = _STEM_RE.match(old_name)
    old_word = mo.group("word") if mo else old_name
    new_word = mn.group("word")
    for d in entry_search_dirs(cfg) + [cfg["_fields"]]:
        if (d / f"{new_name}.md").exists():
            return {"ok": False, "error": f"A note named '{new_name}' already exists."}
    new_fp = old_fp.parent / f"{new_name}.md"
    word_changed = old_word != new_word

    esc_old = re.escape(old_name)
    link_re = re.compile(r"\[\[" + esc_old + r"(#[^\]|]+)?(\|[^\]]+)?\]\]")

    def rewrite(m):
        heading = m.group(1) or ""
        alias = m.group(2)
        if alias is not None:
            atext = alias[1:]
            if word_changed and atext == old_word:
                atext = new_word
            newalias = "|" + atext
        else:
            newalias = ""
        return f"[[{new_name}{heading}{newalias}]]"

    text = old_fp.read_text(encoding="utf-8")
    self_edits = []
    tpat = re.compile(r"^(title:[ \t]*)" + esc_old + r"(.*)$", re.M)
    if tpat.search(text):
        text = tpat.sub(lambda m: m.group(1) + new_name + m.group(2), text, count=1)
        self_edits.append("title")
    if word_changed:
        wpat = re.compile(r"^(Word \(Asaxi\):[ \t]*)" + re.escape(old_word) + r"[ \t]*$", re.M)
        if wpat.search(text):
            text = wpat.sub(lambda m: m.group(1) + new_word, text, count=1)
            self_edits.append("Word (Asaxi)")
        hpat = re.compile(r"^(#[ \t]+)" + re.escape(old_word) + r"(?=[ (\n])", re.M)
        if hpat.search(text):
            text = hpat.sub(lambda m: m.group(1) + new_word, text, count=1)
            self_edits.append("heading")
        for cls in ("asaxi-script", "asaxi-script-alpha"):
            spat = re.compile(r'(<span class="' + cls + r'">)' + re.escape(old_word) + r"(</span>)")
            if spat.search(text):
                text = spat.sub(lambda m: m.group(1) + new_word + m.group(2), text)
                self_edits.append(cls + " span")
    text = link_re.sub(rewrite, text)

    backlinks = []
    total = 0
    for q in _vault_note_files(cfg):
        if q.resolve() == old_fp.resolve():
            continue
        qt = q.read_text(encoding="utf-8")
        if "[[" + old_name not in qt:
            continue
        nt, n = link_re.subn(rewrite, qt)
        if n:
            backlinks.append({"file": str(q.relative_to(cfg["_root"])), "count": n})
            total += n
            if not dry_run:
                q.write_text(nt, encoding="utf-8")

    if not dry_run:
        new_fp.write_text(text, encoding="utf-8")
        old_fp.unlink()

    return {"ok": True, "dry_run": dry_run, "old_name": old_name, "new_name": new_name,
            "dir": old_fp.parent.name, "self_edits": self_edits,
            "backlink_files": backlinks[:200], "backlink_file_count": len(backlinks),
            "backlink_edit_count": total, "id": read_entry_id(text)}



# ------------------------------------ list files (fill + Latin-alphabetical sort)

_LIST_CATEGORIES = {
    "noun": "01_Asaxi Nouns (List)",
    "verb-root": "02_Asaxi Verbs_Root (List)",
    "verb-u": "02_Asaxi Verbs_ů (List)",
    "adjective": "03_Asaxi Adjectives (List)",
    "root word": "03_Asaxi Root Words (List)",
    "number": "04_Asaxi Numbers (List)",
}
_VOCAB_LINE_RE = re.compile(
    r"(?im)^[ \t]*-[ \t]*\[\[[^\]|#]*\((?:noun|verb|adjective|root word|particle|number|idiom)\)"
    r"(?:#[^\]|]*)?(?:\|[^\]]*)?\]\].*\n?")


def list_sort_key(word):
    """Latin-alphabetical key: fold Asaxi diacritics onto their base letter."""
    w = (word or "").lower().replace("ŋ", "ng").replace("'", "")
    w = unicodedata.normalize("NFD", w)
    w = "".join(c for c in w if not unicodedata.combining(c))
    return (w, (word or "").lower())


def ga_kind_of(text):
    """'Literal' / 'Idiomatic' from a ga-noun's tags, else None."""
    if re.search(r"(?m)^[ \t]*-[ \t]*ga-literal[ \t]*$", text):
        return "Literal"
    if re.search(r"(?m)^[ \t]*-[ \t]*ga-idiomatic[ \t]*$", text):
        return "Idiomatic"
    return None


def _list_line(stem, gloss):
    return f"- [[{stem}]] - {gloss}" if (gloss or "").strip() else f"- [[{stem}]]"


def _preamble(text):
    return re.sub(r"\n{3,}", "\n\n", text).strip("\n")


def rebuild_lists(cfg, dry_run=False):
    """Fill each category List with every entry of that category, Latin-sorted,
    preserving the file's frontmatter/prose/nav. The ga-noun list is grouped by
    the ga-literal / ga-idiomatic tag. Idempotent / re-runnable."""
    from collections import defaultdict
    lex = Lexicon(cfg)
    cat = defaultdict(list)
    ga = {"Literal": [], "Idiomatic": [], None: []}
    for e in lex.entries:
        stem = Path(e["path"]).stem
        text = Path(e["path"]).read_text(encoding="utf-8")
        key = template_key_for(stem, text)
        rec = (stem, e["word"], e.get("gloss_en", ""))
        if key == "ga-noun":
            ga[ga_kind_of(text)].append(rec)
        elif key in _LIST_CATEGORIES:
            cat[key].append(rec)

    lexdir = cfg["_lexicon"]
    report = []
    for key, lname in _LIST_CATEGORIES.items():
        fp = lexdir / f"{lname}.md"
        if not fp.exists():
            report.append({"list": lname, "error": "missing"})
            continue
        text = fp.read_text(encoding="utf-8")
        was = len(_VOCAB_LINE_RE.findall(text))
        skeleton = _preamble(_VOCAB_LINE_RE.sub("", text))
        recs = sorted(cat.get(key, []), key=lambda r: list_sort_key(r[1]))
        body = "\n".join(_list_line(s, g) for s, w, g in recs)
        newtext = (skeleton + "\n\n" + body + "\n") if skeleton else (body + "\n")
        if not dry_run:
            fp.write_text(newtext, encoding="utf-8")
        report.append({"list": lname, "category": key, "was": was, "now": len(recs)})

    gname = WORD_TYPES["ga-noun"]["list"]
    gfp = lexdir / gname
    if gfp.exists():
        gtext = gfp.read_text(encoding="utf-8")
        mfirst = re.search(r"(?m)^###[ \t]+", gtext)
        pre = _preamble(gtext[:mfirst.start()]) if mfirst else _preamble(gtext)
        hlit = re.search(r"(?m)^###[ \t]+(.*[Ll]iteral.*)$", gtext)
        hidi = re.search(r"(?m)^###[ \t]+(.*[Ii]diomatic.*)$", gtext)
        lit_hdr = hlit.group(1).strip() if hlit else "Literal Ga-noun Compounds in Asaxi"
        idi_hdr = hidi.group(1).strip() if hidi else "Idiomatic Ga-noun Compounds in Asaxi"
        lit = sorted(ga["Literal"], key=lambda r: list_sort_key(r[1]))
        idi = sorted(ga["Idiomatic"] + ga[None], key=lambda r: list_sort_key(r[1]))
        gbody = (pre + "\n\n"
                 + f"### {lit_hdr}\n" + "\n".join(_list_line(s, g) for s, w, g in lit) + "\n\n"
                 + "- - -\n\n"
                 + f"### {idi_hdr}\n" + "\n".join(_list_line(s, g) for s, w, g in idi) + "\n")
        if not dry_run:
            gfp.write_text(gbody, encoding="utf-8")
        report.append({"list": gname[:-3], "category": "ga-noun",
                       "literal": len(lit), "idiomatic": len(idi), "untagged": len(ga[None])})
    return {"ok": True, "dry_run": dry_run, "report": report}



# ------------------------------------ frequency ratings (1-100)
# Higher = more frequent -> sorts to the top of the Anki deck. Stored per entry
# as `freq:` in front matter (hand-editable). Fallback chain (see effective_freq):
#   stored freq:  ->  wordfreq of a single-word gloss  ->  0 (end of deck).

# Core cross-linguistic vocabulary (Swadesh / Leipzig-Jakarta, bare English forms).
# Any single-word gloss matching this set is floored near the top.
CORE_MEANINGS = {
    "i", "you", "we", "he", "she", "they", "this", "that", "who", "what", "not",
    "all", "many", "some", "few", "other", "one", "two", "three", "four", "five",
    "big", "long", "wide", "thick", "heavy", "small", "short", "narrow", "thin",
    "good", "bad", "new", "old", "cold", "warm", "hot", "full", "round", "dry",
    "wet", "far", "near", "right", "left", "black", "white", "red", "green",
    "yellow", "blue", "name", "water", "fire", "sun", "moon", "star", "sky",
    "wind", "rain", "cloud", "smoke", "ash", "snow", "ice", "stone", "sand",
    "earth", "ground", "soil", "dust", "mountain", "sea", "lake", "river",
    "road", "path", "salt", "night", "day", "year", "tree", "leaf", "root",
    "bark", "seed", "flower", "grass", "fruit", "skin", "flesh", "meat", "blood",
    "bone", "fat", "egg", "horn", "tail", "feather", "hair", "head", "ear",
    "eye", "nose", "mouth", "tooth", "tongue", "claw", "nail", "foot", "leg",
    "knee", "hand", "arm", "wing", "belly", "guts", "neck", "back", "breast",
    "heart", "liver", "man", "woman", "person", "child", "husband", "wife",
    "mother", "father", "animal", "fish", "bird", "dog", "louse", "snake",
    "worm", "drink", "eat", "bite", "chew", "suck", "spit", "vomit", "blow",
    "breathe", "laugh", "see", "hear", "know", "think", "smell", "fear",
    "sleep", "live", "die", "kill", "fight", "hunt", "hit", "cut", "split",
    "stab", "scratch", "dig", "swim", "fly", "walk", "come", "go", "lie",
    "sit", "stand", "turn", "fall", "give", "hold", "squeeze", "rub", "wash",
    "wipe", "pull", "push", "throw", "tie", "sew", "count", "say", "speak",
    "sing", "play", "float", "flow", "freeze", "swell", "run", "burn", "cook",
    "work", "want", "love", "hate", "make", "do", "take", "find", "grow",
    "buy", "sell", "help", "learn", "teach", "read", "write", "yes", "no",
    "here", "there", "now", "then", "today", "sun", "hello", "goodbye",
    "thanks", "please", "sorry", "food", "house", "home", "friend", "enemy",
    "king", "god", "money", "time", "word", "true", "empty", "clean", "dirty",
    "sharp", "dull", "smooth", "wet", "heavy", "young", "many", "big",
}

_FREQ_RE = re.compile(r"(?m)^freq:[ \t]*(\d{1,3})[ \t]*$")


def _wordfreq_ok():
    try:
        import wordfreq  # noqa: F401
        return True
    except Exception:
        return False


def _gloss_head(gloss):
    """First single English/Polish word of a gloss, or None for a multiword gloss.
    Takes the first synonym, drops parentheticals and a leading 'to '/article."""
    if not gloss:
        return None
    seg = re.split(r"[;,/]", gloss.strip())[0]
    seg = re.sub(r"\([^)]*\)", "", seg).strip()
    seg = re.sub(r"^(?:to |a |an |the )", "", seg, flags=re.I).strip()
    seg = seg.strip(".\"'")
    if not seg or " " in seg:
        return None
    return seg


def wordfreq_rating(gloss_en, gloss_pl=""):
    """1-100 rating from a SINGLE-word gloss via wordfreq (English and/or Polish),
    boosted for core vocabulary. None if no single-word gloss or wordfreq is absent."""
    try:
        from wordfreq import zipf_frequency
    except Exception:
        return None
    cands = []
    he = _gloss_head(gloss_en)
    hp = _gloss_head(gloss_pl)
    if he:
        cands.append((he, "en"))
    if hp:
        cands.append((hp, "pl"))
    if not cands:
        return None
    z = max(zipf_frequency(w, lang) for w, lang in cands)
    if z <= 0:
        return None
    rating = max(1, min(100, round(z * 12.5)))
    if he and he.lower() in CORE_MEANINGS:
        rating = max(rating, 88)
    return rating


def read_freq(text):
    m = _FREQ_RE.search(text or "")
    if not m:
        return None
    return max(1, min(100, int(m.group(1))))


def set_freq_text(text, val):
    """Insert or update `freq: <val>` in the front matter."""
    val = max(1, min(100, int(val)))
    if _FREQ_RE.search(text):
        return _FREQ_RE.sub(f"freq: {val}", text, count=1)
    m = re.search(r"(?m)^id:.*$", text)
    if m:
        return text[:m.end()] + f"\nfreq: {val}" + text[m.end():]
    m2 = re.match(r"^﻿?---[ \t]*\r?\n", text)
    if m2:
        return text[:m2.end()] + f"freq: {val}\n" + text[m2.end():]
    return f"---\nfreq: {val}\n---\n\n" + text


def gloss_zipf(gloss_en, gloss_pl=""):
    """Raw wordfreq Zipf (0-8) of a single-word gloss — a fine-grained tiebreak so
    words sharing the same 1-100 rating still order by their true frequency. 0 if
    unavailable."""
    try:
        from wordfreq import zipf_frequency
    except Exception:
        return 0.0
    cands = []
    he = _gloss_head(gloss_en)
    hp = _gloss_head(gloss_pl)
    if he:
        cands.append((he, "en"))
    if hp:
        cands.append((hp, "pl"))
    if not cands:
        return 0.0
    return max(zipf_frequency(w, lang) for w, lang in cands)


def effective_freq(text, gloss_en="", gloss_pl=""):
    """Stored freq -> single-word wordfreq -> 0 (end of deck)."""
    f = read_freq(text)
    if f is not None:
        return f
    wf = wordfreq_rating(gloss_en, gloss_pl)
    return wf if wf is not None else 0


def words_at_freq(cfg, value, exclude="", type_filter="", limit=8):
    """Up to `limit` (8) random corpus words of the SAME word type carrying exactly
    this freq rating — shown under the Frequency field to gauge calibration.
    `type_filter` accepts a filename suffix ('verb', 'noun') or a WORD_TYPES key
    ('verb-root', 'ga-noun'), which is normalized to the suffix before matching."""
    try:
        v = max(1, min(100, int(str(value).strip())))
    except (ValueError, TypeError):
        return {"ok": False, "error": "bad value"}
    import random
    exclude = (exclude or "").strip()
    tf = (type_filter or "").strip().lower()
    if tf in WORD_TYPES:                       # a type key -> its filename suffix
        tf = WORD_TYPES[tf]["suffix"].lower()
    matches = []
    for d in entry_search_dirs(cfg):
        for p in d.glob("*.md"):
            m = FILENAME_RE.match(p.name)
            if not m or m.group("type").lower() == "list" or m.group("word")[0].isdigit():
                continue
            if p.stem == exclude:
                continue
            if tf and m.group("type").lower() != tf:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except Exception:
                continue
            if read_freq(text) != v:
                continue
            ge = re.search(r"^trnsltion\. En:\s*(.+)$", text, re.M)
            matches.append({"word": m.group("word"), "type": m.group("type").lower(),
                            "gloss": (ge.group(1).strip()[:40] if ge else "")})
    random.shuffle(matches)
    return {"ok": True, "value": v, "count": len(matches), "words": matches[:limit]}


def freq_prompt(gloss_en, gloss_pl="", usage_note=""):
    """Prompt for a small local model to estimate everyday frequency (1-100)."""
    return (
        "You rate how often a word is used in everyday language.\n\n"
        "You are given ONE vocabulary item: its English translation(s), optional Polish\n"
        "translation(s), and an optional usage note. The translations all describe the\n"
        "SAME single concept. Judge how often an ordinary speaker would use a word with\n"
        "this meaning in daily life.\n\n"
        "Reply with ONE integer from 1 to 100 and NOTHING else - no words, no\n"
        "punctuation. Higher = more frequent.\n\n"
        "Guide:\n"
        "  90-100  basic/function words: I, you, water, go, not, big, good, hello, thanks\n"
        "  70-89   common everyday words: house, run, cold, friend, eat, road\n"
        "  40-69   ordinary words: shell, elbow, charcoal, dove, whisper\n"
        "  10-39   uncommon/specific: atrophy, ember, silvery\n"
        "  1-9     rare, poetic, or highly technical\n"
        "If the meaning is core basic vocabulary (Swadesh / Leipzig-Jakarta type), rate it high.\n\n"
        f"English: {gloss_en or '(none)'}\n"
        f"Polish: {gloss_pl or '(none)'}\n"
        f"Usage note: {usage_note or '(none)'}\n\n"
        "Answer (1-100):")


def rank_frequency(cfg, dry_run=False):
    """Stamp `freq:` on entries that lack it, using wordfreq on single-word glosses.
    Never overwrites an existing rating (manual or LLM). Idempotent."""
    lex = Lexicon(cfg)
    filled = 0
    already = 0
    no_single = 0
    samples = []
    for e in lex.entries:
        fp = Path(e["path"])
        text = fp.read_text(encoding="utf-8")
        if read_freq(text) is not None:
            already += 1
            continue
        wf = wordfreq_rating(e.get("gloss_en", ""), e.get("gloss_pl", ""))
        if wf is None:
            no_single += 1
            continue
        if not dry_run:
            fp.write_text(set_freq_text(text, wf), encoding="utf-8")
        filled += 1
        if len(samples) < 10:
            samples.append({"word": e["word"], "gloss": (e.get("gloss_en", "") or "")[:32], "freq": wf})
    return {"ok": True, "dry_run": dry_run, "wordfreq_available": _wordfreq_ok(),
            "filled": filled, "already_rated": already,
            "no_single_word_gloss": no_single, "samples": samples}


# ------------------------------------ template comparison (standard fields)

_TPL_FILES = {
    "noun": "Lngstics_Noun Template.md",
    "verb-root": "Lngstics_Verb-root Template.md",
    "verb-u": "Lngstics_Verb-ů Template.md",
    "adjective": "Lngstics_Adjective Template.md",
    "root word": "Lngstics_Root Word Template.md",
    "ga-noun": "Lngstics_Ga-noun Template.md",
    "particle": "Lngstics_Grammar Particle.md",
    "number": "Lngstic_Number Template.md",
    "idiom": "Lngstics_Idiom Template.md",
}


_TPL_HDR_CACHE = {}


def _template_headers(cfg, tpl_key):
    if tpl_key in _TPL_HDR_CACHE:
        return _TPL_HDR_CACHE[tpl_key]
    tp = cfg["_root"] / "00_Templates" / _TPL_FILES.get(tpl_key, "")
    out = None
    if tp.exists():
        out = [s["header"] for s in split_sections(tp.read_text(encoding="utf-8"))]
    _TPL_HDR_CACHE[tpl_key] = out
    return out


def template_key_for(name, text):
    m = FILENAME_RE.match(name + ".md")
    suffix = m.group("type").lower() if m else ""
    if suffix == "verb":
        return "verb-u" if "Verbs_ů (List)" in text else "verb-root"
    if suffix == "noun" and "Ga-noun Compounds" in text:
        return "ga-noun"
    if suffix in ("root word",):
        return "root word"
    if suffix in ("number",):
        return "number"
    if suffix in ("particle",):
        return "particle"
    return suffix if suffix in _TPL_FILES else None


_IGNORE_CACHE = {"mtime": None, "data": None}


def _ignore_path(cfg=None):
    return TOOL_DIR / "audit_ignore.json"


def load_ignores(cfg=None):
    p = _ignore_path()
    if not p.exists():
        return []
    mt = p.stat().st_mtime
    if _IGNORE_CACHE["mtime"] != mt:
        try:
            _IGNORE_CACHE["data"] = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            _IGNORE_CACHE["data"] = []
        _IGNORE_CACHE["mtime"] = mt
    return _IGNORE_CACHE["data"] or []


def set_ignore(cfg, header, remove=False):
    header = (header or "").strip()
    if not header:
        return {"ok": False, "error": "empty header"}
    cur = list(load_ignores())
    if remove:
        cur = [h for h in cur if h.lower() != header.lower()]
    elif header.lower() not in {h.lower() for h in cur}:
        cur.append(header)
    _ignore_path().write_text(json.dumps(sorted(cur), ensure_ascii=False, indent=2) + "\n",
                              encoding="utf-8")
    _IGNORE_CACHE["mtime"] = None
    return {"ok": True, "ignored": sorted(cur)}


def field_audit(cfg, name, text):
    """Standard vs nonstandard sections, judged against the type's template."""
    key = template_key_for(name, text)
    tpl = _template_headers(cfg, key) if key else None
    entry_hdrs = [s["header"] for s in split_sections(text)]
    if tpl is None:
        return {"template": None, "nonstandard": [], "missing_from_template": [],
                "note": "no template for this word type — cannot audit"}
    conventional = ["Usage Note", "Usage Notes", "Grammatical Note", "Lexical Aspect",
                    "Example sentences", "Alternate forms", "Etymology"]
    std = set(tpl) | set(conventional)
    norm = lambda h: re.sub(r"[\s:.;!?,]+$", "", h).lower()
    entry_norm = {}
    for h in entry_hdrs:
        entry_norm.setdefault(norm(h), h)
    case_fixes = []
    for t in list(tpl) + conventional:
        if t not in entry_hdrs and norm(t) in entry_norm:
            case_fixes.append({"from": entry_norm[norm(t)], "to": t})
    # any header with trailing punctuation is a typo even if otherwise unknown
    for h in entry_hdrs:
        stripped = re.sub(r"[\s:.;!?,]+$", "", h)
        if stripped != h and not any(f["from"] == h for f in case_fixes):
            case_fixes.append({"from": h, "to": stripped})
    fix_sources = {f["from"] for f in case_fixes}
    ignores = {h.lower() for h in load_ignores(cfg)}
    raw_nonstandard = [h for h in entry_hdrs
                       if h not in std and h not in fix_sources
                       and not norm(h).startswith("usage note")]
    nonstandard = [h for h in raw_nonstandard if h.lower() not in ignores]
    ignored_present = [h for h in raw_nonstandard if h.lower() in ignores]
    missing = [h for h in tpl if h not in entry_hdrs and norm(h) not in entry_norm]
    return {"template": key, "nonstandard": nonstandard,
            "missing_from_template": missing, "case_fixes": case_fixes,
            "ignored": ignored_present}


def add_missing_sections(cfg, name, dry_run=False):
    """Append every template section the entry lacks, using the template's
    own placeholder content. Appended at the end (surgical, nothing else moves)."""
    fp = entry_file(cfg, name)
    if not fp.exists():
        return {"ok": False, "error": f"No such entry: {name}"}
    text = fp.read_text(encoding="utf-8")
    audit = field_audit(cfg, name, text)
    missing = audit.get("missing_from_template") or []
    if not missing:
        return {"ok": True, "added": [], "note": "no template sections missing"}
    tpl_path = cfg["_root"] / "00_Templates" / _TPL_FILES[audit["template"]]
    tpl_secs = {s["header"]: s["content"] for s in
                split_sections(tpl_path.read_text(encoding="utf-8"))}
    # auto-features: derive the Asaxi word so added sections get the same
    # auto-fill a freshly-created entry would (currently: IPA in Pronunciation).
    wm = re.search(r"(?m)^Word \(Asaxi\):\s*(.+)$", text)
    aword = wm.group(1).strip() if wm else word_from_stem(name)
    updates = []
    for h in missing:
        if h.strip().lower() == "pronunciation":
            content = f"IPA: {suggest_ipa(aword)}"   # auto-suggested, like build_entry
        else:
            content = (tpl_secs.get(h) or "x").strip() or "x"
        updates.append({"header": h, "content": content})
    r = update_entry(cfg, name, section_updates=updates, dry_run=dry_run)
    r["added"] = missing
    return r


def fix_all_headers(cfg, dry_run=True):
    """Apply every pending header capitalization/punctuation fix across the lexicon."""
    lex = Lexicon(cfg)
    fixed = []
    for e in lex.entries:
        name = Path(e["path"]).stem
        text = Path(e["path"]).read_text(encoding="utf-8")
        au = field_audit(cfg, name, text)
        fixes = au.get("case_fixes") or []
        if not fixes:
            continue
        if not dry_run:
            update_entry(cfg, name,
                         section_updates=[{"header": f["from"], "rename_to": f["to"]}
                                          for f in fixes])
        fixed.append({"name": name,
                      "renames": [f'{f["from"]} → {f["to"]}' for f in fixes]})
    return {"ok": True, "dry_run": dry_run, "entries": fixed, "count": len(fixed)}
