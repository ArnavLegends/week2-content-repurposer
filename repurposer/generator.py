"""Provider adapters and validation for generated social-content drafts."""

from __future__ import annotations

import json
import re
from typing import Any

from .prompts import build_prompt


class ContentGenerationError(RuntimeError):
    """Raised when an AI provider fails or returns an unusable response."""


def _safe_provider_message(message: Any, api_key: str) -> str:
    """Return a short provider message without echoing the submitted API key."""
    text = str(message or "No additional error message was supplied.").strip()
    if api_key:
        text = text.replace(api_key, "[REDACTED API KEY]")
    # Prevent a huge HTML/proxy error page from taking over the Streamlit UI.
    text = re.sub(r"\s+", " ", text)
    return text[:500]


def _format_gemini_api_error(exc: Exception, api_key: str) -> str:
    """Translate Gemini HTTP errors into actionable messages."""
    status = getattr(exc, "code", None)
    message = _safe_provider_message(getattr(exc, "message", None) or str(exc), api_key)

    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None

    if status == 429:
        return (
            "Gemini returned HTTP 429 (rate limit or quota exceeded). "
            "Check the API project's model quota and billing/usage limits, then retry after the limit resets. "
            f"Provider message: {message}"
        )
    if status in {401, 403}:
        return (
            f"Gemini returned HTTP {status} (authentication or permission failure). "
            "Check that this is an active Gemini API key from the correct Google AI Studio project. "
            f"Provider message: {message}"
        )
    if status == 404:
        return (
            "Gemini returned HTTP 404 (model or endpoint not found). "
            "Verify the exact model ID and that it is available to this API project. "
            f"Provider message: {message}"
        )
    if status is not None and 500 <= status <= 599:
        return (
            f"Gemini returned HTTP {status} (Google service-side error). This is usually transient, "
            "rather than an invalid API key. Retry once after a minute. If it continues, try "
            "gemini-3.5-flash-lite and check Google's Gemini API status. "
            f"Provider message: {message}"
        )
    if status is not None:
        return f"Gemini returned HTTP {status}. Provider message: {message}"
    return f"Gemini request failed ({type(exc).__name__}). Provider message: {message}"


def parse_output(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        result = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ContentGenerationError("The model returned an unexpected format. Try generating again.") from exc

    if not isinstance(result, dict):
        raise ContentGenerationError("The model response was not a JSON object.")

    thread = result.get("x_thread")
    linkedin = result.get("linkedin_post")
    instagram = result.get("instagram_caption")
    if not isinstance(thread, list) or not 3 <= len(thread) <= 10:
        raise ContentGenerationError("The X thread did not contain a usable number of posts. Try generating again.")
    if not all(isinstance(post, str) and post.strip() for post in thread):
        raise ContentGenerationError("One or more X thread posts were empty or invalid.")
    if not isinstance(linkedin, str) or not linkedin.strip():
        raise ContentGenerationError("The LinkedIn draft was missing. Try generating again.")
    if not isinstance(instagram, str) or not instagram.strip():
        raise ContentGenerationError("The Instagram caption was missing. Try generating again.")

    return {
        "x_thread": [post.strip() for post in thread],
        "linkedin_post": linkedin.strip(),
        "instagram_caption": instagram.strip(),
    }


def generate_content(
    provider: str,
    api_key: str,
    model: str,
    article: dict[str, str],
    audience: str,
    tone: str,
    angle: str,
) -> dict[str, Any]:
    if not api_key.strip():
        raise ContentGenerationError("Add your API key in the sidebar before generating.")
    if not model.strip():
        raise ContentGenerationError("Enter a model name in the sidebar.")

    prompt = build_prompt(
        article_title=article["title"],
        article_url=article["url"],
        article_text=article["text"],
        audience=audience,
        tone=tone,
        angle=angle,
    )

    try:
        if provider == "OpenAI":
            from openai import OpenAI

            client = OpenAI(api_key=api_key.strip())
            response = client.responses.create(
                model=model.strip(),
                input=prompt,
                text={"format": {"type": "json_object"}},
            )
            raw_text = response.output_text
        elif provider == "Google Gemini":
            from google import genai
            from google.genai import errors, types

            try:
                with genai.Client(api_key=api_key.strip()) as client:
                    response = client.models.generate_content(
                        model=model.strip(),
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            temperature=0.8,
                        ),
                    )
                raw_text = response.text
            except errors.APIError as exc:
                raise ContentGenerationError(_format_gemini_api_error(exc, api_key)) from exc
        else:
            raise ContentGenerationError("Choose either OpenAI or Google Gemini.")
    except ContentGenerationError:
        raise
    except Exception as exc:
        # Include enough detail to debug without ever echoing the supplied API key.
        safe_message = _safe_provider_message(str(exc), api_key)
        raise ContentGenerationError(
            f"{provider} request failed ({type(exc).__name__}). Provider message: {safe_message}"
        ) from exc

    if not raw_text:
        raise ContentGenerationError("The provider returned an empty response. Try again or choose another model.")
    return parse_output(raw_text)
