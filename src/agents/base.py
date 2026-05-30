"""Shared agent plumbing.

An agent = a role persona + one or more loaded skill modules (the distilled
expert frameworks under src/skills/) + a typed JSON contract. This base class
loads skills, builds the system prompt, calls the LLM, and validates the reply
against a Pydantic model.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from ..llm import client

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

T = TypeVar("T", bound=BaseModel)


@lru_cache(maxsize=None)
def load_skill(name: str) -> str:
    """Read a skill module markdown file by stem name (cached)."""
    path = SKILLS_DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Skill module not found: {path}")
    return path.read_text(encoding="utf-8")


class Agent:
    """Base agent: persona + skills -> system prompt; run_json -> validated model."""

    persona: str = ""
    skills: tuple[str, ...] = ()

    def system_prompt(self) -> str:
        blocks = [self.persona.strip()]
        for skill in self.skills:
            blocks.append(load_skill(skill))
        return "\n\n---\n\n".join(b for b in blocks if b)

    def run_json(
        self,
        user_prompt: str,
        model: type[T],
        *,
        temperature: float | None = None,
    ) -> T:
        """Call the LLM in JSON mode and validate into `model`.

        Retries once with a stricter instruction if validation fails.
        """
        schema_hint = (
            "Respond with a single JSON object that matches this schema "
            f"(keys and types):\n{model.model_json_schema()}"
        )
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": f"{user_prompt}\n\n{schema_hint}"},
        ]
        data = client.chat_json(messages, temperature=temperature)
        try:
            return model.model_validate(data)
        except ValidationError:
            # One corrective retry — common with smaller local models.
            messages.append({"role": "assistant", "content": str(data)})
            messages.append(
                {
                    "role": "user",
                    "content": "That did not match the schema. Return ONLY a valid "
                    "JSON object with exactly the required keys and types.",
                }
            )
            data = client.chat_json(messages, temperature=0)
            return model.model_validate(data)

    def run_text(self, user_prompt: str, *, temperature: float | None = None) -> str:
        """Call the LLM for a plain-text reply (e.g. open mock-interview chat)."""
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": user_prompt},
        ]
        return client.chat(messages, temperature=temperature)
