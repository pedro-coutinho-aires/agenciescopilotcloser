from __future__ import annotations

import uuid
from datetime import date

import jinja2
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.engine import get_db
from db.models import (
    DealORM,
    DocumentTemplateORM,
    GuidelineORM,
    LeadORM,
    PropertyORM,
    ProposalORM,
    ContractDraftORM,
)
from models import (
    GenerateProposalRequest,
    GenerateContractRequest,
    GenerateMessageRequest,
    GenerateSummaryRequest,
    SendForSigningRequest,
    GeneratedTextResponse,
    ProposalStatus,
    ContractStatus,
    DealStage,
    DocumentStatus,
)
from routes.deal import deal_to_dict, _DEAL_OPTIONS
from services.template_engine import render_and_enhance, render_template
from services.pdf_generator import generate_proposal_pdf, generate_contract_pdf, generate_pdf_from_html
from services.llm_service import llm
from integrations.clicksign import clicksign
from integrations.base import SignatureRequest, SignerInfo

router = APIRouter(tags=["generate"])

GUARANTEE_LABELS = {
    "caucao": "Caução",
    "fiador": "Fiador",
    "seguro_fianca": "Seguro-fiança",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _load_deal_with_relations(deal_id: str, db: AsyncSession) -> DealORM:
    result = await db.execute(
        select(DealORM)
        .where(DealORM.id == deal_id)
        .options(*_DEAL_OPTIONS)
    )
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(404, "Deal not found")
    return deal


async def _load_lead(lead_id: str, db: AsyncSession) -> LeadORM:
    result = await db.execute(select(LeadORM).where(LeadORM.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


async def _load_property(property_id: str, db: AsyncSession) -> PropertyORM:
    result = await db.execute(select(PropertyORM).where(PropertyORM.id == property_id))
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(404, "Property not found")
    return prop


def _active_proposal(deal: DealORM):
    return next((p for p in deal.proposals if p.is_active), None)


def _active_contract(deal: DealORM):
    return next((c for c in deal.contract_drafts if c.is_active), None)


async def _resolve_template(template_ref: str, db: AsyncSession) -> tuple[str | None, str]:
    """Resolve a template reference to (html_content_or_none, j2_filename_fallback).

    If template_ref is empty, return (None, "proposal_default.j2").
    If template_ref is a .j2 filename, return (None, template_ref).
    If template_ref is a UUID or slug, look up in DB:
      - If html_template exists, return (html_content, "")
      - Otherwise return (None, "proposal_default.j2")
    """
    if not template_ref:
        return None, "proposal_default.j2"

    if template_ref.endswith(".j2"):
        return None, template_ref

    # Try by UUID (id) first, then by slug
    result = await db.execute(
        select(DocumentTemplateORM).where(DocumentTemplateORM.id == template_ref).limit(1)
    )
    tmpl = result.scalar_one_or_none()

    if tmpl is None:
        result = await db.execute(
            select(DocumentTemplateORM).where(DocumentTemplateORM.slug == template_ref).limit(1)
        )
        tmpl = result.scalar_one_or_none()

    if tmpl is None:
        return None, "proposal_default.j2"

    if tmpl.html_template:
        return tmpl.html_template, ""

    return None, "proposal_default.j2"


def _render_from_string(html_content: str, context: dict, instruction: str = "") -> tuple[str, list[str]]:
    """Render an HTML Jinja2 template from a string and optionally enhance with LLM."""
    warnings: list[str] = []
    try:
        base_text = jinja2.Template(html_content).render(**context)
    except Exception as exc:
        return f"Erro ao renderizar template: {exc}", [str(exc)]

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


def _build_proposal_context(deal: DealORM, lead: LeadORM, prop: PropertyORM) -> dict:
    p = _active_proposal(deal)
    pending_docs = [d.label for d in deal.documents if d.status == DocumentStatus.pending.value]

    return {
        "lead_name": lead.name,
        "lead_phone": lead.phone,
        "lead_email": lead.email or "",
        "property_title": prop.title,
        "property_address": prop.address,
        "property_neighborhood": prop.neighborhood,
        "property_city": prop.city,
        "rent": float(p.rent),
        "condo_fee": float(p.condo_fee),
        "iptu": float(p.iptu),
        "guarantee_type_label": GUARANTEE_LABELS.get(p.guarantee_type, p.guarantee_type),
        "deposit_months": p.deposit_months,
        "move_in_date": p.move_in_date.isoformat() if p.move_in_date else "[PENDENTE]",
        "contract_duration_months": p.contract_duration_months,
        "special_conditions": p.special_conditions or "",
        "pending_documents": pending_docs,
        "current_date": date.today().strftime("%d/%m/%Y"),
    }


def _build_contract_context(deal: DealORM, lead: LeadORM, prop: PropertyORM) -> dict:
    p = _active_proposal(deal)
    if not p:
        raise HTTPException(400, "No active proposal for this deal")

    missing_fields = []
    lead_cpf = lead.cpf
    lead_rg = lead.rg
    lead_marital = lead.marital_status
    lead_occupation = lead.occupation

    if not lead_cpf:
        missing_fields.append("CPF do locatário")
    if not lead_rg:
        missing_fields.append("RG do locatário")
    if not p.move_in_date:
        missing_fields.append("Data de início do contrato")

    return {
        "lead_name": lead.name,
        "lead_cpf": lead_cpf,
        "lead_rg": lead_rg,
        "lead_marital_status": lead_marital,
        "lead_occupation": lead_occupation,
        "lead_email": lead.email or "",
        "lead_phone": lead.phone,
        "owner_name": prop.owner_name or "[PENDENTE]",
        "property_address": prop.address,
        "property_neighborhood": prop.neighborhood,
        "property_city": prop.city,
        "rent": float(p.rent),
        "condo_fee": float(p.condo_fee),
        "iptu": float(p.iptu),
        "contract_duration_months": p.contract_duration_months,
        "move_in_date": p.move_in_date.isoformat() if p.move_in_date else "[PENDENTE]",
        "guarantee_type_label": GUARANTEE_LABELS.get(p.guarantee_type, p.guarantee_type),
        "deposit_months": p.deposit_months,
        "missing_fields": missing_fields,
        "current_date": date.today().strftime("%d/%m/%Y"),
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/generate/proposal")
async def generate_proposal(req: GenerateProposalRequest, db: AsyncSession = Depends(get_db)):
    deal = await _load_deal_with_relations(req.deal_id, db)
    lead = await _load_lead(deal.lead_id, db)
    prop = await _load_property(deal.property_id, db)

    rent = req.rent or float(prop.rent)
    condo_fee = req.condo_fee or float(prop.condo_fee)
    iptu = req.iptu or float(prop.iptu)

    pending_docs = [d.label for d in deal.documents if d.status == DocumentStatus.pending.value]

    # Parse move_in_date
    move_in_date_obj = None
    move_in_date_str = req.move_in_date or (
        lead.desired_move_in_date.isoformat() if lead.desired_move_in_date else ""
    )
    if move_in_date_str:
        try:
            move_in_date_obj = date.fromisoformat(move_in_date_str)
        except ValueError:
            move_in_date_obj = None

    context = {
        "lead_name": lead.name,
        "property_title": prop.title,
        "property_address": prop.address,
        "property_neighborhood": prop.neighborhood,
        "property_city": prop.city,
        "rent": rent,
        "condo_fee": condo_fee,
        "iptu": iptu,
        "guarantee_type_label": GUARANTEE_LABELS.get(req.guarantee_type.value, req.guarantee_type.value),
        "deposit_months": req.deposit_months,
        "move_in_date": move_in_date_str or "[PENDENTE]",
        "contract_duration_months": req.contract_duration_months,
        "special_conditions": req.special_conditions or "",
        "pending_documents": pending_docs,
    }

    html_content, j2_filename = await _resolve_template(req.template_name, db)
    proposal_instruction = "Melhore a linguagem da proposta de forma profissional e cordial, mantendo todos os valores e dados exatos."
    if html_content:
        text, warnings = _render_from_string(html_content, context, instruction=proposal_instruction)
    else:
        text, warnings = render_and_enhance(
            j2_filename,
            context,
            instruction=proposal_instruction,
        )

    # Deactivate previous proposals
    for existing in deal.proposals:
        existing.is_active = False

    # Determine next version
    next_version = max((p.version for p in deal.proposals), default=0) + 1

    proposal = ProposalORM(
        id=str(uuid.uuid4()),
        deal_id=deal.id,
        version=next_version,
        rent=rent,
        condo_fee=condo_fee,
        iptu=iptu,
        guarantee_type=req.guarantee_type.value,
        deposit_months=req.deposit_months,
        move_in_date=move_in_date_obj,
        contract_duration_months=req.contract_duration_months,
        special_conditions=req.special_conditions,
        generated_text=text,
        status=ProposalStatus.draft.value,
        is_active=True,
    )
    db.add(proposal)
    deal.stage = DealStage.proposal_ready.value
    await db.flush()

    return GeneratedTextResponse(text=text, warnings=warnings)


@router.post("/generate/contract")
async def generate_contract(req: GenerateContractRequest, db: AsyncSession = Depends(get_db)):
    deal = await _load_deal_with_relations(req.deal_id, db)

    active_proposal = _active_proposal(deal)
    if not active_proposal:
        raise HTTPException(400, "Gere uma proposta antes de gerar a minuta.")

    lead = await _load_lead(deal.lead_id, db)
    prop = await _load_property(deal.property_id, db)

    context = _build_contract_context(deal, lead, prop)
    missing_fields = context["missing_fields"]

    html_content, j2_filename = await _resolve_template(req.template_name, db)
    # For contracts, fall back to contract_default.j2 instead of proposal_default.j2
    if not html_content and not req.template_name:
        j2_filename = "contract_default.j2"
    elif not html_content and j2_filename == "proposal_default.j2" and req.template_name:
        j2_filename = "contract_default.j2"

    contract_instruction = "Revise a minuta mantendo a linguagem jurídica simples e profissional. Mantenha todos os campos [PENDENTE] como estão. Não crie cláusulas novas."
    if html_content:
        text, warnings = _render_from_string(html_content, context, instruction=contract_instruction)
    else:
        text, warnings = render_and_enhance(
            j2_filename,
            context,
            instruction=contract_instruction,
        )

    # Deactivate previous contracts
    for existing in deal.contract_drafts:
        existing.is_active = False

    next_version = max((c.version for c in deal.contract_drafts), default=0) + 1

    contract = ContractDraftORM(
        id=str(uuid.uuid4()),
        deal_id=deal.id,
        version=next_version,
        template_id=req.template_name,
        generated_text=text,
        missing_fields=missing_fields,
        status=ContractStatus.draft.value,
        is_active=True,
    )
    db.add(contract)
    deal.stage = DealStage.contract_draft_ready.value
    await db.flush()

    return GeneratedTextResponse(text=text, warnings=warnings)


@router.post("/generate/message")
async def generate_message(req: GenerateMessageRequest, db: AsyncSession = Depends(get_db)):
    deal = await _load_deal_with_relations(req.deal_id, db)
    lead = await _load_lead(deal.lead_id, db)
    prop = await _load_property(deal.property_id, db)

    active_proposal = _active_proposal(deal)

    missing_docs = [d.label for d in deal.documents if d.status == DocumentStatus.pending.value]

    rent = float(active_proposal.rent) if active_proposal else float(prop.rent)
    condo_fee = float(active_proposal.condo_fee) if active_proposal else float(prop.condo_fee)
    iptu = float(active_proposal.iptu) if active_proposal else float(prop.iptu)
    guarantee_label = (
        GUARANTEE_LABELS.get(active_proposal.guarantee_type, "Caução")
        if active_proposal else "Caução"
    )
    move_in_date = (
        active_proposal.move_in_date.isoformat()
        if active_proposal and active_proposal.move_in_date
        else (lead.desired_move_in_date.isoformat() if lead.desired_move_in_date else "[PENDENTE]")
    )

    context = {
        "purpose": req.purpose.value,
        "lead_name": lead.name,
        "property_title": prop.title,
        "property_address": prop.address,
        "missing_documents": missing_docs,
        "rent": rent,
        "condo_fee": condo_fee,
        "iptu": iptu,
        "guarantee_type_label": guarantee_label,
        "move_in_date": move_in_date,
    }

    # Fetch relevant guideline
    guideline_feature = f"{req.purpose.value}_guideline"
    guideline_result = await db.execute(
        select(GuidelineORM).where(
            GuidelineORM.feature == guideline_feature,
            GuidelineORM.is_active == True,
        ).limit(1)
    )
    guideline = guideline_result.scalar_one_or_none()

    # Also check for purpose-based feature keys used by the seeded guidelines
    if guideline is None:
        purpose_map = {
            "confirm_proposal": "proposal_message",
            "request_missing_documents": "document_request",
            "explain_next_steps": "contract_message",
            "follow_up_pending": "proposal_message",
        }
        mapped_feature = purpose_map.get(req.purpose.value)
        if mapped_feature:
            guideline_result2 = await db.execute(
                select(GuidelineORM).where(
                    GuidelineORM.feature == mapped_feature,
                    GuidelineORM.is_active == True,
                ).limit(1)
            )
            guideline = guideline_result2.scalar_one_or_none()

    base_instruction = "Melhore a mensagem para ser cordial, profissional e direta. Mantenha curta e adequada para WhatsApp."
    extra_instruction = ""
    if guideline:
        extra_instruction = f"\n\nDiretrizes adicionais: {guideline.content}"

    text, warnings = render_and_enhance(
        "messages.j2",
        context,
        instruction=base_instruction + extra_instruction,
    )

    return GeneratedTextResponse(text=text.strip(), warnings=warnings)


@router.post("/generate/summary")
async def generate_summary(req: GenerateSummaryRequest, db: AsyncSession = Depends(get_db)):
    deal = await _load_deal_with_relations(req.deal_id, db)
    lead = await _load_lead(deal.lead_id, db)
    prop = await _load_property(deal.property_id, db)

    active_proposal = _active_proposal(deal)
    active_contract = _active_contract(deal)

    received_docs = [
        d.label for d in deal.documents
        if d.status in (DocumentStatus.received.value, DocumentStatus.approved.value)
    ]
    pending_docs = [d.label for d in deal.documents if d.status == DocumentStatus.pending.value]
    needs_resend = [
        d.label for d in deal.documents if d.status == DocumentStatus.needs_resend.value
    ]

    stage_labels = {
        "negotiation": "Em negociação",
        "documents_pending": "Documentos pendentes",
        "proposal_ready": "Proposta pronta",
        "contract_draft_ready": "Minuta pronta",
        "waiting_approval": "Aguardando aprovação",
        "closed": "Fechado",
        "lost": "Perdido",
    }

    summary_data = f"""Resumo do Fechamento

Lead: {lead.name}
Telefone: {lead.phone}
Ocupação: {lead.occupation or "N/I"}
Renda: {lead.income_range or "N/I"}

Imóvel: {prop.title}
Endereço: {prop.address}, {prop.neighborhood}, {prop.city}

Status: {stage_labels.get(deal.stage, deal.stage)}

Documentos recebidos ({len(received_docs)}):
{chr(10).join(f'- {d}' for d in received_docs) if received_docs else '- Nenhum'}

Documentos pendentes ({len(pending_docs)}):
{chr(10).join(f'- {d}' for d in pending_docs) if pending_docs else '- Nenhum'}

{'Documentos que precisam reenvio:' + chr(10) + chr(10).join(f'- {d}' for d in needs_resend) if needs_resend else ''}"""

    if active_proposal:
        p = active_proposal
        summary_data += f"""

Condições comerciais:
- Aluguel: R$ {float(p.rent):.2f}
- Condomínio: R$ {float(p.condo_fee):.2f}
- IPTU: R$ {float(p.iptu):.2f}
- Total mensal: R$ {float(p.rent) + float(p.condo_fee) + float(p.iptu):.2f}
- Garantia: {GUARANTEE_LABELS.get(p.guarantee_type, p.guarantee_type)}
- Entrada prevista: {p.move_in_date.isoformat() if p.move_in_date else '[PENDENTE]'}
- Prazo: {p.contract_duration_months} meses"""

    if active_contract and active_contract.missing_fields:
        summary_data += f"""

Campos pendentes na minuta:
{chr(10).join(f'- {f}' for f in active_contract.missing_fields)}"""

    system_prompt = (
        "Você é o copiloto de fechamento da Lais. "
        "Dado o resumo de um processo de fechamento de locação, "
        "adicione ao final uma seção 'Próxima ação sugerida:' com uma recomendação clara e objetiva. "
        "Responda com o resumo completo + a próxima ação."
    )

    enhanced = llm.generate(system_prompt, summary_data)
    text = enhanced if enhanced else summary_data + "\n\nPróxima ação sugerida:\nVerifique os documentos pendentes e entre em contato com o lead."

    return GeneratedTextResponse(text=text)


@router.get("/generate/proposal/pdf/{deal_id}")
async def get_proposal_pdf(deal_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return the proposal as a PDF file."""
    deal = await _load_deal_with_relations(deal_id, db)
    active_proposal = _active_proposal(deal)
    if not active_proposal:
        raise HTTPException(400, "Gere uma proposta antes.")

    # If we have stored proposal text, use it for PDF generation
    if active_proposal.generated_text:
        text = active_proposal.generated_text
        if "<" in text and ("</p>" in text or "</div>" in text or "</table>" in text):
            pdf_bytes = generate_pdf_from_html(text)
        else:
            lead = await _load_lead(deal.lead_id, db)
            prop = await _load_property(deal.property_id, db)
            context = _build_proposal_context(deal, lead, prop)
            pdf_bytes = generate_proposal_pdf(context)
    else:
        lead = await _load_lead(deal.lead_id, db)
        prop = await _load_property(deal.property_id, db)
        context = _build_proposal_context(deal, lead, prop)
        pdf_bytes = generate_proposal_pdf(context)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=proposta_{deal_id}.pdf"},
    )


@router.get("/generate/contract/pdf/{deal_id}")
async def get_contract_pdf(deal_id: str, db: AsyncSession = Depends(get_db)):
    """Generate and return the contract as a PDF file."""
    deal = await _load_deal_with_relations(deal_id, db)
    active_contract = _active_contract(deal)

    # If we have a stored contract with generated text, use it for PDF generation
    if active_contract and active_contract.generated_text:
        text = active_contract.generated_text
        if "<" in text and ("</p>" in text or "</div>" in text or "</table>" in text):
            pdf_bytes = generate_pdf_from_html(text)
        else:
            active_proposal = _active_proposal(deal)
            if not active_proposal:
                raise HTTPException(400, "Gere uma proposta antes de gerar o contrato.")
            lead = await _load_lead(deal.lead_id, db)
            prop = await _load_property(deal.property_id, db)
            context = _build_contract_context(deal, lead, prop)
            pdf_bytes = generate_contract_pdf(context)
    else:
        active_proposal = _active_proposal(deal)
        if not active_proposal:
            raise HTTPException(400, "Gere uma proposta antes de gerar o contrato.")
        lead = await _load_lead(deal.lead_id, db)
        prop = await _load_property(deal.property_id, db)
        context = _build_contract_context(deal, lead, prop)
        pdf_bytes = generate_contract_pdf(context)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=contrato_{deal_id}.pdf"},
    )


@router.post("/generate/contract/sign/{deal_id}")
async def send_contract_for_signing(
    deal_id: str,
    req: SendForSigningRequest = SendForSigningRequest(),
    db: AsyncSession = Depends(get_db),
):
    """Send the contract PDF to Clicksign for digital signature."""
    deal = await _load_deal_with_relations(deal_id, db)
    active_proposal = _active_proposal(deal)
    if not active_proposal:
        raise HTTPException(400, "Gere uma proposta antes.")

    lead = await _load_lead(deal.lead_id, db)
    prop = await _load_property(deal.property_id, db)

    # Use provided email/phone or fall back to lead data
    lead_email = req.lead_email or lead.email or ""
    lead_phone = req.lead_phone or lead.phone or ""
    owner_email = req.owner_email or ""

    if not lead_email:
        raise HTTPException(400, "E-mail do locatário é obrigatório para assinatura digital.")

    context = _build_contract_context(deal, lead, prop)

    # Use template-based PDF if available
    active_contract = _active_contract(deal)
    if active_contract and active_contract.generated_text:
        text = active_contract.generated_text
        if "<" in text and ("</p>" in text or "</div>" in text or "</table>" in text):
            pdf_bytes = generate_pdf_from_html(text)
        else:
            pdf_bytes = generate_contract_pdf(context)
    else:
        pdf_bytes = generate_contract_pdf(context)

    sig_request = SignatureRequest(
        document_name=f"contrato_locacao_{lead.name.replace(' ', '_').lower()}",
        document_pdf=pdf_bytes,
        signers=[
            SignerInfo(
                name=lead.name,
                email=lead_email,
                phone=lead_phone,
                document_cpf=context.get("lead_cpf") or "",
            ),
            SignerInfo(
                name=prop.owner_name or "Proprietário",
                email=owner_email or "proprietario@email.com",
                phone="",
            ),
        ],
        message=f"Contrato de locação — {prop.title}",
    )

    result = clicksign.upload_and_send(sig_request)

    return {
        "success": result.success,
        "provider": result.provider,
        "document_id": result.document_id,
        "signing_url": result.signing_url,
        "status": result.status,
        "error": result.error,
    }
