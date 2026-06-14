from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import get_db
from db.models import (
    AgencyORM,
    DealORM,
    DealDocumentORM,
    DocumentTemplateORM,
    LeadORM,
    PropertyORM,
    ChatMessageORM,
)
from models import (
    CreateDealRequest,
    LinkAttachmentRequest,
    UpdateDocStatusRequest,
    DocumentStatus,
    DealStage,
)
from services.document_reader import read_document_with_vision

router = APIRouter(tags=["deal"])


# ---------------------------------------------------------------------------
# Serialization helper
# ---------------------------------------------------------------------------

def _doc_to_dict(doc: DealDocumentORM) -> dict:
    return {
        "id": doc.id,
        "label": doc.label,
        "type": doc.type,
        "status": doc.status,
        "attachment_id": doc.attachment_id,
        "notes": doc.notes,
        "is_optional": doc.is_optional,
    }


def _proposal_to_dict(p) -> Optional[dict]:
    if p is None:
        return None
    return {
        "id": p.id,
        "deal_id": p.deal_id,
        "rent": float(p.rent),
        "condo_fee": float(p.condo_fee),
        "iptu": float(p.iptu),
        "guarantee_type": p.guarantee_type,
        "deposit_months": p.deposit_months,
        "move_in_date": p.move_in_date.isoformat() if p.move_in_date else "",
        "contract_duration_months": p.contract_duration_months,
        "special_conditions": p.special_conditions,
        "generated_text": p.generated_text,
        "status": p.status,
    }


def _contract_to_dict(c) -> Optional[dict]:
    if c is None:
        return None
    return {
        "id": c.id,
        "deal_id": c.deal_id,
        "template_id": c.template_id or "",
        "generated_text": c.generated_text,
        "missing_fields": c.missing_fields or [],
        "status": c.status,
    }


def deal_to_dict(deal: DealORM) -> dict:
    """Convert a DealORM with eagerly loaded relationships to the Pydantic Deal shape."""
    active_proposal = next(
        (p for p in deal.proposals if p.is_active), None
    )
    active_contract = next(
        (c for c in deal.contract_drafts if c.is_active), None
    )

    # Determine template slug for document_template_id field
    template_slug = ""
    if deal.document_template:
        template_slug = deal.document_template.slug

    return {
        "id": deal.id,
        "lead_id": deal.lead_id,
        "property_id": deal.property_id,
        "type": deal.type,
        "stage": deal.stage,
        "document_template_id": template_slug,
        "documents": [_doc_to_dict(d) for d in deal.documents],
        "proposal": _proposal_to_dict(active_proposal),
        "contract_draft": _contract_to_dict(active_contract),
        "pending_actions": deal.pending_actions or [],
        "created_at": deal.created_at.isoformat() if deal.created_at else "",
        "updated_at": deal.updated_at.isoformat() if deal.updated_at else "",
    }


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

_DEAL_OPTIONS = [
    selectinload(DealORM.documents),
    selectinload(DealORM.proposals),
    selectinload(DealORM.contract_drafts),
    selectinload(DealORM.document_template),
]


