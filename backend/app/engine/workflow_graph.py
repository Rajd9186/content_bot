from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.engine.graph_state import WorkflowState
from app.engine.workflow_nodes import (
    PlannerNode,
    ParallelResearchCoordinator,
    ClaimExtractionNode,
    ContradictionDetectionNode,
    ContentWritingNode,
    CritiqueNode,
    RevisionNode,
    SelfVerificationNode,
    HyperlinkValidationNode,
    should_revise,
)


def build_workflow_graph(
    planner_agent,
    research_service,
    memory_service,
    verifier_agent,
    contradiction_agent,
    writer_agent,
    critique_agent,
    revision_agent,
    self_verifier_agent,
    hyperlink_agent,
    vector_store=None,
    status_callback=None,
    event_callback=None,
) -> StateGraph:
    workflow = StateGraph(WorkflowState)

    workflow.add_node("planner", PlannerNode(planner_agent, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("research", ParallelResearchCoordinator(research_service, memory_service, vector_store=vector_store, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("claim_extraction", ClaimExtractionNode(verifier_agent, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("contradiction_detection", ContradictionDetectionNode(contradiction_agent, vector_store=vector_store, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("content_writer", ContentWritingNode(writer_agent, vector_store=vector_store, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("critique", CritiqueNode(critique_agent, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("revision", RevisionNode(revision_agent, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("self_verification", SelfVerificationNode(self_verifier_agent, status_callback=status_callback, event_callback=event_callback))
    workflow.add_node("hyperlink_validation", HyperlinkValidationNode(hyperlink_agent, status_callback=status_callback, event_callback=event_callback))

    workflow.set_entry_point("planner")

    workflow.add_edge("planner", "research")
    workflow.add_edge("research", "claim_extraction")
    workflow.add_edge("claim_extraction", "contradiction_detection")
    workflow.add_edge("contradiction_detection", "content_writer")
    workflow.add_edge("content_writer", "critique")
    workflow.add_conditional_edges("critique", should_revise, {"revision": "revision", "finalize": "self_verification"})
    workflow.add_edge("revision", "critique")
    workflow.add_edge("self_verification", "hyperlink_validation")
    workflow.add_edge("hyperlink_validation", END)

    return workflow.compile(checkpointer=MemorySaver())
