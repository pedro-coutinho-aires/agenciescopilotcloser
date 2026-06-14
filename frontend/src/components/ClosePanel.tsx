"use client";

import {
  FileText,
  FileCheck,
  ScrollText,
  ClipboardList,
  X,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Deal, Lead, Property, ChatMessage } from "@/types";
import { DocumentChecklist } from "@/components/DocumentChecklist";
import { ProposalBuilder } from "@/components/ProposalBuilder";
import { ContractPreview } from "@/components/ContractPreview";
import { CloseSummary } from "@/components/CloseSummary";
import { cn } from "@/lib/utils";

const STAGE_LABELS: Record<string, string> = {
  negotiation: "Em negociação",
  documents_pending: "Documentos pendentes",
  proposal_ready: "Proposta pronta",
  contract_draft_ready: "Minuta pronta",
  waiting_approval: "Aguardando aprovação",
  closed: "Fechado",
  lost: "Perdido",
};

const STAGE_COLORS: Record<string, string> = {
  negotiation: "bg-amber-100 text-amber-800 ring-amber-200/60",
  documents_pending: "bg-orange-100 text-orange-800 ring-orange-200/60",
  proposal_ready: "bg-blue-100 text-blue-800 ring-blue-200/60",
  contract_draft_ready: "bg-violet-100 text-violet-800 ring-violet-200/60",
  waiting_approval: "bg-cyan-100 text-cyan-800 ring-cyan-200/60",
  closed: "bg-emerald-100 text-emerald-800 ring-emerald-200/60",
  lost: "bg-red-100 text-red-800 ring-red-200/60",
};

interface Props {
  deal: Deal;
  lead: Lead;
  property: Property;
  messages?: ChatMessage[];
  onUpdateDeal: (deal: Deal) => void;
  refreshDeal: () => Promise<void>;
  onClose: () => void;
  onSendInChat?: (fileName: string, text: string) => void;
}

export function ClosePanel({
  deal,
  lead,
  property,
  messages,
  onUpdateDeal,
  refreshDeal,
  onClose,
  onSendInChat,
}: Props) {
  const approvedDocs = deal.documents.filter(
    (d) => d.status === "approved" || d.status === "received"
  ).length;
  const docProgress = Math.round(
    (approvedDocs / Math.max(deal.documents.length, 1)) * 100
  );

  return (
    <div className="flex h-full flex-col bg-card">
      {/* Header */}
      <div className="gradient-brand px-5 py-4 text-brand-foreground">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="flex size-7 items-center justify-center rounded-lg bg-white/15">
                <FileCheck className="size-4" />
              </div>
              <h2 className="font-semibold text-lg tracking-tight">
                Agencies Copilot Closer
              </h2>
            </div>
            <p className="mt-1.5 text-sm text-brand-foreground/80">
              {lead.name}
            </p>
            <p className="mt-0.5 inline-flex items-center gap-1 text-xs text-brand-foreground/65">
              <MapPin className="size-3" />
              {property.neighborhood}, {property.city}
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon-sm"
            onClick={onClose}
            className="text-brand-foreground/80 hover:bg-white/15 hover:text-brand-foreground"
          >
            <X className="size-4" />
          </Button>
        </div>

        <div className="mt-3 flex items-center gap-3">
          <Badge
            className={cn(
              "ring-1 border-0 font-medium",
              STAGE_COLORS[deal.stage] || "bg-white/20 text-white ring-white/20"
            )}
          >
            {STAGE_LABELS[deal.stage] || deal.stage}
          </Badge>
          <div className="flex-1">
            <div className="flex items-center justify-between text-[10px] text-brand-foreground/70 mb-1">
              <span>Documentos</span>
              <span>
                {approvedDocs}/{deal.documents.length}
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/20">
              <div
                className="h-full rounded-full bg-white/80 transition-all duration-500"
                style={{ width: `${docProgress}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="docs" className="flex flex-1 flex-col overflow-hidden">
        <TabsList className="mx-4 mt-3 w-auto grid grid-cols-4">
          <TabsTrigger value="docs" className="gap-1.5 text-xs">
            <ClipboardList className="size-3.5" />
            Docs
          </TabsTrigger>
          <TabsTrigger value="proposal" className="gap-1.5 text-xs">
            <FileText className="size-3.5" />
            Proposta
          </TabsTrigger>
          <TabsTrigger value="contract" className="gap-1.5 text-xs">
            <ScrollText className="size-3.5" />
            Contrato
          </TabsTrigger>
          <TabsTrigger value="summary" className="gap-1.5 text-xs">
            <FileCheck className="size-3.5" />
            Resumo
          </TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-auto">
          <TabsContent value="docs" className="px-4 pb-4 mt-2">
            <DocumentChecklist
              deal={deal}
              onUpdateDeal={onUpdateDeal}
              refreshDeal={refreshDeal}
              onSendInChat={onSendInChat}
              leadName={lead.name}
              messages={messages}
            />
          </TabsContent>

          <TabsContent value="proposal" className="px-4 pb-4 mt-2">
            <ProposalBuilder
              deal={deal}
              lead={lead}
              property={property}
              onUpdateDeal={onUpdateDeal}
              refreshDeal={refreshDeal}
              onSendInChat={onSendInChat}
            />
          </TabsContent>

          <TabsContent value="contract" className="px-4 pb-4 mt-2">
            <ContractPreview
              deal={deal}
              refreshDeal={refreshDeal}
              onSendInChat={onSendInChat}
              leadName={lead.name}
            />
          </TabsContent>

          <TabsContent value="summary" className="px-4 pb-4 mt-2">
            <CloseSummary deal={deal} />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