async def _get_deal_or_404(deal_id: str, db: AsyncSession) -> DealORM:
    result = await db.execute(
        select(DealORM)
        .where(DealORM.id == deal_id)
        .options(*_DEAL_OPTIONS)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/mock-data")
async def get_mock_data(db: AsyncSession = Depends(get_db)):
    """Return mock lead, property, messages, and document templates for the frontend."""
    # Fetch first agency
    agency_result = await db.execute(select(AgencyORM).limit(1))
    agency = agency_result.scalar_one_or_none()
    if not agency:
        raise HTTPException(500, "Database not seeded — no agency found")

    # First lead for the agency
    lead_result = await db.execute(
        select(LeadORM).where(LeadORM.agency_id == agency.id).limit(1)
    )
    lead_orm = lead_result.scalar_one_or_none()

    # First property for the agency
    prop_result = await db.execute(
        select(PropertyORM).where(PropertyORM.agency_id == agency.id).limit(1)
    )
    prop_orm = prop_result.scalar_one_or_none()

    # Chat messages for the lead (if any)
    messages = []
    if lead_orm:
        msgs_result = await db.execute(
            select(ChatMessageORM)
            .where(ChatMessageORM.lead_id == lead_orm.id)
            .order_by(ChatMessageORM.created_at)
        )
        msgs = msgs_result.scalars().all()
        messages = [
            {
                "id": m.id,
                "sender": m.sender,
                "text": m.text,
                "created_at": m.created_at.isoformat(),
                "attachments": [],
            }
            for m in msgs
        ]

    # Document templates for the agency
    tmpl_result = await db.execute(
        select(DocumentTemplateORM).where(DocumentTemplateORM.agency_id == agency.id)
    )
    templates_orm = tmpl_result.scalars().all()
    document_templates = {
        t.slug: {"id": t.slug, "name": t.name}
        for t in templates_orm
    }

    lead_dict = None
    if lead_orm:
        lead_dict = {
            "id": lead_orm.id,
            "name": lead_orm.name,
            "phone": lead_orm.phone,
            "email": lead_orm.email,
            "interest_type": lead_orm.interest_type,
            "income_range": lead_orm.income_range,
            "desired_move_in_date": lead_orm.desired_move_in_date.isoformat() if lead_orm.desired_move_in_date else None,
            "marital_status": lead_orm.marital_status,
            "occupation": lead_orm.occupation,
        }

    prop_dict = None
    if prop_orm:
        prop_dict = {
            "id": prop_orm.id,
            "title": prop_orm.title,
            "address": prop_orm.address,
            "neighborhood": prop_orm.neighborhood,
            "city": prop_orm.city,
            "rent": float(prop_orm.rent),
            "condo_fee": float(prop_orm.condo_fee),
            "iptu": float(prop_orm.iptu),
            "bedrooms": prop_orm.bedrooms,
            "parking_spots": prop_orm.parking_spots,
            "accepts_pet": prop_orm.accepts_pet,
            "status": prop_orm.status,
            "owner_name": prop_orm.owner_name,
        }

    return {
        "lead": lead_dict,
        "property": prop_dict,
        "messages": messages,
        "document_templates": document_templates,
    }


@router.post("/deal")
async def create_deal(req: CreateDealRequest, db: AsyncSession = Depends(get_db)):
    # Find template by slug
    tmpl_result = await db.execute(
        select(DocumentTemplateORM).where(
            DocumentTemplateORM.slug == req.document_template_id
        )
    )
    template = tmpl_result.scalar_one_or_none()
    if not template:
        raise HTTPException(404, f"Template '{req.document_template_id}' not found")

    # Find agency from lead
    lead_result = await db.execute(
        select(LeadORM).where(LeadORM.id == req.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    deal = DealORM(
        id=str(uuid.uuid4()),
        agency_id=lead.agency_id,
        lead_id=req.lead_id,
        property_id=req.property_id,
        document_template_id=template.id,
        type="locacao",
        stage="negotiation",
        pending_actions=[
            "Confirmar modalidade de garantia",
            "Solicitar documentos obrigatórios",
            "Gerar proposta comercial",
        ],
    )
    db.add(deal)
    await db.flush()  # get deal.id

    # Insert deal documents from template
    for doc_data in template.documents:
        doc = DealDocumentORM(
            id=str(uuid.uuid4()),
            deal_id=deal.id,
            label=doc_data["label"],
            type=doc_data["type"],
            status="pending",
        )
        db.add(doc)

    await db.flush()

    # Reload with relationships
    result = await db.execute(
        select(DealORM)
        .where(DealORM.id == deal.id)
        .options(*_DEAL_OPTIONS)
    )
    deal_loaded = result.scalar_one()

    return deal_to_dict(deal_loaded)


@router.get("/deal/{deal_id}")
async def get_deal(deal_id: str, db: AsyncSession = Depends(get_db)):
    deal = await _get_deal_or_404(deal_id, db)
    return deal_to_dict(deal)


@router.patch("/deal/{deal_id}/link-attachment")
async def link_attachment(
    deal_id: str, req: LinkAttachmentRequest, db: AsyncSession = Depends(get_db)
):
    deal = await _get_deal_or_404(deal_id, db)

    target_doc = next((d for d in deal.documents if d.id == req.document_id), None)
    if not target_doc:
        raise HTTPException(404, f"Document '{req.document_id}' not found in deal")

    target_doc.status = DocumentStatus.received.value
    target_doc.attachment_id = req.attachment_id

    # Move deal to documents_pending stage
    deal.stage = DealStage.documents_pending.value

    await db.flush()
    return deal_to_dict(deal)


@router.patch("/deal/{deal_id}/update-doc-status")
async def update_doc_status(
    deal_id: str, req: UpdateDocStatusRequest, db: AsyncSession = Depends(get_db)
):
    deal = await _get_deal_or_404(deal_id, db)

    target_doc = next((d for d in deal.documents if d.id == req.document_id), None)
    if not target_doc:
        raise HTTPException(404, f"Document '{req.document_id}' not found in deal")

    target_doc.status = req.status.value

    await db.flush()
    return deal_to_dict(deal)


@router.patch("/deal/{deal_id}/toggle-doc-optional")
async def toggle_doc_optional(
    deal_id: str,
    document_id: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    deal = await _get_deal_or_404(deal_id, db)

    target_doc = next((d for d in deal.documents if d.id == document_id), None)
    if not target_doc:
        raise HTTPException(404, f"Document '{document_id}' not found in deal")

    target_doc.is_optional = not target_doc.is_optional

    await db.flush()
    return deal_to_dict(deal)


@router.post("/deal/{deal_id}/read-document")
async def read_uploaded_document(
    deal_id: str,
    file: UploadFile = File(...),
    document_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document, use AI to read it, extract lead fields, and auto-link to checklist."""
    deal = await _get_deal_or_404(deal_id, db)

    content = await file.read()
    mime = file.content_type or "application/octet-stream"

    # Use Claude Vision to extract fields
    extracted = read_document_with_vision(content, mime, file.filename or "")
    fields = extracted.model_dump(exclude_none=True)

    # Update lead with extracted fields
    lead_result = await db.execute(
        select(LeadORM).where(LeadORM.id == deal.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    if lead:
        if fields.get("cpf"):
            lead.cpf = fields["cpf"]
        if fields.get("rg"):
            lead.rg = fields["rg"]
        if fields.get("marital_status"):
            lead.marital_status = fields["marital_status"]
        if fields.get("occupation"):
            lead.occupation = fields["occupation"]
        if fields.get("birth_date"):
            # birth_date from vision is a string; convert to date if possible
            from datetime import date as _date
            bd = fields["birth_date"]
            if isinstance(bd, str):
                try:
                    lead.birth_date = _date.fromisoformat(bd)
                except ValueError:
                    pass  # ignore unparseable date strings
            elif isinstance(bd, _date):
                lead.birth_date = bd

    # Auto-link to document checklist if document_id provided
    if document_id:
        for doc in deal.documents:
            if doc.id == document_id:
                doc.status = DocumentStatus.received.value
                doc.attachment_id = file.filename
                break

    # Auto-classify and link if no document_id
    if not document_id and extracted.document_type:
        doc_type_map = {
            "CNH": "doc_rg_cnh",
            "RG": "doc_rg_cnh",
            "Holerite": "doc_income",
            "CPF": "doc_cpf",
            "Comprovante de residência": "doc_address",
        }
        target_doc_id = doc_type_map.get(extracted.document_type, "")
        if target_doc_id:
            for doc in deal.documents:
                if doc.id == target_doc_id and doc.status == DocumentStatus.pending.value:
                    doc.status = DocumentStatus.received.value
                    doc.attachment_id = file.filename
                    break

    deal.stage = DealStage.documents_pending.value
    await db.flush()

    return {
        "extracted_fields": fields,
        "deal": deal_to_dict(deal),
    }


@router.patch("/lead/{lead_id}")
async def update_lead(
    lead_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """Update any fields on a LeadORM record."""
    lead_result = await db.execute(select(LeadORM).where(LeadORM.id == lead_id))
    lead = lead_result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")

    allowed_fields = {
        "name", "phone", "email", "interest_type", "income_range",
        "desired_move_in_date", "marital_status", "occupation",
        "cpf", "rg", "birth_date", "address_extracted", "income_extracted",
    }

    from datetime import date as _date

    for field, value in body.items():
        if field not in allowed_fields:
            continue
        if value is None:
            setattr(lead, field, None)
            continue
        if field in ("birth_date", "desired_move_in_date") and isinstance(value, str):
            try:
                value = _date.fromisoformat(value)
            except ValueError:
                continue
        setattr(lead, field, value)

    await db.flush()

    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "interest_type": lead.interest_type,
        "income_range": lead.income_range,
        "desired_move_in_date": lead.desired_move_in_date.isoformat() if lead.desired_move_in_date else None,
        "marital_status": lead.marital_status,
        "occupation": lead.occupation,
        "cpf": lead.cpf,
        "rg": lead.rg,
        "birth_date": lead.birth_date.isoformat() if lead.birth_date else None,
        "address_extracted": lead.address_extracted,
        "income_extracted": lead.income_extracted,
    }


@router.get("/deal/{deal_id}/extracted-fields")
async def get_extracted_fields(deal_id: str, db: AsyncSession = Depends(get_db)):
    """Get all fields extracted from documents for this deal (reads from lead table)."""
    # Get deal to find lead_id
    deal_result = await db.execute(
        select(DealORM).where(DealORM.id == deal_id)
    )
    deal = deal_result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, "Deal not found")

    lead_result = await db.execute(
        select(LeadORM).where(LeadORM.id == deal.lead_id)
    )
    lead = lead_result.scalar_one_or_none()
    if not lead:
        return {}

    fields: dict = {}
    if lead.cpf:
        fields["cpf"] = lead.cpf
    if lead.rg:
        fields["rg"] = lead.rg
    if lead.marital_status:
        fields["marital_status"] = lead.marital_status
    if lead.occupation:
        fields["occupation"] = lead.occupation
    if lead.birth_date:
        fields["birth_date"] = lead.birth_date.isoformat()
    if lead.address_extracted:
        fields["address_extracted"] = lead.address_extracted
    if lead.income_extracted:
        fields["income_extracted"] = lead.income_extracted

    return fields
