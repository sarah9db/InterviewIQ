from __future__ import annotations

from interview_agents.models import EmailInfo
from interview_agents.tools.llm_utils import make_llm
from interview_agents.tools.search_tool import SearchTool


llm = make_llm()
search_tool = SearchTool()


def prep_doc_node(state: dict) -> dict:
    email_info: EmailInfo = state["parsed_email"]
    role = email_info.role
    company = email_info.company

    if not role or not company:
        return {"prep_doc": ""}

    research = search_tool.search(
        f'"{company}" "{role}" interview questions responsibilities tech stack recent news'
    )

    prompt = f"""
You are an interview prep assistant.

Role: {role}
Company: {company}
Context from email:
{email_info.snippet or "N/A"}

Web research results (JSON):
{research}

Create a concise but actionable markdown prep guide with sections:
- Role overview at {company}
- What they likely care about
- Likely interview format
- 10-15 likely questions they may ask
- 5-10 strong questions candidate should ask
- Company-specific notes (products, culture, recent news)
""".strip()

    doc = llm.invoke(prompt)
    return {"prep_doc": doc}
