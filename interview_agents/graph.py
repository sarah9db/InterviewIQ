from __future__ import annotations

from langgraph.graph import END, StateGraph

from interview_agents.agents.gmail_agent import parse_email_node
from interview_agents.agents.prep_agent import prep_doc_node
from interview_agents.agents.sheet_agent import update_sheet_node, write_sheet_node
from interview_agents.agents.sms_agent import sms_node
from interview_agents.state import GraphState


def build_email_graph():
    graph = StateGraph(GraphState)

    graph.add_node("parse_email", parse_email_node)
    graph.add_node("write_sheet", write_sheet_node)
    graph.add_node("prep_doc", prep_doc_node)
    graph.add_node("update_sheet", update_sheet_node)

    graph.set_entry_point("parse_email")
    graph.add_edge("parse_email", "write_sheet")
    graph.add_edge("write_sheet", "prep_doc")
    graph.add_edge("prep_doc", "update_sheet")
    graph.add_edge("update_sheet", END)

    return graph.compile()


def build_sms_graph():
    graph = StateGraph(GraphState)
    graph.add_node("sms", sms_node)
    graph.set_entry_point("sms")
    graph.add_edge("sms", END)
    return graph.compile()
