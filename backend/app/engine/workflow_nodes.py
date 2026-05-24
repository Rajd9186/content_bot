import time
import traceback
import asyncio
from typing import Any

from app.log_config.logger import get_logger


class WorkflowNode:
    def __init__(self, name: str, status_callback: Any = None, event_callback: Any = None):
        self.name = name
        self.logger = get_logger(f"Node:{name}")
        self.status_callback = status_callback
        self.event_callback = event_callback

    async def emit_event(self, project_id: str, event_type: str, message: str, data: dict = None, workflow_id: str = None):
        if self.event_callback:
            try:
                await self.event_callback(project_id, self.name, event_type, message, data, workflow_id)
            except Exception as e:
                self.logger.warning(f"Event callback failed: {e}")

    async def __call__(self, state: dict) -> dict:
        self.logger.info(f"Entering node: {self.name}")
        
        # Trigger real-time status update if callback exists
        if self.status_callback:
            try:
                await self.status_callback(state.get("project_id"), self.name)
            except Exception as cb_err:
                self.logger.warning(f"Status callback failed: {cb_err}")

        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            start = time.time()
            try:
                result = await self.execute(state)
                elapsed = time.time() - start
                
                steps = list(state.get("steps_completed", []))
                steps.append(self.name)
                result["steps_completed"] = steps
                
                telemetry = dict(state.get("telemetry", {}))
                node_durations = telemetry.get("node_durations", {})
                node_durations[self.name] = round(elapsed * 1000, 2)
                telemetry["node_durations"] = node_durations
                
                # Update retry count in telemetry if any
                if attempt > 0:
                    telemetry["total_retries"] = telemetry.get("total_retries", 0) + attempt
                
                result["telemetry"] = telemetry
                self.logger.info(f"Completed node: {self.name} in {elapsed:.2f}s (attempt {attempt+1})")
                return result
            except Exception as e:
                last_error = e
                elapsed = time.time() - start
                self.logger.warning(f"Node {self.name} attempt {attempt+1} failed: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1)) # Simple backoff
                    continue

                self.logger.error(f"Node {self.name} failed after {max_retries+1} attempts: {e}")
                errors = list(state.get("errors", []))
                errors.append({
                    "node": self.name,
                    "error": str(e),
                    "traceback": traceback.format_exc(),
                    "duration_ms": round(elapsed * 1000, 2),
                })
                return {
                    "errors": errors,
                    "steps_completed": list(state.get("steps_completed", [])) + [f"{self.name}_failed"],
                }

    async def execute(self, state: dict) -> dict:
        raise NotImplementedError


class PlannerNode(WorkflowNode):
    def __init__(self, planner_agent):
        super().__init__("planner")
        self.planner = planner_agent

    async def execute(self, state: dict) -> dict:
        outline = await self.planner.run(
            topic=state["topic"],
            title=state["title"],
            content_type=state["content_type"],
            tone=state["tone"],
            target_audience=state["target_audience"],
            points_to_cover=state["points_to_cover"],
            seo_keywords=state["seo_keywords"],
        )
        sections = outline.get("sections", [])
        research_tasks = []
        for s in sections:
            research_tasks.extend(s.get("research_queries", []))
        if not research_tasks:
            research_tasks = [
                f"{state['topic']} current state research findings 2026",
                f"{state['topic']} statistics data evidence",
                f"{state['topic']} trusted source analysis",
                f"{state['topic']} applications impact outcomes",
            ]
        return {
            "outline": outline,
            "research_tasks": [{"query": q, "assigned_to": self._assign_agent(q)} for q in research_tasks],
        }

    def _assign_agent(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["academic", "study", "research", "journal", "paper", "university"]):
            return "academic"
        if any(w in q for w in ["news", "report", "announced", "launched", "partnership"]):
            return "news"
        if any(w in q for w in ["market", "financial", "investment", "revenue", "funding", "economic"]):
            return "financial"
        if any(w in q for w in ["government", "policy", "regulation", "compliance", "law"]):
            return "government"
        return "news"


class ParallelResearchCoordinator(WorkflowNode):
    def __init__(self, research_service, memory_service, vector_store=None):
        super().__init__("research_coordinator")
        self.research_service = research_service
        self.memory = memory_service
        self.vector_store = vector_store

    async def execute(self, state: dict) -> dict:
        import asyncio

        tasks = state.get("research_tasks", [])
        if not tasks:
            return {"all_sources": [], "research_results": {}}
        
        await self.emit_event(state["project_id"], "info", f"Starting research for {len(tasks)} queries across multiple domains", workflow_id=state.get("workflow_id"))

        grouped: dict[str, list[str]] = {}
        for t in tasks:
            agent = t.get("assigned_to", "news")
            grouped.setdefault(agent, []).append(t["query"])

        async def research_agent(agent_name: str, queries: list[str]) -> tuple[str, list[dict]]:
            # Parallelize queries within the agent
            search_tasks = [self.research_service.search(q, agent_type=agent_name) for q in queries]
            search_results_list = await asyncio.gather(*search_tasks)
            
            results = []
            for q, search_results in zip(queries, search_results_list):
                for r in search_results:
                    r["assigned_agent"] = agent_name
                    r["query"] = q
                    # Emit event for each source discovered
                    await self.emit_event(
                        state["project_id"], 
                        "discovery", 
                        f"Found source: {r.get('title')}", 
                        data={"url": r.get("url"), "domain": r.get("domain"), "agent": agent_name},
                        workflow_id=state.get("workflow_id")
                    )
                results.extend(search_results)
            return agent_name, results

        coros = [research_agent(agent, qs) for agent, qs in grouped.items()]
        completed = await asyncio.gather(*coros, return_exceptions=True)

        all_sources = []
        research_results = {}
        
        # Clear vector store for new project run if it exists
        if self.vector_store:
            self.vector_store.clear()

        for item in completed:
            if isinstance(item, Exception):
                self.logger.error(f"Research agent failed: {item}")
                continue
            agent_name, sources = item
            research_results[agent_name] = sources
            all_sources.extend(sources)
            
            # Index snippets in vector store for RAG
            if self.vector_store and sources:
                await self.vector_store.add_documents(sources)

            for s in sources:
                snippet = s.get("content", "") or s.get("snippet", "") or ""
                await self.memory.store(
                    agent_name=agent_name,
                    key=f"research:{s.get('url', '')[:200]}",
                    value={"query": queries_for(agent_name, tasks), "snippet": snippet[:300]},
                    memory_type="research",
                )

        summary = f"Collected {len(all_sources)} sources across {len(research_results)} research domains."
        return {"all_sources": all_sources, "research_results": research_results, "research_summary": summary}


def queries_for(agent: str, tasks: list[dict]) -> str:
    return "; ".join(t["query"] for t in tasks if t.get("assigned_to") == agent)


class ClaimExtractionNode(WorkflowNode):
    def __init__(self, verifier_agent):
        super().__init__("claim_extraction")
        self.verifier = verifier_agent

    async def execute(self, state: dict) -> dict:
        sources = state.get("all_sources", [])
        if not sources:
            return {"claims": [], "verified_claims": []}

        await self.emit_event(state["project_id"], "info", f"Extracting factual claims from {len(sources)} sources", workflow_id=state.get("workflow_id"))

        claims_text = "\n".join(
            s.get("content", "") or s.get("snippet", "") or "" for s in sources
        )
        if not claims_text.strip():
            return {"claims": [], "verified_claims": []}

        result = await self.verifier.run(research_data=claims_text, evidence_sources=sources)
        claims = result.get("claims", [])
        
        for claim in claims:
            await self.emit_event(
                state["project_id"], 
                "claim", 
                f"Extracted claim: {claim.get('claim_text')[:100]}...", 
                data={"confidence": claim.get("confidence")},
                workflow_id=state.get("workflow_id")
            )

        verified = [c for c in claims if c.get("confidence", 0) >= 0.7]
        return {"claims": claims, "verified_claims": verified}


class ContradictionDetectionNode(WorkflowNode):
    def __init__(self, contradiction_agent, vector_store=None):
        super().__init__("contradiction_detection")
        self.contradiction_agent = contradiction_agent
        self.vector_store = vector_store

    async def execute(self, state: dict) -> dict:
        claims = state.get("claims", [])
        sources = state.get("all_sources", [])
        
        await self.emit_event(state["project_id"], "info", f"Analyzing {len(claims)} claims for contradictions", workflow_id=state.get("workflow_id"))

        # Enrich claims with retrieved evidence for better contradiction detection
        enriched_claims = []
        if self.vector_store and self.vector_store.size > 0:
            for c in claims:
                text = c.get("claim_text", "")
                evidence = await self.vector_store.search(text, top_k=3)
                enriched_claims.append({
                    **c,
                    "retrieved_evidence": [
                        {"url": e.get("url"), "content": e.get("content") or e.get("snippet")}
                        for e in evidence
                    ]
                })
        else:
            enriched_claims = claims

        result = await self.contradiction_agent.run(claims=enriched_claims, sources=sources)
        contradictions = result.get("contradictions", [])
        
        for cont in contradictions:
            await self.emit_event(
                state["project_id"], 
                "contradiction", 
                f"Detected contradiction: {cont.get('explanation')[:150]}", 
                data={"severity": cont.get("severity")},
                workflow_id=state.get("workflow_id")
            )

        return {"contradictions": contradictions}


class ContentWritingNode(WorkflowNode):
    def __init__(self, writer_agent, vector_store=None):
        super().__init__("content_writer")
        self.writer = writer_agent
        self.vector_store = vector_store

    async def execute(self, state: dict) -> dict:
        await self.emit_event(state["project_id"], "info", "Writing content draft based on verified claims and research", workflow_id=state.get("workflow_id"))
        # Perform RAG retrieval for relevant context if vector store is populated
        rag_context = ""
        if self.vector_store and self.vector_store.size > 0:
            query = f"{state['topic']} {state['title']}"
            results = await self.vector_store.search(query, top_k=8)
            rag_context = "\n\n".join([
                f"Source: {r.get('url')}\nContent: {r.get('content') or r.get('snippet')}"
                for r in results
            ])
            self.logger.info(f"Retrieved {len(results)} relevant snippets for RAG context")

        content = await self.writer.run(
            title=state["title"],
            outline=state["outline"],
            verified_claims=state.get("verified_claims", []),
            tone=state["tone"],
            target_audience=state["target_audience"],
            content_type=state["content_type"],
            seo_keywords=state["seo_keywords"],
            research_summary=state.get("research_summary", ""),
            rag_context=rag_context,
        )
        return {"content_draft": content, "final_content": content}


class CritiqueNode(WorkflowNode):
    def __init__(self, critique_agent):
        super().__init__("critique")
        self.critique_agent = critique_agent

    async def execute(self, state: dict) -> dict:
        await self.emit_event(state["project_id"], "info", "Critiquing generated content for quality and accuracy", workflow_id=state.get("workflow_id"))
        result = await self.critique_agent.run(
            content=state.get("content_draft", {}),
            claims=state.get("verified_claims", []),
            outline=state.get("outline", {}),
        )
        needs_revision = result.get("needs_revision", False)
        if needs_revision:
            await self.emit_event(state["project_id"], "warning", f"Critique found issues: {result.get('feedback')[:150]}", workflow_id=state.get("workflow_id"))
        return {"critique_result": result, "needs_revision": needs_revision}


class RevisionNode(WorkflowNode):
    def __init__(self, revision_agent):
        super().__init__("revision")
        self.revision_agent = revision_agent

    async def execute(self, state: dict) -> dict:
        revision_count = state.get("revision_count", 0) + 1
        await self.emit_event(state["project_id"], "info", f"Performing content revision #{revision_count}", workflow_id=state.get("workflow_id"))
        result = await self.revision_agent.run(
            content=state.get("content_draft", {}),
            critique=state.get("critique_result", {}),
            revision_number=revision_count,
        )
        return {"content_draft": result.get("content", state["content_draft"]), "revision_count": revision_count}


class SelfVerificationNode(WorkflowNode):
    def __init__(self, self_verifier_agent):
        super().__init__("self_verification")
        self.self_verifier = self_verifier_agent

    async def execute(self, state: dict) -> dict:
        await self.emit_event(state["project_id"], "info", "Starting final self-verification and hallucination check", workflow_id=state.get("workflow_id"))
        content = state.get("final_content", state.get("content_draft", {}))
        result = await self.self_verifier.run(
            content=content.get("markdown", ""),
            citations=content.get("citations", []),
            claims_count=len(content.get("citations", [])),
        )
        
        hallucination_score = result.get("hallucination_risk_score", 0.0)
        if hallucination_score > 0.3:
            await self.emit_event(state["project_id"], "warning", f"Elevated hallucination risk detected: {hallucination_score}", workflow_id=state.get("workflow_id"))
        else:
            await self.emit_event(state["project_id"], "info", "Self-verification passed with high confidence", workflow_id=state.get("workflow_id"))

        return {"audit_result": result}


class HyperlinkValidationNode(WorkflowNode):
    def __init__(self, hyperlink_agent):
        super().__init__("hyperlink_validation")
        self.hyperlink_agent = hyperlink_agent

    async def execute(self, state: dict) -> dict:
        content = state.get("final_content", state.get("content_draft", {}))
        citations = content.get("citations", [])
        markdown = content.get("markdown", "")
        
        await self.emit_event(state["project_id"], "info", f"Validating {len(citations)} hyperlinks for health and trust", workflow_id=state.get("workflow_id"))
        
        result = await self.hyperlink_agent.run(citations=citations, markdown=markdown)
        
        # Hyperlink agent already checks health in Phase 2 update.
        broken_count = sum(1 for r in result.get("results", []) if r.get("status") == "broken")
        if broken_count > 0:
            await self.emit_event(state["project_id"], "warning", f"Found {broken_count} broken or suspicious hyperlinks", workflow_id=state.get("workflow_id"))

        return {"hyperlink_results": result.get("results", [])}


def should_revise(state: dict) -> str:
    needs = state.get("needs_revision", False)
    count = state.get("revision_count", 0)
    max_r = state.get("max_revisions", 3)
    if needs and count < max_r:
        return "revision"
    return "finalize"
