"""Read PDF/PNG documents using Claude Vision API and extract lead fields."""

import base64
import json
import logging
from typing import Optional
from pydantic import BaseModel
from services.llm_service import llm

logger = logging.getLogger(__name__)


class ExtractedLeadFields(BaseModel):
    """Fields extracted from a document."""
    full_name: Optional[str] = None
    cpf: Optional[str] = None
    rg: Optional[str] = None
    birth_date: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    address: Optional[str] = None
    income: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    document_type: Optional[str] = None  # what kind of document this is


EXTRACTION_SYSTEM_PROMPT = """Você é um assistente especializado em leitura de documentos para processos de locação imobiliária.

Analise o documento fornecido e extraia os seguintes campos, se disponíveis:
- full_name: nome completo
- cpf: número do CPF
- rg: número do RG
- birth_date: data de nascimento
- marital_status: estado civil
- occupation: profissão/ocupação
- address: endereço completo
- income: renda ou valor do salário
- email: e-mail
- phone: telefone
- document_type: tipo do documento (ex: "CNH", "RG", "Holerite", "Comprovante de residência", etc.)

Responda APENAS com um JSON válido contendo os campos encontrados.
Se um campo não estiver disponível no documento, use null.
Não invente dados. Extraia apenas o que está visível no documento.

Exemplo de resposta:
{"full_name": "João da Silva", "cpf": "123.456.789-00", "rg": null, "document_type": "CNH"}"""


def read_document_with_vision(
    file_content: bytes,
    mime_type: str,
    file_name: str = "",
) -> ExtractedLeadFields:
    """Use Claude Vision to read a document and extract lead fields.

    Supports: image/png, image/jpeg, application/pdf
    """
    if not llm._anthropic_client:
        logger.warning("No Anthropic client available for vision")
        return ExtractedLeadFields(document_type=_guess_doc_type(file_name))

    b64_content = base64.standard_b64encode(file_content).decode("utf-8")

    # Build the content block based on mime type
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
        logger.warning(f"Unsupported mime type: {mime_type}")
        return ExtractedLeadFields(document_type=_guess_doc_type(file_name))

    try:
        response = llm._anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        content_block,
                        {
                            "type": "text",
                            "text": f"Extraia os dados deste documento ({file_name}). Responda apenas com JSON.",
                        },
                    ],
                }
            ],
        )

        raw_text = response.content[0].text.strip()
        # Extract JSON from response (handle markdown code blocks)
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        data = json.loads(raw_text)
        return ExtractedLeadFields(**data)

    except Exception as e:
        logger.error(f"Vision API failed: {e}")
        return ExtractedLeadFields(document_type=_guess_doc_type(file_name))


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
    return "Documento"
