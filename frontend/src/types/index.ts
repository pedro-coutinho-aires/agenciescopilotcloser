export type DocumentType =
  | "rg_cnh"
  | "cpf"
  | "comprovante_renda"
  | "comprovante_residencia"
  | "estado_civil"
  | "comprovante_caucao";

export type DocumentStatus = "pending" | "received" | "approved" | "needs_resend";

export type DealStage =
  | "negotiation"
  | "documents_pending"
  | "proposal_ready"
  | "contract_draft_ready"
  | "waiting_approval"
  | "closed"
  | "lost";

export type GuaranteeType = "caucao" | "fiador" | "seguro_fianca";

export type MessagePurpose =
  | "request_missing_documents"
  | "confirm_proposal"
  | "explain_next_steps"
  | "follow_up_pending";

export interface Lead {
  id: string;
  name: string;
  phone: string;
  email?: string;
  interest_type: string;
  income_range?: string;
  desired_move_in_date?: string;
  marital_status?: string;
  occupation?: string;
}

export interface Property {
  id: string;
  title: string;
  address: string;
  neighborhood: string;
  city: string;
  rent: number;
  condo_fee: number;
  iptu: number;
  bedrooms: number;
  parking_spots: number;
  accepts_pet: boolean;
  status: string;
  owner_name?: string;
}

export interface Attachment {
  id: string;
  file_name: string;
  mime_type: string;
  mock_document_type?: DocumentType;
  url?: string;
}

export interface ChatMessage {
  id: string;
  sender: "lead" | "lais" | "broker";
  text: string;
  created_at: string;
  attachments: Attachment[];
}

export interface DealDocument {
  id: string;
  label: string;
  type: DocumentType;
  status: DocumentStatus;
  attachment_id?: string;
  notes?: string;
  is_optional?: boolean;
}

export interface Proposal {
  id: string;
  deal_id: string;
  rent: number;
  condo_fee: number;
  iptu: number;
  guarantee_type: GuaranteeType;
  deposit_months?: number;
  move_in_date: string;
  contract_duration_months: number;
  special_conditions?: string;
  generated_text: string;
  status: string;
}

export interface ContractDraft {
  id: string;
  deal_id: string;
  template_id: string;
  generated_text: string;
  missing_fields: string[];
  status: string;
}

export interface Deal {
  id: string;
  lead_id: string;
  property_id: string;
  type: string;
  stage: DealStage;
  document_template_id: string;
  documents: DealDocument[];
  proposal?: Proposal;
  contract_draft?: ContractDraft;
  pending_actions: string[];
  created_at: string;
  updated_at: string;
}

export interface GeneratedTextResponse {
  text: string;
  warnings: string[];
}

export interface ProcessedDocument {
  id: string;
  file_name: string;
  mime_type: string;
  document_type: string;
  document_resume: string;
  document_html: string;
  extracted_fields: Record<string, string>;
}

export interface DocumentProcessResult {
  attachment: Attachment;
  analysis: ProcessedDocument;
  updated_lead_fields: Record<string, string>;
  suggested_response: string;
}

export interface TemplateInfo {
  id: string;
  slug: string;
  name: string;
  has_html_template: boolean;
  type?: string;
}
