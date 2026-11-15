#!/usr/bin/env python3
"""
ollama_chat.py — LLM Chat via Ollama REST API
=============================================
Sends user messages to a locally-running Ollama instance and returns
the assistant's response. Maintains a rolling conversation context.

Start Ollama:  ollama serve
Pull model:    ollama pull mistral   (or llama3.2:3b for lower RAM)
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Optional

log = logging.getLogger(__name__)

OLLAMA_DEFAULT_URL = "http://127.0.0.1:11434"


class OllamaChat:
    """
    Stateful chat session against a local Ollama model.

    Parameters
    ----------
    model : str
        Ollama model tag, e.g. "mistral", "llama3.2:3b", "phi3".
    system_prompt : str
        System-level instruction prepended to every conversation.
    base_url : str
        Ollama server URL (default: localhost:11434).
    max_history : int
        Maximum number of message pairs to keep in rolling context.
    """

    def __init__(
        self,
        model: str = "mistral",
        system_prompt: str = "You are a helpful, concise voice assistant.",
        base_url: str = OLLAMA_DEFAULT_URL,
        max_history: int = 10,
    ):
        self._model      = model
        self._base_url   = base_url.rstrip("/")
        self._max_hist   = max_history
        self._history: list[dict] = []
        self._system     = system_prompt
        self._ensure_model_loaded()
        log.info("OllamaChat ready (model=%s)", model)

    # ── Public ────────────────────────────────────────────────────────────────

    def chat(self, user_text: str) -> str:
        """Send a message and return the assistant's reply."""
        self._history.append({"role": "user", "content": user_text})
        self._trim_history()

        messages = [{"role": "system", "content": self._system}] + self._history
        payload  = json.dumps({
            "model":    self._model,
            "messages": messages,
            "stream":   False,
            "options":  {"temperature": 0.7, "num_ctx": 2048},
        }).encode()

        try:
            req = urllib.request.Request(
                f"{self._base_url}/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                data   = json.loads(resp.read())
                reply  = data["message"]["content"].strip()
        except urllib.error.URLError as exc:
            log.error("Ollama request failed: %s", exc)
            reply = "Sorry, I could not get a response from the language model."
        except (KeyError, json.JSONDecodeError) as exc:
            log.error("Unexpected Ollama response: %s", exc)
            reply = "I encountered an error processing the response."

        self._history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self):
        """Clear conversation history."""
        self._history.clear()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _trim_history(self):
        """Keep only the last max_history message pairs."""
        max_msgs = self._max_hist * 2
        if len(self._history) > max_msgs:
            self._history = self._history[-max_msgs:]

    def _ensure_model_loaded(self):
        """Ping /api/tags; warn if the model is not found locally."""
        try:
            with urllib.request.urlopen(
                f"{self._base_url}/api/tags", timeout=5
            ) as resp:
                data   = json.loads(resp.read())
                names  = [m["name"] for m in data.get("models", [])]
                if not any(self._model in n for n in names):
                    log.warning(
                        "Model '%s' not found locally. "
                        "Run: ollama pull %s", self._model, self._model
                    )
        except Exception:
            log.warning("Could not reach Ollama at %s", self._base_url)


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bot = OllamaChat(model="mistral")
    while True:
        try:
            q = input("You: ")
        except (EOFError, KeyboardInterrupt):
            break
        print("Bot:", bot.chat(q))
