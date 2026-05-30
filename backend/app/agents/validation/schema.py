from __future__ import annotations

import json
import logging
from typing import Any, Optional, Type

from pydantic import BaseModel, ValidationError

from app.agents.contracts import ValidationResult

logger = logging.getLogger(__name__)


class SchemaValidator:
    def validate_data(
        self, data: dict[str, Any], schema: Type[BaseModel],
    ) -> ValidationResult:
        try:
            schema(**data)
            return ValidationResult(valid=True)
        except ValidationError as e:
            errors = []
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err["loc"])
                errors.append(f"{loc}: {err['msg']}")
            return ValidationResult(valid=False, errors=errors)

    def validate_json_string(
        self, raw: str, schema: Type[BaseModel],
    ) -> tuple[Optional[BaseModel], ValidationResult]:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            return None, ValidationResult(
                valid=False, errors=[f"Invalid JSON: {e}"],
            )

        try:
            instance = schema(**data)
            return instance, ValidationResult(valid=True)
        except ValidationError as e:
            errors = []
            for err in e.errors():
                loc = " -> ".join(str(l) for l in err["loc"])
                errors.append(f"{loc}: {err['msg']}")
            return None, ValidationResult(valid=False, errors=errors)

    def validate_content_completeness(
        self, content: str, min_words: int = 100, required_sections: Optional[list[str]] = None,
    ) -> ValidationResult:
        errors = []
        warnings = []

        word_count = len(content.split())
        if word_count < min_words:
            errors.append(
                f"Content too short: {word_count} words, minimum {min_words}"
            )

        if required_sections:
            content_lower = content.lower()
            for section in required_sections:
                section_lower = section.lower()
                heading_patterns = [
                    f"# {section_lower}",
                    f"## {section_lower}",
                    f"# {section_lower}:",
                    f"## {section_lower}:",
                ]
                found = any(
                    pattern in content_lower for pattern in heading_patterns
                )
                if not found:
                    warnings.append(
                        f"Required section '{section}' not found"
                    )

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_citations(
        self, content: str,
    ) -> ValidationResult:
        import re

        citations = re.findall(r"\[Source:\s*([^\]]+)\]", content)
        if not citations:
            return ValidationResult(
                valid=True,
                warnings=["No citations found in content"],
            )
        return ValidationResult(valid=True)
