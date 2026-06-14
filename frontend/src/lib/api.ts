const API_BASE = "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API error");
  }
  return res.json();
}

// Mock data
export function getMockData() {
  return request<{
    lead: import("@/types").Lead;
    property: import("@/types").Property;
    messages: import("@/types").ChatMessage[];
    document_templates: Record<string, { id: string; name: string }>;
  }>("/mock-data");
}

// Deal
export function createDeal(lead_id: string, property_id: string, document_template_id = "locacao_pf_caucao") {
  return request<import("@/types").Deal>("/deal", {
    method: "POST",
    body: JSON.stringify({ lead_id, property_id, document_template_id }),
  });
}

export function getDeal(deal_id: string) {
  return request<import("@/types").Deal>(`/deal/${deal_id}`);
}

export function linkAttachment(deal_id: string, document_id: string, attachment_id: string) {
  return request<import("@/types").Deal>(`/deal/${deal_id}/link-attachment`, {
    method: "PATCH",
    body: JSON.stringify({ document_id, attachment_id }),
  });
}

export function updateDocStatus(deal_id: string, document_id: string, status: string) {
  return request<import("@/types").Deal>(`/deal/${deal_id}/update-doc-status`, {
    method: "PATCH",
    body: JSON.stringify({ document_id, status }),
  });
}

export function toggleDocOptional(dealId: string, documentId: string) {
  return request<import("@/types").Deal>(`/deal/${dealId}/toggle-doc-optional`, {
    method: "PATCH",
    body: JSON.stringify({ document_id: documentId }),
  });
}

// Generate
export function generateProposal(params: {
  deal_id: string;
  rent?: number;
  condo_fee?: number;
  iptu?: number;
  guarantee_type?: string;
  deposit_months?: number;
  move_in_date?: string;
  contract_duration_months?: number;
  special_conditions?: string;
  template_name?: string;
}) {
  return request<import("@/types").GeneratedTextResponse>("/generate/proposal", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export function generateContract(deal_id: string, template_name = "") {
  return request<import("@/types").GeneratedTextResponse>("/generate/contract", {
    method: "POST",
    body: JSON.stringify({ deal_id, template_name }),
  });
}

export function generateMessage(deal_id: string, purpose: string) {
  return request<import("@/types").GeneratedTextResponse>("/generate/message", {
    method: "POST",
    body: JSON.stringify({ deal_id, purpose }),
  });
}

export function generateSummary(deal_id: string) {
  return request<import("@/types").GeneratedTextResponse>("/generate/summary", {
    method: "POST",
    body: JSON.stringify({ deal_id }),
  });
}

// PDF downloads
export function getProposalPdfUrl(deal_id: string) {
  return `${API_BASE}/generate/proposal/pdf/${deal_id}`;
}

export function getContractPdfUrl(deal_id: string) {
  return `${API_BASE}/generate/contract/pdf/${deal_id}`;
}

// Send contract for digital signing
export function sendForSigning(deal_id: string, signerInfo?: { lead_email?: string; lead_phone?: string; owner_email?: string }) {
  return request<{
    success: boolean;
    provider: string;
    document_id: string;
    signing_url: string;
    status: string;
    error: string;
  }>(`/generate/contract/sign/${deal_id}`, {
    method: "POST",
    body: JSON.stringify(signerInfo || {}),
  });
}

// Upload document for AI reading
export async function uploadDocument(
  deal_id: string,
  file: File,
  document_id = ""
): Promise<{ extracted_fields: Record<string, string>; deal: import("@/types").Deal }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("document_id", document_id);

  const res = await fetch(`${API_BASE}/deal/${deal_id}/read-document`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "Upload failed");
  }
  return res.json();
}

// Get extracted fields
export function getExtractedFields(deal_id: string) {
  return request<Record<string, string>>(`/deal/${deal_id}/extracted-fields`);
}

// Document processing
export async function processDocument(file: File, dealId?: string, leadId?: string): Promise<import("@/types").DocumentProcessResult> {
  const formData = new FormData();
  formData.append("file", file);
  if (dealId) formData.append("deal_id", dealId);
  if (leadId) formData.append("lead_id", leadId);

  const res = await fetch(`${API_BASE}/documents/process`, { method: "POST", body: formData });
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail); }
  return res.json();
}

export function getDocumentDownloadUrl(attachmentId: string) {
  return `${API_BASE}/documents/${attachmentId}/download`;
}

export function getDocumentAnalysis(attachmentId: string) {
  return request<import("@/types").ProcessedDocument>(`/documents/${attachmentId}/analysis`);
}

// Templates
export function getTemplates() {
  return request<import("@/types").TemplateInfo[]>("/templates");
}

export async function generateTemplate(file: File, name: string, type: string): Promise<{ id: string; slug: string; name: string; html_template: string }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name);
  formData.append("type", type);
  const res = await fetch(`${API_BASE}/templates/generate`, { method: "POST", body: formData });
  if (!res.ok) { const e = await res.json().catch(() => ({ detail: res.statusText })); throw new Error(e.detail); }
  return res.json();
}

export function previewTemplate(templateId: string) {
  return request<{ html: string }>(`/templates/${templateId}/preview`);
}

// Guidelines
export function getGuidelines(feature?: string) {
  const query = feature ? `?feature=${feature}` : "";
  return request<Array<{ id: string; feature: string; title: string; content: string }>>(`/guidelines${query}`);
}

export function updateGuideline(id: string, content: string) {
  return request<{ id: string; feature: string; title: string; content: string }>(`/guidelines/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ content }),
  });
}

// Lead update
export function updateLead(leadId: string, fields: Record<string, unknown>) {
  return request<import("@/types").Lead>(`/lead/${leadId}`, { method: "PATCH", body: JSON.stringify(fields) });
}

// Chat simulation
export function simulateLeadChat(params: {
  deal_id?: string;
  messages: import("@/types").ChatMessage[];
  lead: import("@/types").Lead;
  property: import("@/types").Property;
}) {
  return request<import("@/types").GeneratedTextResponse & {
    send_documents?: Array<{ filename: string; filepath: string }>;
  }>("/chat/simulate", {
    method: "POST",
    body: JSON.stringify(params),
  });
}
