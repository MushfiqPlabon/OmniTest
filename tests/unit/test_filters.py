"""Unit tests for fastapi-filter query builders and `?search=` support."""

from sqlalchemy import select
from sqlalchemy.dialects import postgresql

from app.filters import EssayPromptFilter, QuizFilter, StudyMaterialFilter
from app.modules.essays.models import EssayPrompt
from app.modules.materials.models import StudyMaterial
from app.modules.quizzes.models import Quiz


def _compile_sql(stmt) -> str:
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def test_study_material_filter_search_and_slug_normalization():
    flt = StudyMaterialFilter(subject="  Math ", topic=" Algebra ", difficulty="medium", search="slope")
    assert flt.subject == "math"
    assert flt.topic == "algebra"

    sql = _compile_sql(flt.filter(select(StudyMaterial)))
    assert "study_materials.title ILIKE '%%slope%%'" in sql
    assert "study_materials.content ILIKE '%%slope%%'" in sql
    assert "study_materials.subject = 'math'" in sql


def test_quiz_filter_search_compiles():
    flt = QuizFilter(subject="SCIENCE", search="biology")
    assert flt.subject == "science"

    sql = _compile_sql(flt.filter(select(Quiz)))
    assert "quizzes.title ILIKE '%%biology%%'" in sql
    assert "quizzes.topic ILIKE '%%biology%%'" in sql


def test_essay_prompt_filter_search_compiles():
    flt = EssayPromptFilter(topic="  Persuasive_Essay ", search="micro-grids")
    assert flt.topic == "persuasive_essay"

    sql = _compile_sql(flt.filter(select(EssayPrompt)))
    assert "essay_prompts.topic ILIKE '%%micro-grids%%'" in sql
    assert "essay_prompts.prompt_text ILIKE '%%micro-grids%%'" in sql
