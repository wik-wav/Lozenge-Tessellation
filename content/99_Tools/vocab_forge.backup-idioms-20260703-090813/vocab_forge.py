# -*- coding: utf-8 -*-
"""
Asaxi Vocab Forge — server + CLI.

Run the UI:      python vocab_forge.py serve
Agent CLI:       python vocab_forge.py search <query>
                 python vocab_forge.py validate <word> <type>
                 python vocab_forge.py add --json payload.json [--commit]
                 python vocab_forge.py schema
Stdlib only. See AGENTS.md for the agent contract.
"""
import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
import forge_core as core

TOOL_DIR = Path(__file__).resolve().parent
APP_VERSION = 13  # bump when API routes change


def fresh_lexicon(cfg):
    return core.Lexicon(cfg)


# ----------------------------------------------- LLM backends (optional)
# Supports Ollama (native API) and LM Studio (OpenAI-compatible API).
# config.json -> "llm": {"backend": "auto" | "ollama" | "lmstudio" | "none", ...}

DEFAULT_LLM = {
    "backend": "auto",
    "ollama": {"url": "http://localhost:11434", "model": "llama3.1"},
    "lmstudio": {"url": "http://localhost:1234", "model": ""},
    "timeout_seconds": 60,
}


def llm_cfg(cfg):
    out = dict(DEFAULT_LLM)
    out.update(cfg.get("llm") or {})
    if "ollama" in cfg and "llm" not in cfg:  # legacy config support
        out["ollama"] = {"url": cfg["ollama"]["url"], "model": cfg["ollama"]["model"]}
        out["timeout_seconds"] = cfg["ollama"].get("timeout_seconds", 60)
    return out


def _get_json(url, timeout=2):
    with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
        return json.loads(r.read())


def _probe_ollama(lc):
    models = [m["name"] for m in _get_json(lc["ollama"]["url"] + "/api/tags").get("models", [])]
    return {"available": True, "backend": "ollama", "label": "Ollama", "models": models}


def _probe_lmstudio(lc):
    models = [m["id"] for m in _get_json(lc["lmstudio"]["url"] + "/v1/models").get("data", [])]
    return {"available": True, "backend": "lmstudio", "label": "LM Studio", "models": models}


def llm_status(cfg):
    lc = llm_cfg(cfg)
    order = {"auto": ["ollama", "lmstudio"], "ollama": ["ollama"],
             "lmstudio": ["lmstudio"], "none": []}.get(lc["backend"], [])
    for b in order:
        try:
            return _probe_ollama(lc) if b == "ollama" else _probe_lmstudio(lc)
        except Exception:
            continue
    return {"available": False, "backend": None, "label": None, "models": []}


