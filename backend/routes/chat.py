import os
import random
from pathlib import Path
from fastapi import APIRouter, Depends

from models import SimulateChatRequest, GeneratedTextResponse
from services.llm_service import llm
from db.engine import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models import DealORM

router = APIRouter(tags=["chat"])

MOCK_DOCS_DIR = Path(__file__).parent.parent / "data" / "lead_mocked_docs"

# Map of document types to mock files the lead can "send"
AVAILABLE_DOCS = {
    "cnh": "cnh_joao_silva.png",
    "cpf": "cpf_joao_silva.png",
    "holerite": "holerite_joao_silva_liquido_5800.pdf",
    "residencia": "residencia_joao_silva.png",
    "certidao": "certidao_casamento_exemplo.pdf",
    "comprovante_pagamento": "comprovante_pagamento_5400_exemplo.pdf",
}


@router.post("/chat/simulate")
async def simulate_lead(req: SimulateChatRequest, db: AsyncSession = Depends(get_db)):
    """LLM simulates a lead response based on conversation context."""

    # Check if lead should send a document based on RECENT conversation context
    # Scan the last 5 broker/lais messages (not just the very last one)
    recent_broker_texts = []
    for m in reversed(req.messages[-10:] if req.messages else []):
        if m.sender in ("broker", "lais"):
            recent_broker_texts.append(m.text.lower())
            if len(recent_broker_texts) >= 5:
                break
    combined_broker_context = " ".join(recent_broker_texts)

    # Determine if broker is asking for documents
    docs_to_send = []
    already_sent = set()

    # Track which docs were already sent
    for m in req.messages:
        if m.sender == "lead" and m.attachments:
            for att in m.attachments:
                already_sent.add(att.file_name)

    # Check if broker asked for specific docs (in any recent message)
    doc_keywords = {
        "cnh": ["cnh", "identidade", "rg", "documento com foto"],
        "cpf": ["cpf"],
        "holerite": ["holerite", "renda", "comprovante de renda", "contracheque"],
        "residencia": ["residência", "residencia", "endereço", "endereco", "comprovante de residência"],
        "certidao": ["certidão", "certidao", "casamento", "estado civil"],
        "comprovante_pagamento": ["caução", "caucao", "pagamento", "depósito", "deposito"],
    }

    payment_blocked = False

    if any(kw in combined_broker_context for kws in doc_keywords.values() for kw in kws):
        for doc_type, keywords in doc_keywords.items():
            if any(kw in combined_broker_context for kw in keywords):
                # Payment doc requires contract to be signed/ready
                if doc_type == "comprovante_pagamento":
                    allowed_stages = ("contract_draft_ready", "waiting_approval", "closed")
                    deal_stage = None
                    if req.deal_id:
                        result = await db.execute(select(DealORM).where(DealORM.id == req.deal_id))
                        deal = result.scalar_one_or_none()
                        if deal:
                            deal_stage = deal.stage
                    if deal_stage not in allowed_stages:
                        payment_blocked = True
                        continue

                filename = AVAILABLE_DOCS[doc_type]
                if filename not in already_sent:
                    docs_to_send.append({"type": doc_type, "filename": filename})

    should_send_doc = len(docs_to_send) > 0

    system_prompt = f"""Você é {req.lead.name}, um lead real de imobiliária no WhatsApp.

Seus dados:
- Ocupação: {req.lead.occupation or 'não informado'}
- Renda: {req.lead.income_range or 'não informado'}
- Estado civil: {req.lead.marital_status or 'não informado'}
- Data desejada de mudança: {req.lead.desired_move_in_date or 'não informado'}

Imóvel:
- {req.property.title}
- R$ {req.property.rent:.0f} + R$ {req.property.condo_fee:.0f} cond.

REGRAS OBRIGATÓRIAS:
- Seja DIRETO e SECO. Mensagens de no máximo 1-2 frases.
- Use linguagem INFORMAL de WhatsApp (abreviações ok, sem formalidade).
- NÃO use saudações longas. Vá direto ao ponto.
- NÃO repita informações que já foram ditas.
- Se pedirem documentos, diga algo curto tipo "to mandando" ou "segue" ou "mando agora".
- Se receber proposta, reaja de forma realista (pode negociar, aceitar, ou pedir tempo).
- Se receber contrato, diga que vai analisar.
- NUNCA ofereça enviar documentos por conta própria. Só envie quando o corretor pedir ESPECIFICAMENTE um documento pelo nome.
- Exemplos de tom:
  "beleza, mando agora"
  "ok, segue aí"
  "show, vou ver"
  "pode ser, me dá um tempo pra analisar"
  "fechado"
  "quanto fica o total?"
"""

    if payment_blocked:
        system_prompt += """
IMPORTANTE: O corretor pediu o comprovante de pagamento, mas você ainda não assinou o contrato.
Diga algo natural como "mando o pagamento depois de assinar o contrato" ou "primeiro preciso ver o contrato antes de pagar".
NÃO envie o comprovante agora."""

    if should_send_doc:
        doc_types = ", ".join(d["type"] for d in docs_to_send)
        system_prompt += f"""
IMPORTANTE: Nesta resposta, você está ENVIANDO documento(s) ({doc_types}).
Diga algo curto como "segue meu/minha [tipo do doc]" ou "to mandando" ou "aí ó".
NÃO escreva mais que uma frase."""

    conversation = "\n".join(
        f"{'Você' if m.sender == 'lead' else 'Corretor'}: {m.text}"
        for m in req.messages[-10:]
    )

    user_prompt = f"Conversa:\n{conversation}\n\nSua resposta (CURTA, máximo 1-2 frases):"

    response = llm.generate(system_prompt, user_prompt, max_tokens=100)

    if not response:
        response = "ok, vou ver" if not should_send_doc else "segue aí"

    # Clean up
    for prefix in [f"{req.lead.name}:", "Lead:", "Você:", "João:", "João Silva:"]:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()

    # Remove quotes if wrapped
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]

    result = {"text": response, "warnings": []}

    # If sending docs, include attachment info as array
    if should_send_doc and docs_to_send:
        result["send_documents"] = [
            {
                "filename": doc["filename"],
                "filepath": str(MOCK_DOCS_DIR / doc["filename"]),
            }
            for doc in docs_to_send
        ]

    return result
