from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel


# --- Enums ---

class DocumentType(str, Enum):
    rg_cnh = "rg_cnh"
    cpf = "cpf"
    comprovante_renda = "comprovante_renda"
    comprovante_residencia = "comprovante_residencia"
    estado_civil = "estado_civil"
    comprovante_caucao = "comprovante_caucao"


class DocumentStatus(str, Enum):
    pending = "pending"
    received = "received"
    approved = "approved"
    needs_resend = "needs_resend"


class DealStage(str, Enum):
    negotiation = "negotiation"
    documents_pending = "documents_pending"
    proposal_ready = "proposal_ready"
    contract_draft_ready = "contract_draft_ready"
    waiting_approval = "waiting_approval"
    closed = "closed"
    lost = "lost"


class GuaranteeType(str, Enum):
    caucao = "caucao"
    fiador = "fiador"
    seguro_fianca = "seguro_fianca"


class ProposalStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    sent = "sent"


class ContractStatus(str, Enum):
    draft = "draft"
    ready_for_review = "ready_for_review"


class MessagePurpose(str, Enum):
    request_missing_documents = "request_missing_documents"
    confirm_proposal = "confirm_proposal"
    explain_next_steps = "explain_next_steps"
    follow_up_pending = "follow_up_pending"


# --- Core Entities ---

class Lead(BaseModel):
    id: str
    name: str
    phone: str
    email: Optional[str] = None
    interest_type: str = "locacao"
    income_range: Optional[str] = None
    desired_move_in_date: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None


class Property(BaseModel):
    id: str
    title: str
    address: str
    neighborhood: str
    city: str
    rent: float
    condo_fee: float
    iptu: float
    bedrooms: int
    parking_spots: int
    accepts_pet: bool
    status: str = "available"
    owner_name: Optional[str] = None


class Attachment(BaseModel):
    id: str
    file_name: str
    mime_type: str
    mock_document_type: Optional[DocumentType] = None
    url: Optional[str] = None


class ChatMessage(BaseModel):
    id: str
    sender: str  # "lead" | "lais" | "broker"
    text: str
    created_at: str
    attachments: list[Attachment] = []


class DealDocument(BaseModel):
    id: str
    label: str
    type: DocumentType
    status: DocumentStatus = DocumentStatus.pending
    attachment_id: Optional[str] = None
    notes: Optional[str] = None


class Proposal(BaseModel):
    id: str
    deal_id: str
    rent: float
    condo_fee: float
    iptu: float
    guarantee_type: GuaranteeType
    deposit_months: Optional[int] = None
    move_in_date: str
    contract_duration_months: int
    special_conditions: Optional[str] = None
    generated_text: str = ""
    status: ProposalStatus = ProposalStatus.draft


class ContractDraft(BaseModel):
    id: str
    deal_id: str
    template_id: str
    generated_text: str = ""
    missing_fields: list[str] = []
    status: ContractStatus = ContractStatus.draft


class Deal(BaseModel):
    id: str
    lead_id: str
    property_id: str
    type: str = "locacao"
    stage: DealStage = DealStage.negotiation
    document_template_id: str = "locacao_pf_caucao"
    documents: list[DealDocument] = []
    proposal: Optional[Proposal] = None
    contract_draft: Optional[ContractDraft] = None
    pending_actions: list[str] = []
    created_at: str = ""
    updated_at: str = ""


# --- Request/Response Models ---

class CreateDealRequest(BaseModel):
    lead_id: str
    property_id: str
    document_template_id: str = "locacao_pf_caucao"


class LinkAttachmentRequest(BaseModel):
    document_id: str
    attachment_id: str


class UpdateDocStatusRequest(BaseModel):
    document_id: str
    status: DocumentStatus


class GenerateProposalRequest(BaseModel):
    deal_id: str
    rent: Optional[float] = None
    condo_fee: Optional[float] = None
    iptu: Optional[float] = None
    guarantee_type: GuaranteeType = GuaranteeType.caucao
    deposit_months: int = 3
    move_in_date: str = ""
    contract_duration_months: int = 30
    special_conditions: Optional[str] = None
    template_name: str = ""


class GenerateContractRequest(BaseModel):
    deal_id: str
    template_name: str = ""


class GenerateMessageRequest(BaseModel):
    deal_id: str
    purpose: MessagePurpose


class GenerateSummaryRequest(BaseModel):
    deal_id: str


class SimulateChatRequest(BaseModel):
    deal_id: Optional[str] = None
    messages: list[ChatMessage]
    lead: Lead
    property: Property


class SendForSigningRequest(BaseModel):
    lead_email: str = ""
    lead_phone: str = ""
    owner_email: str = ""


class GeneratedTextResponse(BaseModel):
    text: str
    warnings: list[str] = []
