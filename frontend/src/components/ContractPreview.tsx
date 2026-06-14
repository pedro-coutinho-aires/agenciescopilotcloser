"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  Copy,
  Download,
  FileText,
  FileWarning,
  Loader2,
  Mail,
  PenTool,
  ScrollText,
  Send,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { generateContract, getContractPdfUrl, sendForSigning, getTemplates } from "@/lib/api";
import type { Deal, TemplateInfo } from "@/types";
import { TemplateUploader } from "@/components/TemplateUploader";
import { SendApprovalDialog } from "@/components/SendApprovalDialog";

interface Props {
  deal: Deal;
  refreshDeal: () => Promise<void>;
  onSendInChat?: (fileName: string, text: string) => void;
  leadName?: string;
}

export function ContractPreview({ deal, refreshDeal, onSendInChat, leadName = "lead" }: Props) {
  const [generatedText, setGeneratedText] = useState(
    deal.contract_draft?.generated_text || ""
  );
  const [missingFields, setMissingFields] = useState<string[]>(
    deal.contract_draft?.missing_fields || []
  );
  const [loading, setLoading] = useState(false);
  const [signingStatus, setSigningStatus] = useState<{
    success?: boolean;
    url?: string;
    error?: string;
  }>({});
  const [sendingForSign, setSendingForSign] = useState(false);
  const [signerEmail, setSignerEmail] = useState("");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [showSignForm, setShowSignForm] = useState(false);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplateSlug, setSelectedTemplateSlug] = useState<string>("");
  const [approvalOpen, setApprovalOpen] = useState(false);
  const [approvalMessage, setApprovalMessage] = useState("");

  useEffect(() => {
    getTemplates()
      .then((list) => {
        setTemplates(list);
      })
      .catch(() => {
        // Templates endpoint may not exist yet — ignore
      });
  }, []);

  const handleGenerate = async () => {
    if (!deal.proposal) return;
    setLoading(true);
    try {
      const res = await generateContract(deal.id, selectedTemplateSlug || undefined);
      setGeneratedText(res.text);
      await refreshDeal();
    } catch (err) {
      console.error("Failed to generate contract:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = () => {
    window.open(getContractPdfUrl(deal.id), "_blank");
  };

  const handleSendInChatClick = () => {
    const msg =
      "Segue o contrato de locacao para sua analise. Por favor, revise e nos avise se esta de acordo.";
    setApprovalMessage(msg);
    setApprovalOpen(true);
  };

  const handleConfirmSend = () => {
    if (onSendInChat) {
      onSendInChat(`contrato_${deal.id}.pdf`, approvalMessage);
    }
  };

  const handleSendForSigning = async () => {
    if (!signerEmail) {
      setShowSignForm(true);
      return;
    }
    setSendingForSign(true);
    try {
      const result = await sendForSigning(deal.id, {
        lead_email: signerEmail,
        owner_email: ownerEmail,
      });
      setSigningStatus({
        success: result.success,
        url: result.signing_url,
        error: result.error,
      });
      if (result.success) setShowSignForm(false);
    } catch (err) {
      setSigningStatus({
        success: false,
        error: err instanceof Error ? err.message : "Erro ao enviar para assinatura",
      });
    } finally {
      setSendingForSign(false);
    }
  };

  if (!deal.proposal) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl bg-muted/40 p-8 text-center ring-1 ring-border/50">
        <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-muted">
          <FileWarning className="size-6 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium">Proposta necessaria</p>
        <p className="mt-1 max-w-xs text-xs text-muted-foreground">
          Gere uma proposta primeiro antes de criar a minuta contratual.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Template selector */}
      <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50 space-y-3">
        <h3 className="flex items-center gap-2 text-sm font-medium">
          <FileText className="size-4 text-primary" />
          Template de contrato
        </h3>
        {templates.length > 0 && (
          <Select value={selectedTemplateSlug} onValueChange={setSelectedTemplateSlug}>
            <SelectTrigger className="bg-card">
              <SelectValue placeholder="Selecionar template..." />
            </SelectTrigger>
            <SelectContent>
              {templates.map((t) => (
                <SelectItem key={t.id} value={t.slug}>
                  {t.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
        <TemplateUploader
          type="contract"
          onTemplateGenerated={() => {
            getTemplates()
              .then(setTemplates)
              .catch(() => {});
          }}
        />
      </div>

      <Button onClick={handleGenerate} disabled={loading} className="w-full">
        {loading ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Gerando minuta...
          </>
        ) : (
          <>
            <Sparkles className="size-4" />
            {generatedText ? "Regenerar Minuta" : "Gerar Minuta Preliminar"}
          </>
        )}
      </Button>

      {generatedText && (
        <>
          {missingFields.length > 0 && (
            <div className="rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200/60 dark:bg-amber-950/30 dark:ring-amber-800/40">
              <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-amber-800 dark:text-amber-200">
                <AlertTriangle className="size-3.5" />
                Campos pendentes de preenchimento
              </p>
              <div className="flex flex-wrap gap-1.5">
                {missingFields.map((field) => (
                  <Badge
                    key={field}
                    className="border-0 bg-amber-100 text-amber-900 text-[10px] ring-1 ring-amber-200/60"
                  >
                    {field}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-xl bg-card p-4 ring-1 ring-border/60">
            <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
              <ScrollText className="size-4 text-primary" />
              Minuta Preliminar
            </h3>
            <div className="max-h-[400px] overflow-y-auto rounded-lg bg-muted/30 p-4">
              <pre className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                {generatedText}
              </pre>
            </div>

            {/* Action buttons */}
            <div className="mt-4 space-y-3">
              <p className="text-xs font-medium text-muted-foreground">
                Enviar contrato:
              </p>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="default" onClick={handleSendInChatClick}>
                  <Send className="size-3.5" />
                  Enviar no chat
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={handleDownloadPdf}
                >
                  <Download className="size-3.5" />
                  Baixar PDF
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    if (signerEmail) handleSendForSigning();
                    else setShowSignForm(!showSignForm);
                  }}
                  disabled={sendingForSign}
                >
                  {sendingForSign ? (
                    <Loader2 className="size-3.5 animate-spin" />
                  ) : (
                    <PenTool className="size-3.5" />
                  )}
                  Enviar para assinatura
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() =>
                    navigator.clipboard.writeText(generatedText)
                  }
                >
                  <Copy className="size-3.5" />
                  Copiar
                </Button>
              </div>

              {/* Signing form */}
              {showSignForm && (
                <div className="rounded-lg bg-muted/40 p-3 space-y-2 ring-1 ring-border/50">
                  <p className="text-xs font-medium flex items-center gap-1.5">
                    <Mail className="size-3.5" />
                    Dados para assinatura digital
                  </p>
                  <div className="space-y-1.5">
                    <Input
                      type="email"
                      placeholder="E-mail do locatário *"
                      value={signerEmail}
                      onChange={(e) => setSignerEmail(e.target.value)}
                      className="h-8 text-xs bg-card"
                    />
                    <Input
                      type="email"
                      placeholder="E-mail do proprietário (opcional)"
                      value={ownerEmail}
                      onChange={(e) => setOwnerEmail(e.target.value)}
                      className="h-8 text-xs bg-card"
                    />
                  </div>
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={handleSendForSigning}
                    disabled={sendingForSign || !signerEmail}
                  >
                    {sendingForSign ? (
                      <>
                        <Loader2 className="size-3.5 animate-spin" />
                        Enviando...
                      </>
                    ) : (
                      <>
                        <PenTool className="size-3.5" />
                        Confirmar e enviar para assinatura
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          </div>

          {/* Signing status */}
          {signingStatus.success !== undefined && (
            <div
              className={`rounded-xl p-4 ring-1 ${
                signingStatus.success
                  ? "bg-emerald-50 ring-emerald-200/60 dark:bg-emerald-950/30"
                  : "bg-red-50 ring-red-200/60 dark:bg-red-950/30"
              }`}
            >
              {signingStatus.success ? (
                <div>
                  <p className="text-sm font-medium text-emerald-800 dark:text-emerald-200">
                    Contrato enviado para assinatura digital!
                  </p>
                  {signingStatus.url && (
                    <a
                      href={signingStatus.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 inline-block text-xs text-emerald-600 underline"
                    >
                      Acompanhar assinatura
                    </a>
                  )}
                </div>
              ) : (
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">
                    Erro ao enviar para assinatura
                  </p>
                  <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                    {signingStatus.error}
                  </p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      <SendApprovalDialog
        open={approvalOpen}
        onClose={() => setApprovalOpen(false)}
        onConfirm={handleConfirmSend}
        leadName={leadName}
        message={approvalMessage}
      />
    </div>
  );
}
