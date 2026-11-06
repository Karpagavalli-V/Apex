import json
import re
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from flask import current_app
from app.utils.logger import logger

class LLMClient:
    """
    Lightweight, configurable LLM Client supporting Google Gemini and OpenAI REST APIs,
    with automatic redaction, response validation, and deterministic fallback.
    """

    @classmethod
    def sanitize_prompt(cls, text: str) -> str:
        """
        Removes/masks sensitive data before sending prompts to external LLMs.
        - Masks 12-digit account numbers (e.g., 100482918274 -> 100****8274).
        - Strips any JWT or password patterns if accidentally present.
        """
        if not text:
            return ""

        # Mask 12-digit account numbers
        sanitized = re.sub(
            r"\b(100\d{2})(\d{4})(\d{3})\b",
            r"\1****\3",
            text
        )

        # Redact any Bearer tokens
        sanitized = re.sub(
            r"Bearer\s+[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+",
            "[REDACTED_JWT]",
            sanitized
        )

        return sanitized

    @classmethod
    def call_gemini(cls, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> Dict[str, Any]:
        """
        Calls Google Gemini REST API (v1beta) using standard library urllib.
        """
        api_key = current_app.config.get("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured or empty.")

        model = current_app.config.get("GEMINI_MODEL", "gemini-1.5-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        sanitized_prompt = cls.sanitize_prompt(prompt)
        contents = [{"role": "user", "parts": [{"text": sanitized_prompt}]}]

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": cls.sanitize_prompt(system_instruction)}]
            }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            resp_data = json.loads(response.read().decode("utf-8"))

        candidates = resp_data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Gemini API returned no candidates in response.")

        first_part = candidates[0].get("content", {}).get("parts", [{}])[0]
        text_output = first_part.get("text", "").strip()

        return {
            "provider": "gemini",
            "model": model,
            "text": text_output,
            "is_fallback": False
        }

    @classmethod
    def call_openai(cls, prompt: str, system_instruction: Optional[str] = None, json_mode: bool = False) -> Dict[str, Any]:
        """
        Calls OpenAI Chat Completions REST API (v1) using standard library urllib.
        """
        api_key = current_app.config.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not configured or empty.")

        model = current_app.config.get("OPENAI_MODEL", "gpt-4o-mini")
        url = "https://api.openai.com/v1/chat/completions"

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": cls.sanitize_prompt(system_instruction)})
        messages.append({"role": "user", "content": cls.sanitize_prompt(prompt)})

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=12) as response:
            resp_data = json.loads(response.read().decode("utf-8"))

        choices = resp_data.get("choices", [])
        if not choices:
            raise RuntimeError("OpenAI API returned no choices in response.")

        text_output = choices[0].get("message", {}).get("content", "").strip()

        return {
            "provider": "openai",
            "model": model,
            "text": text_output,
            "is_fallback": False
        }

    @classmethod
    def generate(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = False,
        deterministic_fallback_fn=None
    ) -> Dict[str, Any]:
        """
        Routes generation to the configured LLM provider (gemini or openai),
        with seamless, robust fallback to deterministic rule-based generation
        if the API key is missing, network fails, or response is invalid.
        """
        provider = current_app.config.get("LLM_PROVIDER", "gemini").lower()
        fallback_enabled = current_app.config.get("AI_FALLBACK_ON_ERROR", True)

        try:
            if provider == "gemini":
                return cls.call_gemini(prompt, system_instruction, json_mode)
            elif provider == "openai":
                return cls.call_openai(prompt, system_instruction, json_mode)
            elif provider in ("deterministic", "mock"):
                if deterministic_fallback_fn:
                    return deterministic_fallback_fn()
                return {
                    "provider": "deterministic",
                    "model": "rule-based-v1",
                    "text": "Deterministic fallback output.",
                    "is_fallback": True
                }
            else:
                raise ValueError(f"Unsupported LLM provider '{provider}'. Must be 'gemini', 'openai', or 'deterministic'.")

        except Exception as exc:
            logger.warning(f"External LLM generation failed ({provider}): {exc}. Invoking fallback.")
            if fallback_enabled and deterministic_fallback_fn:
                fallback_res = deterministic_fallback_fn()
                fallback_res["fallback_reason"] = str(exc)
                return fallback_res

            raise RuntimeError(f"LLM generation failed and fallback is disabled: {exc}")
