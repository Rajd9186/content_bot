from __future__ import annotations

import json
import asyncio
from typing import Optional, Any

from app.agents.base import BaseAgent, AgentMetrics
from app.schemas.agent_inputs.writer import WriterInput
from app.schemas.agent_outputs.writer import WriterOutput
from app.prompts.builders.writer_prompts import build_writer_system_prompt, build_writer_user_prompt
from app.validation import validate_draft
from app.orchestration.retry_engine.retry_middleware import execute_with_retry, RetryConfig
from app.log_config.logger import get_logger

logger = get_logger(__name__)


class WriterAgent(BaseAgent[WriterInput, WriterOutput]):
    def __init__(self):
        super().__init__()
        self._retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            backoff_factor=2.0,
            retryable_exceptions=(json.JSONDecodeError, ValueError, RuntimeError, Exception),
        )

    def system_prompt(self) -> str:
        return build_writer_system_prompt()

    def user_prompt(self, input_data: WriterInput) -> str:
        return build_writer_user_prompt(input_data)

    def parse_response(self, response: str, input_data: WriterInput) -> WriterOutput:
        try:
            result = json.loads(response)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse LLM response as JSON, using fallback")
            return self._build_fallback_output(input_data, "LLM response was not valid JSON")

        markdown = result.get("markdown", "")
        title_from_llm = result.get("title", "")

        if not markdown or len(markdown.strip()) < 50:
            return self._build_fallback_output(input_data, "Generated markdown too short or empty")

        return WriterOutput(
            markdown=markdown,
            summary=result.get("summary", ""),
            word_count=result.get("word_count", 0) or len(markdown.split()),
            citations=result.get("citations", []),
            headings_used=result.get("headings_used", []),
            seo_metadata=result.get("seo_metadata", {}),
            is_valid=True,
            generation_attempts=1,
            quality_score=1.0,
        )

    def _build_fallback_output(self, input_data: WriterInput, reason: str) -> WriterOutput:
        title = input_data.title or "Untitled"
        lines = [f"# {title}", ""]
        rp = input_data.research_packet
        if rp and rp.executive_summary:
            lines.append(f"{rp.executive_summary}")
            lines.append("")

        outline = input_data.outline or {}
        sections = outline.get("sections", [])
        citations = []
        citation_id = 0

        for i, section in enumerate(sections):
            heading = section.get("heading", f"Section {i + 1}")
            key_points = section.get("key_points", [])
            lines.append(f"## {heading}")
            lines.append("")

            for kp in key_points:
                if input_data.verified_claims and citation_id < len(input_data.verified_claims):
                    claim = input_data.verified_claims[citation_id]
                    cl_text = claim.get("claim_text", "")
                    conf = claim.get("confidence", 0)
                    if conf >= 0.5:
                        citation_id += 1
                        citation_text = cl_text.rstrip(".")
                        url = claim.get("source_url", "https://source.example.com")
                        lines.append(f"{citation_text} [^{citation_id}]")
                        lines.append("")
                        citations.append({
                            "id": citation_id,
                            "text": citation_text,
                            "source_url": url,
                            "source_title": f"Source {citation_id}",
                            "claim_id": claim.get("id", ""),
                            "confidence": conf,
                        })
                else:
                    lines.append(f"{kp}.")
                    lines.append("")

        if citations:
            lines.append("## References")
            lines.append("")
            for cit in citations:
                lines.append(f"[^{cit['id']}]: {cit['source_title']} — {cit['source_url']}")

        markdown = "\n".join(lines)
        word_count = len(markdown.split())

        return WriterOutput(
            markdown=markdown,
            summary=f"Generated content about {title}. {reason}",
            word_count=word_count,
            citations=citations,
            headings_used=[s.get("heading", f"Section {i+1}") for i, s in enumerate(sections)],
            is_valid=False,
            validation_errors=[reason],
            generation_attempts=1,
            quality_score=0.0,
        )

    async def run(self, input_data: WriterInput) -> WriterOutput:
        system = self.system_prompt()
        user = self.user_prompt(input_data)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        self.logger.info("Writer starting generation", extra={
            "title": input_data.title,
            "claims": len(input_data.verified_claims),
            "sections": len(input_data.outline.get("sections", [])) if input_data.outline else 0,
        })

        async def attempt_generation(attempt_input: WriterInput) -> WriterOutput:
            try:
                llm_response = await self.call_llm(messages, temperature=0.3)
                output = self.parse_response(llm_response.content, attempt_input)
                output.generation_attempts = 1

                report = validate_draft(
                    markdown=output.markdown,
                    title=input_data.title,
                    citations=output.citations,
                    headings_used=output.headings_used,
                    outline_sections=input_data.outline.get("sections", []) if input_data.outline else [],
                )

                output.is_valid = report.is_valid
                output.validation_errors = report.errors
                output.quality_score = report.quality_score

                if not report.is_valid:
                    raise ValueError(f"Draft validation failed: {'; '.join(report.errors)}")

                self._metrics.validation_score = report.quality_score
                self.logger.info("Writer generation successful", extra={
                    "word_count": output.word_count,
                    "citations": len(output.citations),
                    "quality": report.quality_score,
                    "tokens": self._metrics.total_tokens,
                })
                return output

            except json.JSONDecodeError as e:
                self.logger.warning("JSON decode error on attempt", extra={"error": str(e)[:100]})
                raise
            except Exception as e:
                self.logger.warning("Generation attempt failed", extra={"error": str(e)[:200]})
                raise

        retry_result = await execute_with_retry(
            attempt_generation, input_data,
            config=self._retry_config,
        )

        if retry_result.success and retry_result.result:
            output = retry_result.result
            output.generation_attempts = len(retry_result.attempts)
            self._metrics.retry_count = len(retry_result.attempts) - 1
            return output

        self.logger.warning("All writer retries exhausted, using fallback", extra={
            "error": retry_result.error,
            "attempts": len(retry_result.attempts),
        })
        output = self._build_fallback_output(input_data, retry_result.error or "All retries exhausted")
        output.generation_attempts = len(retry_result.attempts)
        self._metrics.retry_count = len(retry_result.attempts) - 1
        self._metrics.error = retry_result.error
        return output
