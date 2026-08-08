"use strict";

let runtimePromise = null;

function runtimeUrl(path) {
  return new URL(path, self.location.href).href;
}

async function initializeRuntime() {
  if (runtimePromise) {
    return runtimePromise;
  }
  runtimePromise = (async () => {
    importScripts(runtimeUrl("./pyodide/pyodide.js"));
    const pyodide = await loadPyodide({
      indexURL: runtimeUrl("./pyodide/"),
    });
    const archiveResponse = await fetch(runtimeUrl("./asaxi-runtime.zip"));
    if (!archiveResponse.ok) {
      throw new Error("The published Asaxi grammar runtime is unavailable");
    }
    pyodide.unpackArchive(await archiveResponse.arrayBuffer(), "zip");
    await pyodide.runPythonAsync(`
import json
import pickle
import sys
from pathlib import Path

RUNTIME_ROOT = next(
    (
        candidate
        for candidate in (
            Path("/asaxi-runtime"),
            Path.cwd() / "asaxi-runtime",
            Path("/home/pyodide/asaxi-runtime"),
        )
        if candidate.is_dir()
    ),
    None,
)
if RUNTIME_ROOT is None:
    raise FileNotFoundError("The published Asaxi runtime archive was not extracted")
sys.path.insert(0, str(RUNTIME_ROOT))

from asaxi_workbench.models import LanguageDatabase
from asaxi_workbench.phrase_memory import PhraseMemoryStore
from asaxi_workbench.translation_document import TranslationDocumentAnalyzer
from asaxi_workbench.translation_models import TranslationDirection
from asaxi_workbench.translator import Translator
from asaxi_workbench.version import WORKBENCH_VERSION

with (RUNTIME_ROOT / "asaxi-language-db.pickle").open("rb") as source:
    database = pickle.load(source)
if not isinstance(database, LanguageDatabase):
    raise TypeError("Published grammar database has an unexpected type")

phrase_memory = PhraseMemoryStore(RUNTIME_ROOT / "authored-phrases.runtime.json")
translator = Translator(database, phrase_memory=phrase_memory)
document_analyzer = TranslationDocumentAnalyzer(translator)

def browser_health():
    grammar = database.grammar_model.reference(
        runtime_workbench_version=WORKBENCH_VERSION,
    ).to_dict()
    return {
        "statistics": dict(database.statistics),
        "grammar_model": grammar,
        "grammar_coverage": {"summary": {}},
        "phrase_memory": {
            "enabled": True,
            "writable": False,
            "count": phrase_memory.count,
            "verified_count": phrase_memory.verified_count,
        },
    }

def browser_translate_document(payload):
    if not isinstance(payload, dict):
        raise ValueError("Translation request must be an object")
    text = payload.get("text")
    if not isinstance(text, str):
        raise ValueError("Translation text must be a string")
    if len(text) > 100_000:
        raise ValueError("Translation text exceeds the 100,000 character limit")
    direction = TranslationDirection(payload.get("direction"))
    return document_analyzer.analyze(text, direction).to_dict()

def browser_request(action, payload_json):
    payload = json.loads(payload_json)
    if action == "health":
        result = browser_health()
    elif action == "translate-document":
        result = browser_translate_document(payload)
    else:
        raise ValueError(f"Unsupported browser-runtime action: {action}")
    return json.dumps(result, ensure_ascii=False, sort_keys=True)
`);
    return pyodide;
  })();
  return runtimePromise;
}

self.addEventListener("message", async (event) => {
  const request = event.data || {};
  if (typeof request.id !== "number" || typeof request.action !== "string") {
    return;
  }
  try {
    const pyodide = await initializeRuntime();
    pyodide.globals.set("browser_action", request.action);
    pyodide.globals.set(
      "browser_payload",
      JSON.stringify(request.payload || {}),
    );
    const rendered = await pyodide.runPythonAsync(
      "browser_request(browser_action, browser_payload)",
    );
    self.postMessage({
      id: request.id,
      ok: true,
      payload: JSON.parse(rendered),
    });
  } catch (error) {
    self.postMessage({
      id: request.id,
      ok: false,
      error: error instanceof Error ? error.message : String(error),
    });
  }
});
