"use client";

import {
  Phone,
  Mail,
  Briefcase,
  DollarSign,
  Heart,
  CreditCard,
  IdCard,
  Calendar,
  Home,
  Building2,
  MapPin,
  BedDouble,
  Car,
  PawPrint,
  User,
  FileText,
  ClipboardList,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { Lead, Property, Deal } from "@/types";
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

function getInitials(name: string) {
  return name
    .split(" ")
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value?: string | null;
}) {
  const isEmpty = !value;
  return (
    <div className="flex items-start gap-2.5 py-1.5">
      <Icon className="size-3.5 shrink-0 mt-0.5 text-muted-foreground" />
      <div className="min-w-0 flex-1">
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide block">
          {label}
        </span>
        <span
          className={cn(
            "text-xs font-medium leading-snug",
            isEmpty ? "text-destructive" : "text-foreground"
          )}
        >
          {isEmpty ? "Pendente" : value}
        </span>
      </div>
    </div>
  );
}

function SectionHeader({ children }: { children: React.ReactNode }) {
  return (
    <div className="mt-4 mb-1 px-4">
      <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">
        {children}
      </p>
      <div className="mt-1 h-px bg-border" />
    </div>
  );
}

interface Props {
  lead: Lead;
  property: Property;
  deal: Deal | null;
  onLeadUpdate: (lead: Lead) => void;
}

export function CRMPanel({ lead, property, deal }: Props) {
  const totalRent = property.rent + property.condo_fee + property.iptu;

  const approvedDocs = deal
    ? deal.documents.filter(
        (d) => d.status === "approved" || d.status === "received"
      ).length
    : 0;
  const totalDocs = deal ? deal.documents.length : 0;

  const hasProposal = !!deal?.proposal;
  const hasContract = !!deal?.contract_draft;

  return (
    <div className="flex flex-col h-full bg-card">
      {/* Lead header */}
      <div className="gradient-brand px-4 py-5 text-brand-foreground">
        <div className="flex items-center gap-3">
          <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-white/20 text-sm font-bold text-white">
            {getInitials(lead.name)}
          </div>
          <div className="min-w-0">
            <h2 className="font-semibold text-base leading-tight truncate">
              {lead.name}
            </h2>
            {deal && (
              <Badge
                className={cn(
                  "mt-1 border-0 ring-1 text-[10px] font-medium",
                  STAGE_COLORS[deal.stage] || "bg-white/20 text-white ring-white/20"
                )}
              >
                {STAGE_LABELS[deal.stage] || deal.stage}
              </Badge>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto pb-4">
        {/* Lead info section */}
        <SectionHeader>Lead</SectionHeader>
        <div className="px-4 space-y-0.5">
          <InfoRow icon={Phone} label="Telefone" value={lead.phone} />
          <InfoRow icon={Mail} label="E-mail" value={lead.email} />
          <InfoRow icon={Briefcase} label="Ocupacao" value={lead.occupation} />
          <InfoRow icon={DollarSign} label="Renda" value={lead.income_range} />
          <InfoRow
            icon={Heart}
            label="Estado civil"
            value={lead.marital_status}
          />
          <InfoRow
            icon={CreditCard}
            label="CPF"
            value={undefined}
          />
          <InfoRow icon={IdCard} label="RG" value={undefined} />
          <InfoRow
            icon={Calendar}
            label="Nascimento"
            value={lead.desired_move_in_date}
          />
          <InfoRow icon={Home} label="Endereco" value={undefined} />
        </div>

        {/* Property info section */}
        <SectionHeader>Imovel</SectionHeader>
        <div className="px-4">
          <div className="rounded-xl bg-muted/40 p-3 ring-1 ring-border/50 space-y-2">
            <div className="flex items-start gap-2">
              <Building2 className="size-4 shrink-0 mt-0.5 text-primary" />
              <div>
                <p className="text-sm font-semibold leading-tight">
                  {property.title}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground flex items-center gap-1">
                  <MapPin className="size-3" />
                  {property.address}, {property.neighborhood}, {property.city}
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs border-t border-border/60 pt-2">
              <div>
                <span className="text-muted-foreground">Aluguel</span>
                <p className="font-semibold">{formatCurrency(property.rent)}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Condominio</span>
                <p className="font-semibold">
                  {formatCurrency(property.condo_fee)}
                </p>
              </div>
              <div>
                <span className="text-muted-foreground">IPTU</span>
                <p className="font-semibold">{formatCurrency(property.iptu)}</p>
              </div>
              <div>
                <span className="text-muted-foreground font-medium">Total</span>
                <p className="font-bold text-primary">
                  {formatCurrency(totalRent)}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 border-t border-border/60 pt-2">
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <BedDouble className="size-3.5" />
                {property.bedrooms} quarto{property.bedrooms !== 1 ? "s" : ""}
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Car className="size-3.5" />
                {property.parking_spots} vaga
                {property.parking_spots !== 1 ? "s" : ""}
              </span>
              {property.accepts_pet && (
                <span className="inline-flex items-center gap-1 text-xs text-emerald-600">
                  <PawPrint className="size-3.5" />
                  Aceita pet
                </span>
              )}
            </div>

            {property.owner_name && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground border-t border-border/60 pt-2">
                <User className="size-3.5" />
                Proprietario: {property.owner_name}
              </div>
            )}
          </div>
        </div>

        {/* Deal stats section */}
        {deal && (
          <>
            <SectionHeader>Negocio</SectionHeader>
            <div className="px-4 space-y-2">
              <div className="rounded-xl bg-muted/40 p-3 ring-1 ring-border/50 space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <ClipboardList className="size-3.5" />
                    Estagio
                  </span>
                  <Badge
                    className={cn(
                      "border-0 ring-1 text-[10px] font-medium",
                      STAGE_COLORS[deal.stage] || "bg-muted text-muted-foreground ring-border/50"
                    )}
                  >
                    {STAGE_LABELS[deal.stage] || deal.stage}
                  </Badge>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="flex items-center gap-1.5 text-muted-foreground">
                    <FileText className="size-3.5" />
                    Documentos
                  </span>
                  <span
                    className={cn(
                      "font-semibold",
                      approvedDocs === totalDocs
                        ? "text-emerald-600"
                        : "text-amber-600"
                    )}
                  >
                    {approvedDocs}/{totalDocs} recebidos
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Proposta</span>
                  <span
                    className={cn(
                      "font-semibold",
                      hasProposal ? "text-emerald-600" : "text-muted-foreground"
                    )}
                  >
                    {hasProposal ? "Gerada" : "Pendente"}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Contrato</span>
                  <span
                    className={cn(
                      "font-semibold",
                      hasContract ? "text-emerald-600" : "text-muted-foreground"
                    )}
                  >
                    {hasContract ? "Gerado" : "Pendente"}
                  </span>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
