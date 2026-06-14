"use client";

import { useState, useRef } from "react";
import {
  CheckCircle2,
  Clock,
  Copy,
  FileWarning,
  Link2,
  Loader2,
  MessageSquare,
  Minus,
  Paperclip,
  Send,
  Sparkles,
  Upload,
  XCircle,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { linkAttachment, updateDocStatus, generateMessage, uploadDocument, toggleDocOptional } from "@/lib/api";
import type { Deal, DealDocument, DocumentStatus, ChatMessage } from "@/types";
import { cn } from "@/lib/utils";
import { SendApprovalDialog } from "@/components/SendApprovalDialog";

const STATUS_LABELS: Record<DocumentStatus, string> = {
  pending: "Pendente",
  received: "Recebido",
  approved: "Aprovado",
  needs_resend: "Reenviar",
};

const STATUS_CONFIG: Record<
  DocumentStatus,
  { color: string; icon: typeof Clock }
> = {
  pending: {
    color: "bg-amber-50 text-amber-700 ring-amber-200/60",
    icon: Clock,
  },
  received: {
    color: "bg-blue-50 text-blue-700 ring-blue-200/60",
    icon: Paperclip,
  },
  approved: {
    color: "bg-emerald-50 text-emerald-700 ring-emerald-200/60",
    icon: CheckCircle2,
  },
  needs_resend: {
    color: "bg-red-50 text-red-700 ring-red-200/60",
    icon: XCircle,
  },
};

interface Props {
  deal: Deal;
  onUpdateDeal: (deal: Deal) => void;
  refreshDeal: () => Promise<void>;
  onSendInChat?: (fileName: string, text: string) => void;
  leadName?: string;
  messages?: ChatMessage[];
}

export function DocumentChecklist({ deal, onUpdateDeal, onSendInChat, leadName = "lead", messages = [] }: Props) {
  const chatAttachments = messages
    .filter((m) => m.sender === "lead" && m.attachments && m.attachments.length > 0)
    .flatMap((m) => m.attachments.map((att) => ({ id: att.id, file_name: att.file_name })));
  const [generatedMessage, setGeneratedMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [extractedFields, setExtractedFields] = useState<Record<string, string>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);
  const docFileInputRef = useRef<HTMLInputElement>(null);
  const [uploadTargetDocId, setUploadTargetDocId] = useState("");
  const [approvalOpen, setApprovalOpen] = useState(false);

  const handleFileUpload = async (file: File, documentId = "") => {
    setUploading(true);
    try {
      const result = await uploadDocument(deal.id, file, documentId);
      onUpdateDeal(result.deal);
      setExtractedFields((prev) => ({ ...prev, ...result.extracted_fields }));
    } catch (err) {
      console.error("Failed to upload document:", err);
    } finally {
      setUploading(false);
    }
  };

  const handleGeneralUpload = () => {
    setUploadTargetDocId("");
    fileInputRef.current?.click();
  };

  const handleDocUpload = (docId: string) => {
    setUploadTargetDocId(docId);
    docFileInputRef.current?.click();
  };

  const handleLinkAttachment = async (docId: string, attachmentId: string) => {
    try {
      const updated = await linkAttachment(deal.id, docId, attachmentId);
      onUpdateDeal(updated);
    } catch (err) {
      console.error("Failed to link attachment:", err);
    }
  };

  const handleStatusChange = async (docId: string, status: DocumentStatus) => {
    try {
      const updated = await updateDocStatus(deal.id, docId, status);
      onUpdateDeal(updated);
    } catch (err) {
      console.error("Failed to update status:", err);
    }
  };

  const handleToggleOptional = async (docId: string) => {
    try {
      const updated = await toggleDocOptional(deal.id, docId);
      onUpdateDeal(updated);
    } catch (err) {
      console.error("Failed to toggle optional:", err);
    }
  };

  const handleRequestDocs = async () => {
    setLoading(true);
    try {
      const res = await generateMessage(deal.id, "request_missing_documents");
      setGeneratedMessage(res.text);
      setApprovalOpen(true);
    } catch (err) {
      console.error("Failed to generate message:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmSend = () => {
    if (onSendInChat && generatedMessage) {
      onSendInChat("", generatedMessage);
    }
  };

  const pendingCount = deal.documents.filter(
    (d) => d.status === "pending" && !d.is_optional
  ).length;
  const receivedCount = deal.documents.filter(
    (d) => d.status === "received" || d.status === "approved"
  ).length;
  const progress = Math.round(
    (receivedCount / Math.max(deal.documents.length, 1)) * 100
  );

  return (
    <div className="space-y-4">
      {/* Hidden file inputs */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileUpload(file, "");
          e.target.value = "";
        }}
      />
      <input
        ref={docFileInputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFileUpload(file, uploadTargetDocId);
          e.target.value = "";
        }}
      />

      {/* Upload button */}
      <Button
        onClick={handleGeneralUpload}
        disabled={uploading}
        className="w-full"
        variant="secondary"
      >
        {uploading ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            IA analisando documento...
          </>
        ) : (
          <>
            <Upload className="size-4" />
            Enviar documento do lead (IA le automaticamente)
          </>
        )}
      </Button>

      {/* Extracted fields */}
      {Object.keys(extractedFields).length > 0 && (
        <div className="rounded-xl bg-blue-50 p-4 ring-1 ring-blue-200/60 dark:bg-blue-950/30 dark:ring-blue-800/40">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-blue-800 dark:text-blue-200">
            <Sparkles className="size-3.5" />
            Dados extraidos pela IA
          </p>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {Object.entries(extractedFields)
              .filter(([k, v]) => v && k !== "document_type")
              .map(([key, value]) => (
                <div key={key}>
                  <span className="text-blue-600 dark:text-blue-400">{fieldLabel(key)}:</span>{" "}
                  <span className="font-medium">{value}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Progress card */}
      <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Progresso dos documentos</span>
          <span className="text-xs text-muted-foreground">
            {receivedCount} de {deal.documents.length}
          </span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-muted">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="mt-2 flex gap-3 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1">
            <span className="size-2 rounded-full bg-emerald-500" />
            {receivedCount} recebidos
          </span>
          <span className="inline-flex items-center gap-1">
            <span className="size-2 rounded-full bg-amber-500" />
            {pendingCount} pendentes
          </span>
        </div>
      </div>

      {/* Document list */}
      <div className="space-y-2">
        {deal.documents.map((doc: DealDocument) => {
          const isOptional = doc.is_optional;
          const config = STATUS_CONFIG[doc.status];
          const StatusIcon = config.icon;

          return (
            <div
              key={doc.id}
              className={cn(
                "rounded-xl bg-card p-3.5 ring-1 ring-border/60 transition-shadow hover:shadow-sm",
                isOptional && "opacity-70"
              )}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0 flex-1">
                  <div
                    className={cn(
                      "flex size-8 shrink-0 items-center justify-center rounded-lg ring-1",
                      isOptional
                        ? "bg-muted text-muted-foreground ring-border/40"
                        : config.color
                    )}
                  >
                    <StatusIcon className="size-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-tight">
                      {doc.label}
                    </p>
                    {isOptional && doc.status === "pending" ? (
                      <Badge
                        className="mt-1.5 border-0 text-[10px] font-medium ring-1 bg-muted text-muted-foreground ring-border/40"
                      >
                        Opcional
                      </Badge>
                    ) : (
                      <Badge
                        className={cn(
                          "mt-1.5 border-0 text-[10px] font-medium ring-1",
                          config.color
                        )}
                      >
                        {STATUS_LABELS[doc.status]}
                      </Badge>
                    )}
                  </div>
                </div>

                <div className="flex shrink-0 items-center gap-2">
                  <Button
                    size="xs"
                    variant="ghost"
                    className={cn(
                      "text-[10px] h-6 px-1.5",
                      isOptional
                        ? "text-muted-foreground hover:text-foreground"
                        : "text-muted-foreground/60 hover:text-muted-foreground"
                    )}
                    onClick={() => handleToggleOptional(doc.id)}
                    title={isOptional ? "Marcar como obrigatório" : "Marcar como opcional"}
                  >
                    <Minus className="size-3" />
                    {isOptional ? "Obrig." : "Opcional"}
                  </Button>

                  {doc.status === "pending" && (
                    <div className="flex gap-1">
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => handleDocUpload(doc.id)}
                        disabled={uploading}
                      >
                        <Upload className="size-3" />
                        Upload
                      </Button>
                      <Select
                        onValueChange={(val) =>
                          handleLinkAttachment(doc.id, val)
                        }
                      >
                        <SelectTrigger className="h-7 w-[120px] text-xs">
                          <Link2 className="size-3 mr-1 text-muted-foreground" />
                          <SelectValue placeholder="Vincular" />
                        </SelectTrigger>
                        <SelectContent>
                          {chatAttachments.map((att) => (
                            <SelectItem key={att.id} value={att.id}>
                              {att.file_name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}

                  {doc.status === "received" && (
                    <div className="flex gap-1">
                      <Button
                        size="xs"
                        variant="outline"
                        className="text-emerald-700 hover:bg-emerald-50 hover:text-emerald-800"
                        onClick={() => handleStatusChange(doc.id, "approved")}
                      >
                        <CheckCircle2 className="size-3" />
                        Aprovar
                      </Button>
                      <Button
                        size="xs"
                        variant="outline"
                        className="text-red-600 hover:bg-red-50 hover:text-red-700"
                        onClick={() =>
                          handleStatusChange(doc.id, "needs_resend")
                        }
                      >
                        <FileWarning className="size-3" />
                        Reenviar
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {pendingCount > 0 && (
        <Button
          onClick={handleRequestDocs}
          disabled={loading}
          className="w-full"
          variant="outline"
        >
          {loading ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Gerando mensagem...
            </>
          ) : (
            <>
              <MessageSquare className="size-4" />
              Pedir documentos faltantes
            </>
          )}
        </Button>
      )}

      {generatedMessage && !approvalOpen && (
        <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
            <MessageSquare className="size-3.5" />
            Mensagem gerada
          </p>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {generatedMessage}
          </p>
          <div className="mt-3 flex gap-2">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigator.clipboard.writeText(generatedMessage)}
            >
              <Copy className="size-3.5" />
              Copiar
            </Button>
            {onSendInChat && (
              <Button
                size="sm"
                variant="default"
                onClick={() => setApprovalOpen(true)}
              >
                <Send className="size-3.5" />
                Enviar no chat
              </Button>
            )}
          </div>
        </div>
      )}

      <SendApprovalDialog
        open={approvalOpen}
        onClose={() => setApprovalOpen(false)}
        onConfirm={handleConfirmSend}
        leadName={leadName}
        message={generatedMessage}
      />
    </div>
  );
}

function fieldLabel(key: string): string {
  const labels: Record<string, string> = {
    full_name: "Nome",
    cpf: "CPF",
    rg: "RG",
    birth_date: "Nascimento",
    marital_status: "Estado civil",
    occupation: "Profissao",
    address: "Endereco",
    income: "Renda",
    email: "E-mail",
    phone: "Telefone",
  };
  return labels[key] || key;
}
