"use client";

import { useState, useEffect } from "react";
import {
  Calendar,
  Copy,
  Download,
  FileText,
  Loader2,
  Send,
  Settings,
  Shield,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { generateProposal, generateMessage, getProposalPdfUrl, getTemplates, getGuidelines, updateGuideline } from "@/lib/api";
import type { Deal, Lead, Property, GuaranteeType, TemplateInfo } from "@/types";
import { TemplateUploader } from "@/components/TemplateUploader";
import { SendApprovalDialog } from "@/components/SendApprovalDialog";

interface Props {
  deal: Deal;
  lead: Lead;
  property: Property;
  onUpdateDeal: (deal: Deal) => void;
  refreshDeal: () => Promise<void>;
  onSendInChat?: (fileName: string, text: string) => void;
}

function FormField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-medium text-muted-foreground">
        {label}
      </label>
      {children}
    </div>
  );
}

export function ProposalBuilder({
  deal,
  lead,
  property,
  refreshDeal,
  onSendInChat,
}: Props) {
  const [rent, setRent] = useState(property.rent.toString());
  const [condoFee, setCondoFee] = useState(property.condo_fee.toString());
  const [iptu, setIptu] = useState(property.iptu.toString());
  const [guaranteeType, setGuaranteeType] = useState<GuaranteeType>("caucao");
  const [depositMonths, setDepositMonths] = useState("3");
  const [moveInDate, setMoveInDate] = useState(
    lead.desired_move_in_date || ""
  );
  const [duration, setDuration] = useState("30");
  const [specialConditions, setSpecialConditions] = useState("");
  const [generatedText, setGeneratedText] = useState(
    deal.proposal?.generated_text || ""
  );
  const [loading, setLoading] = useState(false);
  const [confirmMessage, setConfirmMessage] = useState("");
  const [generatingMessage, setGeneratingMessage] = useState(false);
  const [templates, setTemplates] = useState<TemplateInfo[]>([]);
  const [selectedTemplateSlug, setSelectedTemplateSlug] = useState<string>("");
  const [approvalOpen, setApprovalOpen] = useState(false);

  // Guidelines dialog state
  const [guidelinesOpen, setGuidelinesOpen] = useState(false);
  const [guidelineId, setGuidelineId] = useState<string>("");
  const [guidelineContent, setGuidelineContent] = useState<string>("");
  const [savingGuideline, setSavingGuideline] = useState(false);

  useEffect(() => {
    getTemplates()
      .then((list) => {
        setTemplates(list);
      })
      .catch(() => {
        // Templates endpoint may not exist yet — ignore
      });
  }, []);

  const handleOpenGuidelines = async () => {
    try {
      const list = await getGuidelines("proposal_message");
      if (list.length > 0) {
        setGuidelineId(list[0].id);
        setGuidelineContent(list[0].content);
      }
    } catch {
      // ignore
    }
    setGuidelinesOpen(true);
  };

  const handleSaveGuideline = async () => {
    if (!guidelineId) return;
    setSavingGuideline(true);
    try {
      await updateGuideline(guidelineId, guidelineContent);
      setGuidelinesOpen(false);
    } catch {
      // ignore
    } finally {
      setSavingGuideline(false);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await generateProposal({
        deal_id: deal.id,
        rent: parseFloat(rent),
        condo_fee: parseFloat(condoFee),
        iptu: parseFloat(iptu),
        guarantee_type: guaranteeType,
        deposit_months: parseInt(depositMonths),
        move_in_date: moveInDate,
        contract_duration_months: parseInt(duration),
        special_conditions: specialConditions || undefined,
        template_name: selectedTemplateSlug || undefined,
      });
      setGeneratedText(res.text);
      await refreshDeal();
    } catch (err) {
      console.error("Failed to generate proposal:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleViaWhatsApp = async () => {
    setGeneratingMessage(true);
    try {
      const res = await generateMessage(deal.id, "confirm_proposal");
      setConfirmMessage(res.text);
      setApprovalOpen(true);
    } catch (err) {
      console.error(err);
    } finally {
      setGeneratingMessage(false);
    }
  };

  const handleConfirmSend = () => {
    if (onSendInChat && confirmMessage) {
      onSendInChat("", confirmMessage);
    }
  };

  return (
    <div className="space-y-5">
      {/* Template selector */}
      <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50 space-y-3">
        <h3 className="flex items-center gap-2 text-sm font-medium">
          <FileText className="size-4 text-primary" />
          Template de proposta
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
          type="proposal"
          onTemplateGenerated={() => {
            getTemplates()
              .then(setTemplates)
              .catch(() => {});
          }}
        />
      </div>

      {/* Values section */}
      <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50">
        <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
          <FileText className="size-4 text-primary" />
          Valores e condicoes
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <FormField label="Aluguel (R$)">
            <Input
              type="number"
              value={rent}
              onChange={(e) => setRent(e.target.value)}
              className="bg-card"
            />
          </FormField>
          <FormField label="Condominio (R$)">
            <Input
              type="number"
              value={condoFee}
              onChange={(e) => setCondoFee(e.target.value)}
              className="bg-card"
            />
          </FormField>
          <FormField label="IPTU (R$)">
            <Input
              type="number"
              value={iptu}
              onChange={(e) => setIptu(e.target.value)}
              className="bg-card"
            />
          </FormField>
          <FormField label="Garantia">
            <Select
              value={guaranteeType}
              onValueChange={(v) => setGuaranteeType(v as GuaranteeType)}
            >
              <SelectTrigger className="bg-card">
                <Shield className="size-3.5 mr-1 text-muted-foreground" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="caucao">Caucao</SelectItem>
                <SelectItem value="fiador">Fiador</SelectItem>
                <SelectItem value="seguro_fianca">Seguro-fianca</SelectItem>
              </SelectContent>
            </Select>
          </FormField>
          <FormField label="Meses caucao">
            <Input
              type="number"
              value={depositMonths}
              onChange={(e) => setDepositMonths(e.target.value)}
              className="bg-card"
            />
          </FormField>
          <FormField label="Data de entrada">
            <Input
              type="date"
              value={moveInDate}
              onChange={(e) => setMoveInDate(e.target.value)}
              className="bg-card"
            />
          </FormField>
          <FormField label="Prazo (meses)">
            <Input
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              className="bg-card"
            />
          </FormField>
        </div>
      </div>

      <FormField label="Condicoes especiais">
        <Textarea
          value={specialConditions}
          onChange={(e) => setSpecialConditions(e.target.value)}
          placeholder="Ex: Aceita pet, vaga extra..."
          rows={2}
          className="bg-card resize-none"
        />
      </FormField>

      <Button onClick={handleGenerate} disabled={loading} className="w-full">
        {loading ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Gerando proposta...
          </>
        ) : (
          <>
            <Sparkles className="size-4" />
            Gerar Proposta
          </>
        )}
      </Button>

      {generatedText && (
        <div className="rounded-xl bg-card p-4 ring-1 ring-border/60">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
            <FileText className="size-4 text-primary" />
            Preview da Proposta
          </h3>
          <div className="rounded-lg bg-muted/30 p-3">
            <pre className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {generatedText}
            </pre>
          </div>
          {/* Send options */}
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-1.5">
              <p className="text-xs font-medium text-muted-foreground">Enviar proposta:</p>
              <button
                type="button"
                onClick={handleOpenGuidelines}
                className="text-muted-foreground hover:text-foreground transition-colors"
                title="Configurar diretrizes de mensagem"
              >
                <Settings className="size-3.5" />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                variant="default"
                disabled={generatingMessage}
                onClick={handleViaWhatsApp}
              >
                {generatingMessage ? (
                  <Loader2 className="size-3.5 animate-spin" />
                ) : (
                  <Send className="size-3.5" />
                )}
                Via WhatsApp
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => window.open(getProposalPdfUrl(deal.id), "_blank")}
              >
                <Download className="size-3.5" />
                Documento formal (PDF)
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => navigator.clipboard.writeText(generatedText)}
              >
                <Copy className="size-3.5" />
                Copiar texto
              </Button>
            </div>
          </div>
        </div>
      )}

      {confirmMessage && !approvalOpen && (
        <div className="rounded-xl bg-brand-muted/50 p-4 ring-1 ring-primary/20">
          <p className="mb-2 flex items-center gap-1.5 text-xs font-medium text-primary">
            <Calendar className="size-3.5" />
            Mensagem para o lead
          </p>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">
            {confirmMessage}
          </p>
          <Button
            size="sm"
            variant="secondary"
            className="mt-3"
            onClick={() => navigator.clipboard.writeText(confirmMessage)}
          >
            <Copy className="size-3.5" />
            Copiar
          </Button>
        </div>
      )}

      <SendApprovalDialog
        open={approvalOpen}
        onClose={() => setApprovalOpen(false)}
        onConfirm={handleConfirmSend}
        leadName={lead.name}
        message={confirmMessage}
      />

      <Dialog open={guidelinesOpen} onOpenChange={setGuidelinesOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Diretrizes de mensagem de proposta</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 py-2">
            <p className="text-xs text-muted-foreground">
              Essas diretrizes serão usadas pela IA ao gerar mensagens de proposta via WhatsApp.
            </p>
            <Textarea
              value={guidelineContent}
              onChange={(e) => setGuidelineContent(e.target.value)}
              rows={5}
              className="resize-none"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setGuidelinesOpen(false)}>
              Cancelar
            </Button>
            <Button onClick={handleSaveGuideline} disabled={savingGuideline}>
              {savingGuideline ? <Loader2 className="size-4 animate-spin" /> : null}
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