def llm_call(cfg, prompt):
    """One-shot completion against whichever local backend is up. Returns text."""
    lc = llm_cfg(cfg)
    st = llm_status(cfg)
    if not st["available"]:
        raise RuntimeError("No local LLM reachable. Start Ollama or LM Studio's server.")
    if st["backend"] == "ollama":
        body = json.dumps({"model": lc["ollama"]["model"], "prompt": prompt,
                           "stream": False, "options": {"temperature": 0.3}}).encode()
        req = urllib.request.Request(lc["ollama"]["url"] + "/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=lc["timeout_seconds"]) as r:
            return json.loads(r.read()).get("response", "").strip()
    model = lc["lmstudio"]["model"] or (st["models"][0] if st["models"] else "")
    if not model:
        raise RuntimeError("LM Studio is running but no model is loaded.")
    body = json.dumps({"model": model, "stream": False, "temperature": 0.3,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(lc["lmstudio"]["url"] + "/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=lc["timeout_seconds"]) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def _parse_word_list(text):
    """Small local models drift on format — salvage a clean comma list."""
    text = re.sub(r"(?s)<think>.*?</think>", "", text)
    text = text.strip().strip("`")
    # take the last non-empty line that looks like a list, else the whole thing
    lines = [l.strip(" .") for l in text.splitlines() if l.strip()]
    cand = ""
    for l in lines:
        if "," in l or (len(l.split()) <= 4 and not l.endswith(":")):
            cand = l
    if not cand and lines:
        cand = lines[-1]
    out = []
    for w in re.split(r"[,;\n]+", cand):
        w = re.sub(r"^\d+[.)]\s*", "", w).strip(" .*_\"'`-")
        if w and len(w.split()) <= 4 and len(w) < 40:
            out.append(w)
    seen, dedup = set(), []
    for w in out:
        if w.lower() not in seen:
            seen.add(w.lower()); dedup.append(w)
    return dedup[:12]


_TYPE_LABEL = {
    "noun": "noun", "verb-root": "verb", "verb-u": "verb", "adjective": "adjective",
    "root-word": "root word (bound morpheme)", "ga-noun": "compound noun",
    "particle": "grammatical particle", "number": "number word",
}


def llm_gloss(cfg, payload):
    """Typed gloss helpers: refine / translate / synonyms — all constrained to
    output only translation words, comma-separated. Tuned for small local models."""
    task = payload.get("task", "refine")
    text = (payload.get("text") or "").strip()
    lang = payload.get("lang", "en")          # language of the OUTPUT
    wtype = _TYPE_LABEL.get(payload.get("wtype", ""), payload.get("wtype") or "word")
    if not text:
        return {"ok": False, "error": "the field is empty"}
    lang_name = "English" if lang == "en" else "Polish"
    src_name = "Polish" if lang == "en" else "English"
    art = "an" if wtype[:1].lower() in "aeiou" else "a"
    if task == "refine":
        prompt = (f"Task: reverse dictionary lookup.\n"
                  f"The user is describing the meaning of {art} {wtype}: \"{text}\"\n"
                  f"Give the most fitting, succinct {lang_name} {wtype}(s) for this meaning.\n"
                  f"Output only the {lang_name} translation word(s) or matching short phrases, "
                  f"separated by commas. No explanations, no numbering, no other text.")
    elif task == "translate":
        prompt = (f"Task: translation.\n"
                  f"Translate this {src_name} expression into {lang_name}: \"{text}\"\n"
                  f"It is {art} {wtype}; the translation must also be {art} {wtype}.\n"
                  f"Output only the {lang_name} translation word(s) or short phrases, "
                  f"separated by commas. No explanations, no numbering, no other text.")
    elif task == "synonyms":
        prompt = (f"Task: thesaurus lookup.\n"
                  f"List {lang_name} synonyms and near-synonyms of the {wtype}: \"{text}\"\n"
                  f"Every synonym must also be {art} {wtype}, in {lang_name}.\n"
                  f"Output only the synonym words, separated by commas. "
                  f"No explanations, no numbering, no other text.")
    else:
        return {"ok": False, "error": f"unknown task {task!r}"}
    try:
        raw = llm_call(cfg, prompt)
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
    return {"ok": True, "options": _parse_word_list(raw), "raw": raw[:400]}


def llm_refine(cfg, payload):
    """Fuzzy reverse-dictionary: user's rough gloss -> fitting words."""
    text = (payload.get("text") or "").strip()
    lang = payload.get("lang", "en")
    if not text:
        return {"ok": False, "error": "nothing to refine"}
    lang_name = "English" if lang == "en" else "Polish"
    prompt = (f"Task: reverse dictionary lookup.\n"
              f"Meaning described by the user: \"{text}\"\n"
              f"Give the most fitting, succinct {lang_name} words or very short phrases "
              f"for this meaning.\n"
              f"Output format: only the words or matching phrases separated by commas. "
              f"No explanations, no numbering, no other text.")
    try:
        raw = llm_call(cfg, prompt)
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
    opts = _parse_word_list(raw)
    return {"ok": True, "options": opts, "raw": raw[:400]}


def llm_related(cfg, lex, payload):
    """LLM as fuzzy thesaurus: get synonyms/antonyms of the gloss, then find
    the Asaxi words in the vault whose translations match them."""
    mode = payload.get("mode", "synonyms")
    gl_en = (payload.get("gloss_en") or "").strip()
    gl_pl = (payload.get("gloss_pl") or "").strip()
    if not gl_en and not gl_pl:
        return {"ok": False, "error": "add a translation first"}
    rel = "synonyms and near-synonyms" if mode == "synonyms" else "antonyms (opposites)"
    words = []
    try:
        if gl_en:
            raw = llm_call(cfg, f"List {rel} of the English expression: \"{gl_en}\".\n"
                                f"Output format: only words or short phrases separated by "
                                f"commas. No explanations, no numbering, no other text.")
            words += [("en", w) for w in _parse_word_list(raw)]
        if gl_pl:
            rel_pl = "synonimy i bliskoznaczne słowa" if mode == "synonyms" else "antonimy (przeciwieństwa)"
            raw = llm_call(cfg, f"Podaj {rel_pl} polskiego wyrażenia: \"{gl_pl}\".\n"
                                f"Format odpowiedzi: tylko słowa oddzielone przecinkami. "
                                f"Bez wyjaśnień, bez numeracji, bez innego tekstu.")
            words += [("pl", w) for w in _parse_word_list(raw)]
    except Exception as ex:
        return {"ok": False, "error": str(ex)}
    self_l = (payload.get("word") or "").lower()
    matches, seen = [], set()
    for e in lex.entries:
        if e["word"].lower() == self_l or e["word"].lower() in seen:
            continue
        ten = core._gloss_tokens(e["gloss_en"])
        tpl = core._gloss_tokens(e.get("gloss_pl", ""))
        for lang, w in words:
            toks = {t for t in core._gloss_tokens(w)} or {w.lower()}
            pool = ten if lang == "en" else tpl
            if toks and toks <= pool | {t for t in pool}:
                if toks & pool:
                    matches.append({"word": e["word"], "type": e["type_raw"],
                                    "gloss": e["gloss_en"], "via": f"LLM: {w}"})
                    seen.add(e["word"].lower())
                    break
    return {"ok": True, "llm_words": [w for _, w in words], "matches": matches[:15]}


# ------------------------------------------------------------- server

class Handler(BaseHTTPRequestHandler):
    cfg = None

    def _send(self, obj, code=200, ctype="application/json; charset=utf-8"):
        data = obj if isinstance(obj, bytes) else json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n).decode("utf-8")) if n else {}

    def log_message(self, *a):
        pass

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        cfg = self.cfg
        if u.path in ("/", "/index.html"):
            html = (TOOL_DIR / "ui.html").read_bytes()
            return self._send(html, ctype="text/html; charset=utf-8")
        if u.path == "/api/meta":
            lex = fresh_lexicon(cfg)
            return self._send({
                "types": {k: v["label"] for k, v in core.WORD_TYPES.items()},
                "fields": core.FIELD_SPECS,
                "semantic_fields": lex.semantic_field_names(),
                "lexicon_size": len(lex.entries),
                "llm": llm_status(cfg),
                "version": APP_VERSION,
            })
        if u.path == "/api/search":
            lex = fresh_lexicon(cfg)
            return self._send({"results": lex.search(q.get("q", ""), int(q.get("limit", 12)))})
        if u.path == "/api/schema":
            return self._send(payload_schema())
        if u.path == "/api/browse":
            lex = fresh_lexicon(cfg)
            return self._send({"results": core.browse(lex, q.get("q", ""),
                                                      q.get("type", ""), q.get("field", "")),
                               "types": sorted({e["type_raw"] for e in lex.entries})})
        if u.path == "/api/entry":
            return self._send(core.get_entry(cfg, q.get("name", "")))
        if u.path == "/api/anki_status":
            return self._send(core.anki_status(cfg, name=q.get("name", ""),
                                               word=q.get("word", "")))
        if u.path == "/api/asset":
            fname = re.sub(r"[\\/]", "", q.get("name", ""))
            fp = core.anki_dir(cfg) / fname
            if not fp.exists():
                return self._send({"error": "not found"}, 404)
            ext = fp.suffix.lower().lstrip(".")
            ctype = {"mp3": "audio/mpeg", "webm": "audio/webm", "ogg": "audio/ogg",
                     "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "application/octet-stream")
            return self._send(fp.read_bytes(), ctype=ctype)
        if u.path == "/api/infixes":
            return self._send({"infixes": core.infix_inventory(cfg)})
        if u.path == "/api/links":
            return self._send({"results": core.all_note_names(cfg, q.get("q", ""),
                                                              int(q.get("limit", 20)))})
        return self._send({"error": "not found"}, 404)

    def do_POST(self):
        cfg = self.cfg
        if self.path.startswith("/api/asset_upload"):
            from urllib.parse import urlparse, parse_qs, unquote
            qs = {k: unquote(v[0]) for k, v in
                  parse_qs(urlparse(self.path).query).items()}
            n = int(self.headers.get("Content-Length", 0))
            if n <= 0 or n > 50_000_000:
                return self._send({"ok": False, "error": "bad upload"}, 400)
            data = self.rfile.read(n)
            return self._send(core.save_asset(
                cfg, name=qs.get("name", ""), word=qs.get("word", ""),
                slot=qs.get("slot", ""), ext=qs.get("ext", ""), data=data))
        try:
            body = self._body()
        except Exception:
            return self._send({"error": "invalid JSON"}, 400)
        lex = fresh_lexicon(cfg)
        if self.path == "/api/validate":
            return self._send(core.validate(lex, body))
        if self.path == "/api/preview":
            force = bool(body.pop("force", False))
            return self._send(core.preview(lex, body, force=force))
        if self.path == "/api/commit":
            force = bool(body.pop("force", False))
            return self._send(core.commit(lex, body, force=force))
        if self.path == "/api/llm_refine":
            return self._send(llm_refine(cfg, body))
        if self.path == "/api/llm_gloss":
            return self._send(llm_gloss(cfg, body))
        if self.path == "/api/audit_ignore":
            return self._send(core.set_ignore(cfg, body.get("header", ""),
                                              remove=bool(body.get("remove", False))))
        if self.path == "/api/fix_headers":
            return self._send(core.fix_all_headers(cfg, dry_run=bool(body.get("dry_run", True))))
        if self.path == "/api/entry_addmissing":
            return self._send(core.add_missing_sections(
                cfg, body.get("name", ""), dry_run=bool(body.get("dry_run", False))))
        if self.path == "/api/asset_delete":
            return self._send(core.delete_asset(cfg, body.get("name", "")))
        if self.path == "/api/llm_related":
            return self._send(llm_related(cfg, lex, body))
        if self.path == "/api/linkcheck":
            return self._send({"links": core.check_links(cfg, body.get("names") or [])})
        if self.path == "/api/entry_delete":
            return self._send(core.delete_entry(cfg, body.get("name", ""),
                                                dry_run=bool(body.get("dry_run", True))))
        if self.path == "/api/thesaurus":
            return self._send(core.suggest_related(lex, body))
        if self.path == "/api/morphcheck":
            return self._send(core.compose_check(body.get("word", ""),
                                                 body.get("parts", [])))
        if self.path == "/api/entry_update":
            return self._send(core.update_entry(
                cfg, body.get("name", ""),
                fm_updates=body.get("frontmatter") or {},
                section_updates=body.get("sections") or [],
                dry_run=bool(body.get("dry_run", False)),
                order=body.get("order")))
        return self._send({"error": "not found"}, 404)


def payload_schema():
    return {
        "description": "POST /api/commit (or `add --json`) payload. "
                       "Same payload works for /api/validate and /api/preview.",
        "required": ["word", "type", "gloss_en"],
        "types": list(core.WORD_TYPES.keys()),
        "fields": {k: {"label": v[0], "required": v[1],
                       "applies_to": v[2], "kind": v[3]}
                   for k, v in core.FIELD_SPECS.items()},
        "notes": [
            "semantic_fields entries must match file stems in Semantic_Fields/, e.g. 'Smntc_Field Emotion'.",
            "synonyms/antonyms/derived accept plain Asaxi words; existing words are auto-linked.",
            "ipa may be omitted; it will be derived from the romanization.",
            "commit refuses if validation errors exist unless force=true.",
        ],
        "workflow": "1) GET /api/meta 2) POST /api/validate 3) POST /api/preview 4) POST /api/commit",
    }


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(description="Asaxi Vocab Forge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve", help="run the web UI + API")
    s.add_argument("--port", type=int)
    s.add_argument("--host")
    p = sub.add_parser("search", help="search the lexicon")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=12)
    v = sub.add_parser("validate", help="validate a candidate word")
    v.add_argument("word")
    v.add_argument("type", choices=list(core.WORD_TYPES))
    a = sub.add_parser("add", help="preview/commit an entry from JSON payload")
    a.add_argument("--json", required=True, help="path to JSON payload, or '-' for stdin")
    a.add_argument("--commit", action="store_true", help="actually write (default: dry-run preview)")
    a.add_argument("--force", action="store_true", help="commit despite validation errors")
    sub.add_parser("schema", help="print the JSON payload contract for agents")
    sub.add_parser("fields", help="list semantic field names")
    b = sub.add_parser("backfill-derived",
                       help="retroactively fill Derived terms from etymology links")
    b.add_argument("--commit", action="store_true", help="apply (default: dry-run)")
    th = sub.add_parser("thesaurus", help="synonym/antonym candidates for a gloss")
    th.add_argument("--en", default="")
    th.add_argument("--pl", default="")
    args = ap.parse_args()

    cfg = core.load_config()

    if args.cmd == "serve":
        host = args.host or cfg["server"]["host"]
        port = args.port or cfg["server"]["port"]
        Handler.cfg = cfg
        try:
            srv = ThreadingHTTPServer((host, port), Handler)
        except OSError:
            print(f"Port {port} is already in use by another program.")
            if port == 8765:
                print("(8765 is AnkiConnect's default port — close Anki or use another port.)")
            print(f"Try:  python vocab_forge.py serve --port {port + 1}")
            return
        print(f"Asaxi Vocab Forge → http://{host}:{port}  (vault: {cfg['_root']})")
        print("Ctrl+C to stop.")
        srv.serve_forever()
        return

    lex = fresh_lexicon(cfg)
    if args.cmd == "search":
        out = lex.search(args.query, args.limit)
    elif args.cmd == "validate":
        out = core.validate(lex, {"word": args.word, "type": args.type})
    elif args.cmd == "schema":
        out = payload_schema()
    elif args.cmd == "fields":
        out = lex.semantic_field_names()
    elif args.cmd == "backfill-derived":
        plans = core.backfill_derived(lex)
        if args.commit:
            out = {"applied": [core.apply_derived_update(pl, child_word=pl["child"])
                               for pl in plans]}
        else:
            out = {"dry_run": True, "planned": [
                {"base": pl["base"], "add": pl["line"]} for pl in plans]}
    elif args.cmd == "thesaurus":
        out = core.suggest_related(lex, {"gloss_en": args.en, "gloss_pl": args.pl})
    elif args.cmd == "add":
        raw = sys.stdin.read() if args.json == "-" else Path(args.json).read_text(encoding="utf-8")
        payload = json.loads(raw)
        out = core.commit(lex, payload, force=args.force) if args.commit \
            else core.preview(lex, payload)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
