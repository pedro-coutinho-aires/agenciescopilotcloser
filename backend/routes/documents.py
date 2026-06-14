"""Document upload, processing, and retrieval routes."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models import (
    AttachmentORM,
    DealDocumentORM,
    DealORM,
    DocumentAnalysisORM,
    LeadORM,
)
from services.document_processor import (
    analyze_document,
    extract_lead_data,
    generate_contextual_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])

UPLOADS_DIR = Path(__file__).parent.parent / "uploads"

# Document type -> deal document type mapping
_DOC_TYPE_TO_DEAL_TYPE = {
    "CNH": "rg_cnh",
    "RG": "rg_cnh",
    "CPF": "cpf",
    "Holerite": "comprovante_renda",
    "Comprovante de residência": "comprovante_residencia",
    "Certidão de casamento": "estado_civil",
    "Comprovante de pagamento": "comprovante_caucao",
}


def _attachment_to_dict(att: AttachmentORM) -> dict:
    return {
        "id": att.id,
        "file_name": att.file_name,
        "mime_type": att.mime_type,
        "document_type_classification": att.document_type_classification,
        "url": att.url,
        "created_at": att.created_at.isoformat() if att.created_at else None,
    }


def _analysis_to_dict(analysis: DocumentAnalysisORM) -> dict:
    return {
        "id": analysis.id,
        "attachment_id": analysis.attachment_id,
        "deal_id": analysis.deal_id,
        "lead_id": analysis.lead_id,
        "document_type": analysis.document_type,
        "document_resume": analysis.document_resume,
        "document_html": analysis.document_html,
        "extracted_fields": analysis.extracted_fields or {},
        "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
    }


# ---------------------------------------------------------------------------
# POST /api/documents/process
# ---------------------------------------------------------------------------

@router.post("/documents/process")
async def process_document(
    file: UploadFile = File(...),
    deal_id: Optional[str] = Form(None),
    lead_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload and process a document through the 3-stage LLM pipeline."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    # Read file content
    content = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    original_name = file.filename or "document"

    # Save file to uploads/
    attachment_id = str(uuid4())
    safe_filename = f"{attachment_id}_{original_name}"
    file_path = UPLOADS_DIR / safe_filename
    file_path.write_bytes(content)

    # --- Stage 1: Analyze document ---
    analysis_result = analyze_document(content, mime_type, original_name)

    # Save AttachmentORM
    attachment = AttachmentORM(
        id=attachment_id,
        file_name=original_name,
        mime_type=mime_type,
        document_type_classification=analysis_result.get("document_type"),
        url=f"/api/documents/{attachment_id}/download",
    )
    db.add(attachment)
    await db.flush()

    # Resolve lead_id from deal if not provided directly
    deal_orm: Optional[DealORM] = None
    resolved_lead_id = lead_id

    if deal_id:
        deal_result = await db.execute(select(DealORM).where(DealORM.id == deal_id))
        deal_orm = deal_result.scalar_one_or_none()
        if deal_orm and not resolved_lead_id:
            resolved_lead_id = deal_orm.lead_id

    # Save DocumentAnalysisORM
    doc_analysis = DocumentAnalysisORM(
        attachment_id=attachment_id,
        deal_id=deal_id,
        lead_id=resolved_lead_id,
        document_type=analysis_result.get("document_type"),
        document_resume=analysis_result.get("document_resume"),
        document_html=analysis_result.get("document_html"),
        extracted_fields=analysis_result.get("extracted_fields", {}),
    )
    db.add(doc_analysis)
    await db.flush()

    # --- Stage 2: Extract lead data and update lead ---
    updated_lead_fields: dict = {}
    lead_orm: Optional[LeadORM] = None

    if resolved_lead_id:
        lead_result = await db.execute(
            select(LeadORM).where(LeadORM.id == resolved_lead_id)
        )
        lead_orm = lead_result.scalar_one_or_none()

    if lead_orm:
        lead_current_data = {
            "name": lead_orm.name,
            "cpf": lead_orm.cpf,
            "rg": lead_orm.rg,
            "birth_date": lead_orm.birth_date.isoformat() if lead_orm.birth_date else None,
            "marital_status": lead_orm.marital_status,
            "occupation": lead_orm.occupation,
            "address_extracted": lead_orm.address_extracted,
            "income_extracted": lead_orm.income_extracted,
            "email": lead_orm.email,
            "phone": lead_orm.phone,
        }

        # Fetch prior analyses for this lead
        prior_result = await db.execute(
            select(DocumentAnalysisORM)
            .where(DocumentAnalysisORM.lead_id == resolved_lead_id)
            .where(DocumentAnalysisORM.id != doc_analysis.id)
        )
        prior_analyses = prior_result.scalars().all()
        analysis_history = [
            {"document_type": a.document_type, "extracted_fields": a.extracted_fields}
            for a in prior_analyses
        ]

        updates = extract_lead_data(analysis_result, lead_current_data, analysis_history)
        # Remove meta fields that don't map to LeadORM
        updates.pop("conflict_warning", None)

        # Apply updates to lead
        from datetime import date as _date
        for field, value in updates.items():
            if hasattr(lead_orm, field) and value is not None:
                if field == "birth_date" and isinstance(value, str):
                    try:
                        value = _date.fromisoformat(value)
                    except ValueError:
                        continue
                setattr(lead_orm, field, value)
                updated_lead_fields[field] = str(value) if not isinstance(value, str) else value

        await db.flush()

    # --- Auto-link to deal document checklist ---
    if deal_orm:
        doc_type = analysis_result.get("document_type", "")
        target_deal_type = _DOC_TYPE_TO_DEAL_TYPE.get(doc_type)
        if target_deal_type:
            docs_result = await db.execute(
                select(DealDocumentORM).where(DealDocumentORM.deal_id == deal_id)
            )
            deal_docs = docs_result.scalars().all()
            for deal_doc in deal_docs:
                if deal_doc.type == target_deal_type and deal_doc.status == "pending":
                    deal_doc.status = "received"
                    deal_doc.attachment_id = attachment_id
                    break
        await db.flush()

    # --- Stage 3: Generate contextual response ---
    lead_dict = {}
    if lead_orm:
        lead_dict = {
            "name": lead_orm.name,
            "phone": lead_orm.phone,
            "email": lead_orm.email,
        }

    deal_dict: Optional[dict] = None
    if deal_orm:
        docs_result = await db.execute(
            select(DealDocumentORM).where(DealDocumentORM.deal_id == deal_id)
        )
        deal_docs = docs_result.scalars().all()
        deal_dict = {
            "documents": [
                {"label": d.label, "type": d.type, "status": d.status}
                for d in deal_docs
            ]
        }

    suggested_response = generate_contextual_response(lead_dict, deal_dict, analysis_result)

    return {
        "attachment": _attachment_to_dict(attachment),
        "analysis": _analysis_to_dict(doc_analysis),
        "updated_lead_fields": updated_lead_fields,
        "suggested_response": suggested_response,
    }


# ---------------------------------------------------------------------------
# GET /api/documents/{attachment_id}/download
# ---------------------------------------------------------------------------

@router.get("/documents/{attachment_id}/download")
async def download_document(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download a previously uploaded document."""
    result = await db.execute(
        select(AttachmentORM).where(AttachmentORM.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    if not attachment:
        raise HTTPException(404, "Attachment not found")

    # Find file in uploads dir
    matches = list(UPLOADS_DIR.glob(f"{attachment_id}_*"))
    if not matches:
        raise HTTPException(404, "File not found on disk")

    file_path = matches[0]
    return FileResponse(
        path=str(file_path),
        media_type=attachment.mime_type,
        filename=attachment.file_name,
    )


# ---------------------------------------------------------------------------
# GET /api/documents/{attachment_id}/analysis
# ---------------------------------------------------------------------------

@router.get("/documents/{attachment_id}/analysis")
async def get_document_analysis(
    attachment_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return the DocumentAnalysis record for a given attachment."""
    result = await db.execute(
        select(DocumentAnalysisORM)
        .where(DocumentAnalysisORM.attachment_id == attachment_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(404, "Analysis not found for this attachment")

    return _analysis_to_dict(analysis)
