"""3-stage LLM pipeline for document processing."""
from __future__ import annotations

import base64
import json
import logging
from typing import Optional

from services.llm_service import llm

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = [
    "CNH",
    "CPF",
    "Holerite",
    "Comprovante de residência",
    "Certidão de casamento",
    "Comprovante de pagamento",
    "RG",
    "Outro",
]

# ---------------------------------------------------------------------------
# Stage 1: analyze_document
# ---------------------------------------------------------------------------

ANALYSIS_SYSTEM_PROMPT = """Você é um assistente especializado em leitura de documentos para processos de locação imobiliária.

Analise o documento fornecido e retorne um JSON com os seguintes campos:

1. "document_type": tipo do documento. Deve ser um dos seguintes: CNH, CPF, Holerite, Comprovante de residência, Certidão de casamento, Comprovante de pagamento, RG, Outro.

2. "document_resume": resumo de 2 a 3 frases descrevendo o que o documento contém.

3. "document_html": uma representação HTML limpa e formatada do documento. Deve ser um card HTML estilizado inline (CSS inline) mostrando os principais dados extraídos de forma visualmente organizada. Use divs, tabelas simples, cores neutras e fontes legíveis. Não inclua <html>, <head> nem <body> — apenas o conteúdo do card.

4. "extracted_fields": dicionário com os campos extraídos. Inclua apenas os campos disponíveis no documento. Campos possíveis:
   - cpf: número do CPF
   - rg: número do RG
   - full_name: nome completo
   - birth_date: data de nascimento (formato YYYY-MM-DD se possível)
   - marital_status: estado civil
   - occupation: profissão/ocupação
   - address: endereço completo
   - income: renda ou valor do salário (string com o valor)
   - email: e-mail
   - phone: telefone
   - issuing_authority: órgão emissor (para RG/CNH)
   - expiry_date: data de validade (para CNH)
   - payment_amount: valor do pagamento (para comprovantes de pagamento)
   - payment_date: data do pagamento

Responda APENAS com um JSON válido. Não invente dados. Extraia apenas o que está visível no documento.

Exemplo de resposta:
{
  "document_type": "CNH",
  "document_resume": "CNH de João da Silva, válida até 2028. Contém CPF, RG e data de nascimento.",
  "document_html": "<div style='...'>...</div>",
  "extracted_fields": {"full_name": "João da Silva", "cpf": "123.456.789-00", "birth_date": "1990-05-15"}
}"""


def analyze_document(
    file_content: bytes,
    mime_type: str,
    file_name: str = "",
) -> dict:
    """Stage 1: Use Claude Vision to extract structured data from a document.

    Returns a dict with:
    - document_type: str
    - document_resume: str
    - document_html: str
    - extracted_fields: dict
    """
    if not llm._anthropic_client:
        logger.warning("No Anthropic client available for vision")
        return {
            "document_type": _guess_doc_type(file_name),
            "document_resume": "Documento enviado (análise indisponível).",
            "document_html": "<div>Documento recebido.</div>",
            "extracted_fields": {},
        }

    b64_content = base64.standard_b64encode(file_content).decode("utf-8")

    # Build content block based on mime type
    if mime_type == "application/pdf":
        content_block = {
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": b64_content,
            },
        }
    elif mime_type in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"):
        content_block = {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": mime_type,
                "data": b64_content,
            },
        }
    else:
        logger.warning(f"Unsupported mime type for vision: {mime_type}")
        return {
            "document_type": _guess_doc_type(file_name),
            "document_resume": "Tipo de arquivo não suportado para análise automática.",
            "document_html": "<div>Documento recebido.</div>",
            "extracted_fields": {},
        }

    try:
        response = llm._anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=ANALYSIS_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {
                            "type": "text",
                            "text": f"Analise este documento ({file_name}) e retorne o JSON conforme instruído.",
                        },
                    ],
                }
            ],
        )

        raw_text = response.content[0].text.strip()
        # Strip markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(raw_text)
        return {
            "document_type": data.get("document_type", _guess_doc_type(file_name)),
            "document_resume": data.get("document_resume", ""),
            "document_html": data.get("document_html", ""),
            "extracted_fields": data.get("extracted_fields", {}),
        }

    except Exception as e:
        logger.error(f"Vision API failed in analyze_document: {e}")
        return {
            "document_type": _guess_doc_type(file_name),
            "document_resume": "Erro ao analisar documento.",
            "document_html": "<div>Erro ao processar documento.</div>",
            "extracted_fields": {},
        }


# ---------------------------------------------------------------------------
# Stage 2: extract_lead_data
# ---------------------------------------------------------------------------

LEAD_EXTRACT_SYSTEM_PROMPT = """Você é um assistente que compara dados extraídos de documentos com o perfil atual de um lead imobiliário.

Dado:
1. Os campos extraídos do documento mais recente
2. Os dados atuais do lead
3. O histórico de análises anteriores

Determine quais campos do lead devem ser ATUALIZADOS com os dados do documento.
Retorne apenas os campos que devem ser atualizados (valores novos ou mais completos que os atuais).
Não atualize campos que já estão preenchidos com dados melhores.
Campos possíveis para atualização: cpf, rg, full_name (-> name), birth_date, marital_status, occupation, address_extracted, income_extracted, email, phone.

Regras:
- Prefira dados do documento sobre dados vazios/nulos do lead
- Se o lead já tem um CPF válido e o documento tem outro, sinalize no campo "conflict_warning" (string)
- birth_date deve ser formato YYYY-MM-DD
- Retorne APENAS um JSON com os campos a atualizar + opcionalmente "conflict_warning"

Exemplo de resposta:
{"cpf": "123.456.789-00", "rg": "12.345.678-9", "birth_date": "1990-05-15", "conflict_warning": null}"""


