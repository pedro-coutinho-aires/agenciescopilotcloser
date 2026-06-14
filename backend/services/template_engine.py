import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from services.llm_service import llm

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))


def list_templates() -> list[str]:
    """List all available .j2 template files."""
    return [f.name for f in TEMPLATES_DIR.glob("*.j2")]


def render_template(template_name: str, context: dict) -> str:
    """Render a Jinja2 template with the given context."""
    template = env.get_template(template_name)
    return template.render(**context)


def render_and_enhance(
    template_name: str,
    context: dict,
    instruction: str = "",
) -> tuple[str, list[str]]:
    """Render template then optionally enhance with LLM.

    Returns (text, warnings).
    """
    warnings: list[str] = []

    # Step 1: Render base template
    try:
        base_text = render_template(template_name, context)
    except TemplateNotFound:
        return f"Template '{template_name}' não encontrado.", [f"Template {template_name} not found"]

    # Step 2: Enhance with LLM if available
    if not instruction:
        return base_text, warnings

    system_prompt = (
        "Você é um assistente especializado em locação imobiliária. "
        "Você recebe um documento base gerado por template e uma instrução de personalização. "
        "Mantenha a estrutura do documento, melhore a linguagem e aplique a instrução. "
        "Nunca invente dados que não estejam no documento base. "
        "Se houver campos marcados como [PENDENTE], mantenha-os assim. "
        "Responda apenas com o documento final, sem explicações."
    )
    user_prompt = f"Documento base:\n\n{base_text}\n\nInstrução: {instruction}"

    enhanced = llm.generate(system_prompt, user_prompt)
    if enhanced:
        return enhanced, warnings

    warnings.append("LLM indisponível — usando template base sem personalização.")
    return base_text, warnings
