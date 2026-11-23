"""Model Context Protocol (MCP) server exposing OmniTest tools, resources, and prompts.

Why this exists:
External AI clients connect over authenticated HTTP (`/mcp`) or local stdio
(`python -m app.mcp.server`) to search study guides and generate quizzes.

How it avoids duplication:
Each MCP tool opens a short-lived `AsyncSessionLocal()` session and delegates
directly to the canonical handlers in `app.integrations.llm.tools`.
"""

from fastmcp import FastMCP

from app.core.database import AsyncSessionLocal
from app.core.exceptions import NotFoundError
from app.integrations.llm.tools import (
    GenerateQuizArgs,
    SearchMaterialsArgs,
)
from app.integrations.llm.tools import (
    generate_practice_quiz as run_generate_quiz,
)
from app.integrations.llm.tools import (
    search_study_materials as run_search_materials,
)
from app.mcp.auth import current_mcp_user_id
from app.modules.materials.repositories import MaterialRepository
from app.modules.materials.services import MaterialService
from app.modules.quizzes.repositories import QuizRepository
from app.modules.quizzes.services import QuizService

mcp = FastMCP("OmniTest MCP Server")


@mcp.tool()
async def search_study_materials(query: str, limit: int = 5) -> str:
    """Search the OmniTest knowledge base by semantic similarity using pgvector."""
    args = SearchMaterialsArgs(query=query, limit=limit)
    async with AsyncSessionLocal() as session:
        service = MaterialService(MaterialRepository(session))
        data = await run_search_materials(service, args)

    results = data["results"]
    if not results:
        return "No matching study materials found."
    lines: list[str] = []
    for item in results:
        score = item["similarity"] or 0.0
        lines.append(
            f"[Material #{item['material_id']} '{item['title']}' (sim: {score:.2f})]: {item['content_preview']}"
        )
    return "\n\n".join(lines)


@mcp.tool()
async def generate_practice_quiz(
    subject: str,
    topic: str,
    difficulty: str = "medium",
    num_questions: int = 3,
    question_type: str = "mcq",
    user_id: int | None = None,
) -> str:
    """Generate and save an AI practice quiz in PostgreSQL for GED/SAT prep."""
    # On HTTP `/mcp`, derive user_id strictly from the verified JWT (never caller input).
    mcp_uid = current_mcp_user_id.get()
    effective_user_id = mcp_uid if mcp_uid is not None else user_id
    if effective_user_id is None:
        return "Authentication required: provide user_id in stdio mode or a Bearer token over HTTP."

    args = GenerateQuizArgs.model_validate(
        {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "num_questions": num_questions,
            "question_type": question_type,
        }
    )
    async with AsyncSessionLocal() as session:
        service = QuizService(QuizRepository(session))
        quiz_info = await run_generate_quiz(service, effective_user_id, args)
    qid, title, count = quiz_info["quiz_id"], quiz_info["title"], quiz_info["questions_count"]
    return f"Successfully created Quiz ID {qid}: '{title}' with {count} questions."


@mcp.resource("study-material://{material_id}")
async def get_study_material_resource(material_id: str) -> str:
    """Read complete study material content from PostgreSQL by ID."""
    try:
        parsed_id = int(material_id)
    except ValueError:
        return "Invalid material_id format"

    async with AsyncSessionLocal() as session:
        service = MaterialService(MaterialRepository(session))
        try:
            material = await service.get_by_id(parsed_id)
        except NotFoundError:
            return f"Study material #{material_id} not found."

    return (
        f"Title: {material.title}\n"
        f"Subject: {material.subject}\n"
        f"Topic: {material.topic}\n"
        f"Difficulty: {material.difficulty}\n"
        f"Content:\n{material.content}"
    )


@mcp.prompt()
def ged_sat_tutor_prompt(subject: str, topic: str) -> str:
    """Prompt template for tutoring a student on a specific GED or SAT topic."""
    return (
        f"You are OmniTest Tutor. Guide the student through '{topic}' for GED/SAT {subject}.\n"
        "1. Start with an intuitive definition and real-world example.\n"
        "2. Present 1 high-yield rule or formula.\n"
        "3. Walk through 1 typical exam problem step-by-step.\n"
        "4. Ask the student to solve a practice question to test understanding."
    )


if __name__ == "__main__":
    mcp.run()