def extract_lead_data(
    analysis_result: dict,
    lead_current_data: dict,
    analysis_history: Optional[list] = None,
) -> dict:
    """Stage 2: Determine which lead fields to update based on document analysis.

    Returns a dict of fields to update on the lead.
    """
    extracted = analysis_result.get("extracted_fields", {})
    if not extracted:
        return {}

    history_summary = ""
    if analysis_history:
        history_summary = f"\n\nHistórico de documentos analisados: {json.dumps(analysis_history, ensure_ascii=False)}"

    user_prompt = f"""Campos extraídos do documento:
{json.dumps(extracted, ensure_ascii=False, indent=2)}

Dados atuais do lead:
{json.dumps(lead_current_data, ensure_ascii=False, indent=2)}
{history_summary}

Quais campos do lead devem ser atualizados? Retorne apenas o JSON com os campos a atualizar."""

    try:
        raw = llm.generate(LEAD_EXTRACT_SYSTEM_PROMPT, user_prompt, max_tokens=512)
        if not raw:
            return _simple_lead_update(extracted, lead_current_data)

        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        return json.loads(raw)

    except Exception as e:
        logger.error(f"extract_lead_data failed: {e}")
        return _simple_lead_update(extracted, lead_current_data)


def _simple_lead_update(extracted: dict, lead_current: dict) -> dict:
    """Fallback: simple field mapping without LLM."""
    updates = {}
    field_map = {
        "cpf": "cpf",
        "rg": "rg",
        "birth_date": "birth_date",
        "marital_status": "marital_status",
        "occupation": "occupation",
        "address": "address_extracted",
        "income": "income_extracted",
        "email": "email",
        "phone": "phone",
    }
    for doc_field, lead_field in field_map.items():
        if extracted.get(doc_field) and not lead_current.get(lead_field):
            updates[lead_field] = extracted[doc_field]
    return updates


# ---------------------------------------------------------------------------
# Stage 3: generate_contextual_response
# ---------------------------------------------------------------------------

RESPONSE_SYSTEM_PROMPT = """Você é Lais, copiloto de fechamento de uma imobiliária.
Gere uma resposta natural e amigável para o corretor enviar ao lead via WhatsApp, confirmando o recebimento do documento e informando o próximo passo.

A resposta deve:
- Confirmar o recebimento do documento (mencione o tipo)
- Mencionar quais campos foram preenchidos automaticamente (se houver)
- Informar quais documentos ainda faltam (se houver)
- Ser curta, direta e no tom de mensagem de WhatsApp
- Usar o primeiro nome do lead
- Não usar emojis em excesso (1-2 no máximo)

Retorne APENAS o texto da mensagem, sem explicações."""


def generate_contextual_response(
    lead: dict,
    deal: Optional[dict],
    analysis: dict,
) -> str:
    """Stage 3: Generate a natural broker response about the received document.

    Returns a string with the suggested WhatsApp message.
    """
    doc_type = analysis.get("document_type", "documento")
    extracted = analysis.get("extracted_fields", {})
    filled_fields = [k for k, v in extracted.items() if v]

    # Map field names to friendly labels
    field_labels = {
        "cpf": "CPF",
        "rg": "RG",
        "full_name": "nome completo",
        "birth_date": "data de nascimento",
        "marital_status": "estado civil",
        "occupation": "profissão",
        "address": "endereço",
        "income": "renda",
        "email": "e-mail",
        "phone": "telefone",
    }

    filled_labels = [field_labels.get(f, f) for f in filled_fields if f in field_labels]

    pending_docs: list = []
    if deal:
        docs = deal.get("documents", [])
        pending_docs = [d["label"] for d in docs if d.get("status") == "pending"]

    lead_name = (lead.get("name") or "").split()[0] if lead.get("name") else "cliente"

    user_prompt = f"""Lead: {lead_name}
Documento recebido: {doc_type}
Campos preenchidos automaticamente: {', '.join(filled_labels) if filled_labels else 'nenhum'}
Documentos ainda pendentes no checklist: {', '.join(pending_docs) if pending_docs else 'nenhum — checklist completo!'}

Gere a mensagem de WhatsApp do corretor para o lead."""

    try:
        response = llm.generate(RESPONSE_SYSTEM_PROMPT, user_prompt, max_tokens=256)
        if response:
            return response.strip()
    except Exception as e:
        logger.error(f"generate_contextual_response failed: {e}")

    # Fallback response
    if pending_docs:
        pending_str = ", ".join(pending_docs)
        return (
            f"Recebi sua {doc_type}, {lead_name}! "
            f"Ainda precisamos dos seguintes documentos: {pending_str}."
        )
    return f"Recebi sua {doc_type}, {lead_name}! Checklist completo, obrigado!"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _guess_doc_type(file_name: str) -> str:
    """Fallback: guess document type from filename."""
    name = file_name.lower()
    if "cnh" in name:
        return "CNH"
    if "rg" in name:
        return "RG"
    if "holerite" in name or "renda" in name:
        return "Holerite"
    if "residencia" in name or "endereco" in name:
        return "Comprovante de residência"
    if "cpf" in name:
        return "CPF"
    if "casamento" in name:
        return "Certidão de casamento"
    if "pagamento" in name or "caucao" in name:
        return "Comprovante de pagamento"
    return "Outro"
