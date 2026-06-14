"""Seed the database with default agency, mock lead, mock property, and document templates."""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AgencyORM, GuidelineORM, LeadORM, PropertyORM, DocumentTemplateORM, ChatMessageORM

_DATA_DIR = Path(__file__).parent.parent / "data" / "lead_mocked_docs"
_UPLOADS_DIR = Path(__file__).parent.parent / "uploads"


async def seed_db(session: AsyncSession) -> None:
    # Check if agency table already has data
    result = await session.execute(select(AgencyORM).limit(1))
    if result.scalar_one_or_none() is not None:
        return  # Already seeded

    # --- Agency ---
    agency = AgencyORM(
        name="Imobiliária Demo",
        cnpj="00.000.000/0001-00",
    )
    session.add(agency)
    await session.flush()  # get agency.id

    # --- Mock Lead (João Silva from mock_data.py) ---
    # cpf, rg, birth_date, address_extracted, income_extracted left empty
    # so they get filled automatically when documents are uploaded
    lead = LeadORM(
        agency_id=agency.id,
        name="João Silva",
        phone="+55 11 99999-9999",
        email="joao@email.com",
        interest_type="locacao",
        income_range="R$ 8.000 - R$ 10.000",
        desired_move_in_date=date(2026, 7, 10),
        marital_status="Solteiro",
        occupation="Analista de Produto",
        cpf=None,
        rg=None,
        birth_date=date(1993, 4, 12),
        address_extracted=None,
        income_extracted=None,
    )
    session.add(lead)

    # --- Mock Property (Vila Madalena from mock_data.py) ---
    prop = PropertyORM(
        agency_id=agency.id,
        title="Apartamento 2 quartos na Vila Madalena",
        address="Rua Harmonia, 123",
        neighborhood="Vila Madalena",
        city="São Paulo",
        rent=2700,
        condo_fee=520,
        iptu=110,
        bedrooms=2,
        parking_spots=1,
        accepts_pet=True,
        status="available",
        owner_name="Maria Fernanda",
    )
    session.add(prop)

    # --- Document Templates ---
    # locacao_pf_caucao — 6 docs
    template_caucao = DocumentTemplateORM(
        agency_id=agency.id,
        slug="locacao_pf_caucao",
        name="Locação PF com caução",
        documents=[
            {"id": "doc_rg_cnh", "label": "RG ou CNH", "type": "rg_cnh", "status": "pending"},
            {"id": "doc_cpf", "label": "CPF", "type": "cpf", "status": "pending"},
            {"id": "doc_income", "label": "Comprovante de renda", "type": "comprovante_renda", "status": "pending"},
            {"id": "doc_address", "label": "Comprovante de residência", "type": "comprovante_residencia", "status": "pending"},
            {"id": "doc_marital", "label": "Estado civil", "type": "estado_civil", "status": "pending"},
            {"id": "doc_deposit", "label": "Comprovante de pagamento da caução", "type": "comprovante_caucao", "status": "pending"},
        ],
    )
    session.add(template_caucao)

    # locacao_pf_fiador — 5 docs
    template_fiador = DocumentTemplateORM(
        agency_id=agency.id,
        slug="locacao_pf_fiador",
        name="Locação PF com fiador",
        documents=[
            {"id": "doc_rg_cnh", "label": "RG ou CNH", "type": "rg_cnh", "status": "pending"},
            {"id": "doc_cpf", "label": "CPF", "type": "cpf", "status": "pending"},
            {"id": "doc_income", "label": "Comprovante de renda", "type": "comprovante_renda", "status": "pending"},
            {"id": "doc_address", "label": "Comprovante de residência", "type": "comprovante_residencia", "status": "pending"},
            {"id": "doc_marital", "label": "Estado civil", "type": "estado_civil", "status": "pending"},
        ],
    )
    session.add(template_fiador)

    # --- Default Guidelines ---
    guideline_proposal = GuidelineORM(
        agency_id=agency.id,
        feature="proposal_message",
        title="Diretrizes de mensagem de proposta",
        content=(
            "Ao enviar proposta via mensagem, use linguagem cordial e profissional. "
            "Inclua sempre: valor do aluguel, condomínio, IPTU, total mensal, tipo de garantia, prazo e data de entrada."
        ),
    )
    session.add(guideline_proposal)

    guideline_document = GuidelineORM(
        agency_id=agency.id,
        feature="document_request",
        title="Diretrizes de solicitação de documentos",
        content=(
            "Ao pedir documentos, seja específico sobre quais documentos faltam. "
            "Use tom cordial e não pressione o lead."
        ),
    )
    session.add(guideline_document)

    guideline_contract = GuidelineORM(
        agency_id=agency.id,
        feature="contract_message",
        title="Diretrizes de mensagem de contrato",
        content=(
            "Ao enviar contrato, informe que é uma minuta preliminar que requer revisão. "
            "Solicite que o lead analise com calma."
        ),
    )
    session.add(guideline_contract)

    # --- Mock Chat Messages ---
    await session.flush()  # get lead.id

    msg1 = ChatMessageORM(
        lead_id=lead.id,
        sender="broker",
        text="Oi João! O que achou da visita?",
    )
    session.add(msg1)

    msg2 = ChatMessageORM(
        lead_id=lead.id,
        sender="lead",
        text="Adorei! Acredito que, após ela, eu vá fechar com vocês mesmo.",
    )
    session.add(msg2)

    await session.commit()

    # Copy mock documents to uploads/ directory
    _UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    if _DATA_DIR.exists():
        for src_file in _DATA_DIR.iterdir():
            if src_file.is_file():
                dst = _UPLOADS_DIR / src_file.name
                if not dst.exists():
                    shutil.copy2(src_file, dst)
