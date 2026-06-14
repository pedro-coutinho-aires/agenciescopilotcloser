"""Template generation and management routes."""
from __future__ import annotations

import base64
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from jinja2 import BaseLoader, Environment
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models import AgencyORM, DocumentTemplateORM
from services.llm_service import llm

logger = logging.getLogger(__name__)

router = APIRouter(tags=["templates"])

TEMPLATE_GEN_SYSTEM_PROMPT = """You are a document template generator for a real estate agency.
Given a document example, generate a reusable Jinja2 HTML template.
Use these placeholder variables: {{ lead_name }}, {{ lead_cpf }}, {{ lead_rg }}, {{ lead_phone }}, {{ lead_email }}, {{ lead_occupation }}, {{ lead_marital_status }}, {{ property_address }}, {{ property_neighborhood }}, {{ property_city }}, {{ property_title }}, {{ owner_name }}, {{ rent }}, {{ condo_fee }}, {{ iptu }}, {{ total_monthly }}, {{ guarantee_type_label }}, {{ deposit_months }}, {{ move_in_date }}, {{ contract_duration_months }}, {{ special_conditions }}, {{ current_date }}
Style it professionally with inline CSS for PDF generation.
Return ONLY the HTML template, no explanations."""

SAMPLE_TEMPLATE_DATA = {
    "lead_name": "João da Silva",
    "lead_cpf": "123.456.789-00",
    "lead_rg": "12.345.678-9",
    "lead_phone": "+55 11 99999-9999",
    "lead_email": "joao@email.com",
    "lead_occupation": "Analista de Produto",
    "lead_marital_status": "Solteiro",
    "property_address": "Rua Harmonia, 123",
    "property_neighborhood": "Vila Madalena",
    "property_city": "São Paulo",
    "property_title": "Apartamento 2 quartos na Vila Madalena",
    "owner_name": "Maria Fernanda",
    "rent": "R$ 2.700,00",
    "condo_fee": "R$ 520,00",
    "iptu": "R$ 110,00",
    "total_monthly": "R$ 3.330,00",
    "guarantee_type_label": "Caução",
    "deposit_months": 3,
    "move_in_date": "10/07/2026",
    "contract_duration_months": 30,
    "special_conditions": "Permitido animais de estimação.",
    "current_date": "14/06/2026",
}


def _infer_template_type(slug: str) -> str:
    """Infer template type from slug."""
    slug_lower = slug.lower()
    if "contract" in slug_lower or "contrato" in slug_lower:
        return "contract"
    return "proposal"


def _template_to_dict(t: DocumentTemplateORM) -> dict:
    return {
        "id": t.id,
        "slug": t.slug,
        "name": t.name,
        "has_html_template": bool(t.html_template),
        "type": _infer_template_type(t.slug),
    }


async def _get_first_agency(db: AsyncSession) -> AgencyORM:
    result = await db.execute(select(AgencyORM).limit(1))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(500, "No agency found — database not seeded")
    return agency


# ---------------------------------------------------------------------------
# POST /api/templates/generate
# ---------------------------------------------------------------------------

@router.post("/templates/generate")
async def generate_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    type: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF/PNG example and generate a Jinja2 HTML template from it."""
    if type not in ("proposal", "contract"):
        raise HTTPException(400, "type must be 'proposal' or 'contract'")

    agency = await _get_first_agency(db)

    content = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    file_name = file.filename or "template_example"

    # Build vision content block
    if not llm._anthropic_client:
        raise HTTPException(503, "Claude Vision not available — set ANTHROPIC_API_KEY")

    b64_content = base64.standard_b64encode(content).decode("utf-8")

    if mime_type == "application/pdf":
        content_block = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64_content,
            },
        }
    elif mime_type in ("image/png", "image/jpeg", "image/jpg", "image/webp"):
        content_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": b64_content,
            },
        }
    else:
        raise HTTPException(400, f"Unsupported file type: {mime_type}. Use PDF or image.")

    try:
        response = llm._anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=TEMPLATE_GEN_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {
                            "type": "text",
                            "text": (
                                f"This is an example of a '{name}' document ({type} type). "
                                "Generate the Jinja2 HTML template based on its structure and content."
                            ),
                        },
                    ],
                }
            ],
        )

        html_template = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if html_template.startswith("```"):
            html_template = html_template.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    except Exception as e:
        logger.error(f"Template generation via Vision failed: {e}")
        raise HTTPException(500, f"Failed to generate template: {e}")

    # Create slug from type + name
    import re
    slug_base = f"{type}_{re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')}"

    # Check for slug conflict
    existing_result = await db.execute(
        select(DocumentTemplateORM).where(
            DocumentTemplateORM.agency_id == agency.id,
            DocumentTemplateORM.slug == slug_base,
        )
    )
    existing = existing_result.scalar_one_or_none()

    if existing:
        # Update existing template's html_template
        existing.html_template = html_template
        existing.name = name
        await db.flush()
        return {
            "id": existing.id,
            "slug": existing.slug,
            "name": existing.name,
            "html_template": existing.html_template,
        }

    template_orm = DocumentTemplateORM(
        agency_id=agency.id,
        slug=slug_base,
        name=name,
        documents=[],
        html_template=html_template,
    )
    db.add(template_orm)
    await db.flush()

    return {
        "id": template_orm.id,
        "slug": template_orm.slug,
        "name": template_orm.name,
        "html_template": template_orm.html_template,
    }


# ---------------------------------------------------------------------------
# GET /api/templates
# ---------------------------------------------------------------------------

@router.get("/templates")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """List all templates for the first agency."""
    agency = await _get_first_agency(db)

    result = await db.execute(
        select(DocumentTemplateORM).where(DocumentTemplateORM.agency_id == agency.id)
    )
    templates = result.scalars().all()

    return [_template_to_dict(t) for t in templates]


# ---------------------------------------------------------------------------
# GET /api/templates/{template_id}/preview
# ---------------------------------------------------------------------------

@router.get("/templates/{template_id}/preview")
async def preview_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Render the html_template with sample data and return the rendered HTML."""
    result = await db.execute(
        select(DocumentTemplateORM).where(DocumentTemplateORM.id == template_id)
    )
    template_orm = result.scalar_one_or_none()
    if not template_orm:
        raise HTTPException(404, "Template not found")

    if not template_orm.html_template:
        raise HTTPException(400, "This template has no html_template. Upload a document example first.")

    try:
        env = Environment(loader=BaseLoader())
        tmpl = env.from_string(template_orm.html_template)
        rendered_html = tmpl.render(**SAMPLE_TEMPLATE_DATA)
    except Exception as e:
        logger.error(f"Template render failed: {e}")
        raise HTTPException(500, f"Failed to render template: {e}")

    return {"html": rendered_html}
