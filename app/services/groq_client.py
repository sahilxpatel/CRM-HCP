import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class GroqClient:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        self.mock_mode = os.getenv("GROQ_MOCK", "").lower() in {"1", "true", "yes"}
        if not api_key and not self.mock_mode:
            raise ValueError("GROQ_API_KEY is not set")

        self.primary_model = os.getenv("GROQ_PRIMARY_MODEL", "gemma2-9b-it")
        self.fallback_model = os.getenv(
            "GROQ_FALLBACK_MODEL",
            "llama-3.3-70b-versatile",
        )
        self.client = Groq(api_key=api_key) if api_key else None

    def chat_completion(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ):
        if self.mock_mode:
            return self._mock_completion(messages)
        use_model = model or self.primary_model
        try:
            return self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as exc:
            if self.fallback_model and use_model != self.fallback_model:
                return self.client.chat.completions.create(
                    model=self.fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            raise exc

    def complete_text(
        self,
        messages: List[dict],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> str:
        response = self.chat_completion(
            messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def _mock_completion(self, messages: List[dict]):
        system_prompt = ""
        user_text = ""
        for item in messages:
            if item.get("role") == "system":
                system_prompt = item.get("content", "")
            if item.get("role") == "user":
                user_text = item.get("content", "")

        content = self._mock_response(system_prompt, user_text)

        class _MockMessage:
            def __init__(self, text: str):
                self.content = text

        class _MockChoice:
            def __init__(self, text: str):
                self.message = _MockMessage(text)

        class _MockResponse:
            def __init__(self, text: str):
                self.choices = [_MockChoice(text)]

        return _MockResponse(content)

    def _mock_response(self, system_prompt: str, user_text: str) -> str:
        if "intent router" in system_prompt:
            intent = self._infer_intent(user_text)
            return json.dumps({"intent": intent})

        if "Extract HCP interaction details" in system_prompt:
            extracted = self._extract_interaction(user_text, system_prompt)
            return json.dumps(extracted)

        if "The user wants to edit an interaction" in system_prompt:
            extracted = self._extract_edit(user_text, system_prompt)
            return json.dumps(extracted)

        if "Extract the target HCP name" in system_prompt:
            extracted = self._extract_target(user_text, system_prompt)
            return json.dumps(extracted)

        if "Summarize the interaction notes" in system_prompt:
            return self._summarize(user_text)

        if "Suggest a short, actionable follow-up" in system_prompt:
            return self._followup(user_text)

        if "Given the tool result JSON" in system_prompt:
            return "Noted. I have handled that for you."

        return "How can I help you log or update an HCP interaction?"

    def _infer_intent(self, text: str) -> str:
        lowered = text.lower()
        if "update" in lowered or "edit" in lowered:
            return "edit"
        if "show" in lowered or "list" in lowered or "recent" in lowered:
            return "get"
        if "summarize" in lowered or "summary" in lowered:
            return "summarize"
        if "next" in lowered or "follow" in lowered:
            return "followup"
        if "met" in lowered or "meeting" in lowered or "log" in lowered:
            return "log"
        return "other"

    def _parse_today(self, system_prompt: str) -> datetime:
        match = re.search(r"today=(\d{4}-\d{2}-\d{2})", system_prompt)
        if match:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        return datetime.utcnow()

    def _extract_name(self, text: str) -> Optional[str]:
        match = re.search(r"(Dr\.\s+[A-Za-z]+(?:\s+[A-Za-z]+)?)", text)
        if not match:
            return None
        name = match.group(1)
        tokens = name.split()
        if len(tokens) > 2:
            tail = tokens[-1].lower()
            if tail in {
                "today",
                "yesterday",
                "tomorrow",
                "recent",
                "last",
                "interaction",
                "meeting",
                "visit",
                "call",
            }:
                name = " ".join(tokens[:-1])
        return name

    def _extract_date(self, text: str, system_prompt: str) -> Optional[str]:
        lowered = text.lower()
        base = self._parse_today(system_prompt)
        if "yesterday" in lowered:
            return (base - timedelta(days=1)).date().isoformat()
        if "today" in lowered:
            return base.date().isoformat()
        if "last week" in lowered:
            return (base - timedelta(days=7)).date().isoformat()
        match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text)
        return match.group(1) if match else None

    def _extract_interaction(self, text: str, system_prompt: str) -> dict:
        name = self._extract_name(text) or "Unknown HCP"
        date_value = self._extract_date(text, system_prompt)
        lowered = text.lower()
        if "call" in lowered:
            interaction_type = "Call"
        elif "email" in lowered:
            interaction_type = "Email"
        elif "clinic" in lowered:
            interaction_type = "Clinic visit"
        else:
            interaction_type = "Meeting"
        return {
            "hcp_name": name,
            "interaction_type": interaction_type,
            "date": date_value,
            "notes": text,
        }

    def _extract_edit(self, text: str, system_prompt: str) -> dict:
        match = re.search(r"\b(\d+)\b", text)
        name = self._extract_name(text)
        date_value = self._extract_date(text, system_prompt)
        notes_mode = "append"
        if "replace" in text.lower():
            notes_mode = "replace"
        notes = None
        if "include" in text.lower():
            notes = text.split("include", 1)[1].strip()
        elif "add" in text.lower():
            notes = text.split("add", 1)[1].strip()
        return {
            "id": int(match.group(1)) if match else None,
            "hcp_name": name,
            "interaction_type": None,
            "date": date_value,
            "notes": notes,
            "notes_mode": notes_mode if notes else None,
            "summary": None,
        }

    def _extract_target(self, text: str, system_prompt: str) -> dict:
        return {
            "hcp_name": self._extract_name(text),
            "date": self._extract_date(text, system_prompt),
        }

    def _summarize(self, text: str) -> str:
        words = text.split()
        short = " ".join(words[:18])
        return f"Summary: {short}..."

    def _followup(self, text: str) -> str:
        lowered = text.lower()
        if "not interested" in lowered or "not" in lowered:
            return "Share relevant clinical trial data in two weeks and offer a short Q&A."
        return "Follow up in two weeks with a concise efficacy update and patient outcomes."
