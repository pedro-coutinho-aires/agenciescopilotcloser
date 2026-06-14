"use client";

import { useState, useRef, useEffect, useMemo } from "react";
import {
  Building2,
  CircleDot,
  FileCheck,
  Loader2,
  Paperclip,
  Phone,
  Send,
  Sparkles,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { simulateLeadChat, processDocument, getDocumentAnalysis, getDocumentDownloadUrl, getContractPdfUrl, getProposalPdfUrl } from "@/lib/api";
import type { ChatMessage, Lead, Property, Deal, Attachment, ProcessedDocument } from "@/types";
import { cn } from "@/lib/utils";
import { DocumentPreviewModal } from "@/components/DocumentPreviewModal";

const CLOSING_TRIGGERS = [
  "quero fechar",
  "vamos fechar",
  "vá fechar",
  "va fechar",
  "gostei, quero",
  "quero alugar",
  "como faço para fechar",
  "quais os próximos passos",
  "pode reservar",
  "fechar com vocês",
  "fechar com voces",
];

function detectClosingIntent(messages: ChatMessage[]): boolean {
  return messages.some(
    (m) =>
      m.sender === "lead" &&
      CLOSING_TRIGGERS.some((t) => m.text.toLowerCase().includes(t))
  );
}

function formatTime(iso: string) {
  return new Date(iso).toLocaleTimeString("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ClientTime({ iso, className }: { iso: string; className?: string }) {
  const [time, setTime] = useState<string | null>(null);

  useEffect(() => {
    setTime(formatTime(iso));
  }, [iso]);

  return (
    <span className={className} suppressHydrationWarning>
      {time ?? "·"}
    </span>
  );
}

function getInitials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

interface Props {
  messages: ChatMessage[];
  setMessages: (msgs: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
  lead: Lead;
  property: Property;
  onOpenClosePanel: () => void;
  deal: Deal | null;
  panelOpen?: boolean;
  onLeadUpdated?: (lead: Lead) => void;
  refreshDeal?: () => Promise<void>;
}

export function ChatWindow({
  messages,
  setMessages,
  lead,
  property,
  onOpenClosePanel,
  deal,
  panelOpen = false,
  onLeadUpdated,
  refreshDeal,
}: Props) {
  const [input, setInput] = useState("");
  const [simulating, setSimulating] = useState(false);
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<ProcessedDocument | null>(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const hasIntent = useMemo(() => detectClosingIntent(messages), [messages]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const brokerMsg: ChatMessage = {
      id: `msg_${Date.now()}`,
      sender: "broker",
      text: input.trim(),
      created_at: new Date().toISOString(),
      attachments: [],
    };
    const updated = [...messages, brokerMsg];
    setMessages(updated);
    setInput("");

    setSimulating(true);
    try {
      const res = await simulateLeadChat({
        deal_id: deal?.id,
        messages: updated,
        lead,
        property,
      });
      const leadMsg: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        sender: "lead",
        text: res.text,
        created_at: new Date().toISOString(),
        attachments: [],
      };

      // If lead is sending documents, fetch and process all of them
      const sendDocs = (res as Record<string, unknown>).send_documents as Array<{ filename: string; filepath: string }> | undefined;
      if (sendDocs && sendDocs.length > 0) {
        const attachments = [];
        for (const sendDoc of sendDocs) {
          try {
            const docRes = await fetch(`http://localhost:8000/api/mock-docs/${sendDoc.filename}`);
            const blob = await docRes.blob();
            const file = new File([blob], sendDoc.filename, { type: blob.type });
            const result = await processDocument(file, deal?.id, lead.id);
            attachments.push(result.attachment);
            if (onLeadUpdated && Object.keys(result.updated_lead_fields).length > 0) {
              onLeadUpdated({ ...lead, ...result.updated_lead_fields } as Lead);
            }
          } catch {
            // Doc processing failed, still show the text
          }
        }
        leadMsg.attachments = attachments;
        if (refreshDeal) await refreshDeal();
      }

      setMessages([...updated, leadMsg]);
    } catch {
      console.error("Failed to simulate lead");
    } finally {
      setSimulating(false);
    }
  };

  const handleFileUpload = async (file: File) => {
    setUploadingDoc(true);
    try {
      const result = await processDocument(file, deal?.id, lead.id);

      // Create a lead message with the uploaded file as attachment
      const leadMsg: ChatMessage = {
        id: `msg_${Date.now()}`,
        sender: "lead",
        text: `[Documento enviado: ${file.name}]`,
        created_at: new Date().toISOString(),
        attachments: [result.attachment],
      };

      // Create an Agencies Copilot response with the suggested message
      const laisMsg: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        sender: "lais",
        text: result.suggested_response,
        created_at: new Date().toISOString(),
        attachments: [],
      };

      setMessages((prev) => [...prev, leadMsg, laisMsg]);

      // Notify parent of updated lead fields
      if (onLeadUpdated && Object.keys(result.updated_lead_fields).length > 0) {
        onLeadUpdated({ ...lead, ...result.updated_lead_fields } as Lead);
      }

      // Refresh deal after document processing
      if (refreshDeal) await refreshDeal();
    } catch (err) {
      console.error("Failed to process document:", err);
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleAttachmentClick = async (attachment: Attachment) => {
    // Handle contract/proposal PDFs (generated by the system, not uploaded)
    if (attachment.file_name.startsWith("contrato_") && attachment.file_name.endsWith(".pdf")) {
      const dealId = attachment.file_name.replace("contrato_", "").replace(".pdf", "");
      window.open(getContractPdfUrl(dealId), "_blank");
      return;
    }
    if (attachment.file_name.startsWith("proposta_") && attachment.file_name.endsWith(".pdf")) {
      const dealId = attachment.file_name.replace("proposta_", "").replace(".pdf", "");
      window.open(getProposalPdfUrl(dealId), "_blank");
      return;
    }
    // Regular document — show analysis modal
    try {
      const analysis = await getDocumentAnalysis(attachment.id);
      setPreviewDoc(analysis);
      setPreviewUrl(getDocumentDownloadUrl(attachment.id));
    } catch (err) {
      // If analysis fails, try direct download
      window.open(getDocumentDownloadUrl(attachment.id), "_blank");
    }
  };

  return (
    <div className="flex h-full min-h-0 flex-col bg-background">
      {/* Header */}
      <div className="border-b border-border bg-card px-5 py-4 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
            {getInitials(lead.name)}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <h2 className="truncate font-semibold text-base">{lead.name}</h2>
              <Badge
                variant="outline"
                className="shrink-0 gap-1 border-primary/20 bg-primary/5 text-primary text-[10px] font-medium"
              >
                <CircleDot className="size-2.5 fill-primary" />
                Ativo
              </Badge>
            </div>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1">
                <Phone className="size-3" />
                {lead.phone}
              </span>
              <span className="inline-flex items-center gap-1">
                <Building2 className="size-3" />
                {property.title}
              </span>
            </div>
          </div>
          {!panelOpen && (
            <Button
              size="sm"
              onClick={onOpenClosePanel}
              className="shrink-0 gap-1.5"
            >
              <FileCheck className="size-3.5" />
              Copilot Closer
            </Button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="min-h-0 flex-1 overflow-y-auto chat-pattern">
        <div className="space-y-4 p-5">
          {messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              leadName={lead.name}
              onAttachmentClick={handleAttachmentClick}
            />
          ))}
          {(simulating || uploadingDoc) && (
            <div className="flex w-full items-end gap-2">
              <Avatar initials={getInitials(lead.name)} variant="lead" />
              <div className="rounded-2xl rounded-bl-md bg-card px-4 py-3 shadow-sm ring-1 ring-border/60">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-3.5 animate-spin" />
                  <span>
                    {uploadingDoc
                      ? "Processando documento..."
                      : `${lead.name} está digitando...`}
                  </span>
                </div>
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>
      </div>

      {/* Intent CTA — only show once before deal is created */}
      {hasIntent && !deal && (
        <div className="border-t border-primary/20 bg-brand-muted px-5 py-3.5">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="flex size-8 items-center justify-center rounded-full bg-primary/15">
                <Sparkles className="size-4 text-primary" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">
                  Intencao de fechamento detectada
                </p>
                <p className="text-xs text-muted-foreground">
                  O lead demonstrou interesse em fechar o negocio
                </p>
              </div>
            </div>
            <Button size="sm" onClick={onOpenClosePanel} className="shrink-0">
              Abrir Copilot Closer
            </Button>
          </div>
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border bg-card p-4 shadow-[0_-4px_12px_-4px_rgba(0,0,0,0.05)]">
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,.docx"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFileUpload(file);
            e.target.value = "";
          }}
        />
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-2"
        >
          <Button
            type="button"
            variant="outline"
            size="icon"
            disabled={simulating || uploadingDoc}
            onClick={() => fileInputRef.current?.click()}
            className="size-10 shrink-0 rounded-xl"
            title="Enviar documento do lead"
          >
            <Paperclip className="size-4" />
          </Button>
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Digite uma mensagem..."
            disabled={simulating || uploadingDoc}
            className="h-10 rounded-xl bg-muted/40 border-transparent focus-visible:border-ring"
          />
          <Button
            type="submit"
            disabled={simulating || uploadingDoc || !input.trim()}
            size="icon"
            className="size-10 shrink-0 rounded-xl"
          >
            <Send className="size-4" />
          </Button>
        </form>
      </div>

      {/* Document Preview Modal */}
      <DocumentPreviewModal
        open={!!previewDoc}
        onClose={() => setPreviewDoc(null)}
        document={previewDoc}
        downloadUrl={previewUrl}
      />
    </div>
  );
}

function Avatar({
  initials,
  variant,
}: {
  initials: string;
  variant: "lead" | "broker" | "lais";
}) {
  return (
    <div
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold",
        variant === "lead" && "bg-muted text-muted-foreground",
        variant === "broker" && "gradient-brand text-brand-foreground",
        variant === "lais" && "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-200"
      )}
    >
      {variant === "lais" ? (
        <Sparkles className="size-3.5" />
      ) : variant === "broker" ? (
        <User className="size-3.5" />
      ) : (
        initials
      )}
    </div>
  );
}

function MessageBubble({
  message,
  leadName,
  onAttachmentClick,
}: {
  message: ChatMessage;
  leadName: string;
  onAttachmentClick: (attachment: Attachment) => void;
}) {
  const isLead = message.sender === "lead";
  const isBroker = message.sender === "broker";
  const isLais = message.sender === "lais";
  const isOutgoing = isBroker || isLais;

  const senderLabel = isLead ? leadName : isBroker ? "Voce" : "Agencies Copilot";
  const avatarVariant = isLead ? "lead" : isBroker ? "broker" : "lais";

  return (
    <div
      className={cn(
        "flex w-full items-end gap-2",
        isOutgoing ? "flex-row-reverse" : "flex-row"
      )}
    >
      <Avatar initials={getInitials(leadName)} variant={avatarVariant} />
      <div
        className={cn(
          "max-w-[72%] rounded-2xl px-4 py-2.5 shadow-sm",
          isLead && "rounded-bl-md bg-card ring-1 ring-border/60",
          isBroker && "rounded-br-md gradient-brand text-brand-foreground",
          isLais &&
            "rounded-br-md bg-blue-50 text-blue-900 ring-1 ring-blue-200/60 dark:bg-blue-950/50 dark:text-blue-100 dark:ring-blue-800/40"
        )}
      >
        <div
          className={cn(
            "mb-1 flex items-center gap-2",
            isOutgoing ? "justify-end" : "justify-start"
          )}
        >
          <p
            className={cn(
              "text-[11px] font-medium",
              isLead && "text-muted-foreground",
              isBroker && "text-brand-foreground/80",
              isLais && "text-blue-600 dark:text-blue-300"
            )}
          >
            {senderLabel}
          </p>
          <ClientTime
            iso={message.created_at}
            className={cn(
              "text-[10px]",
              isLead && "text-muted-foreground/60",
              isBroker && "text-brand-foreground/60",
              isLais && "text-blue-500/70 dark:text-blue-400/70"
            )}
          />
        </div>
        <p className="text-sm leading-relaxed whitespace-pre-wrap">
          {message.text}
        </p>
        {message.attachments.length > 0 && (
          <div
            className={cn(
              "mt-2 flex flex-wrap gap-1",
              isOutgoing && "justify-end"
            )}
          >
            {message.attachments.map((att: Attachment) => (
              <Badge
                key={att.id}
                variant="secondary"
                className="text-[10px] font-normal cursor-pointer hover:bg-primary/10 transition-colors"
                onClick={() => onAttachmentClick(att)}
              >
                {att.file_name}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
