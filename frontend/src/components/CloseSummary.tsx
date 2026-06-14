"use client";

import { useState } from "react";
import { ClipboardList, Copy, Loader2, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { generateSummary } from "@/lib/api";
import type { Deal } from "@/types";

interface Props {
  deal: Deal;
}

export function CloseSummary({ deal }: Props) {
  const [summaryText, setSummaryText] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await generateSummary(deal.id);
      setSummaryText(res.text);
    } catch (err) {
      console.error("Failed to generate summary:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {!summaryText && (
        <div className="flex flex-col items-center justify-center rounded-xl bg-muted/40 p-8 text-center ring-1 ring-border/50">
          <div className="mb-3 flex size-12 items-center justify-center rounded-full bg-primary/10">
            <ClipboardList className="size-6 text-primary" />
          </div>
          <p className="text-sm font-medium">Resumo do fechamento</p>
          <p className="mt-1 max-w-xs text-xs text-muted-foreground">
            Gere um resumo consolidado com todos os detalhes do negócio para
            compartilhar com a equipe.
          </p>
        </div>
      )}

      <Button onClick={handleGenerate} disabled={loading} className="w-full">
        {loading ? (
          <>
            <Loader2 className="size-4 animate-spin" />
            Gerando resumo...
          </>
        ) : (
          <>
            <Sparkles className="size-4" />
            {summaryText ? "Regenerar Resumo" : "Gerar Resumo do Fechamento"}
          </>
        )}
      </Button>

      {summaryText && (
        <div className="rounded-xl bg-card p-4 ring-1 ring-border/60">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-medium">
            <ClipboardList className="size-4 text-primary" />
            Resumo do Fechamento
          </h3>
          <div className="max-h-[400px] overflow-y-auto rounded-lg bg-muted/30 p-4">
            <pre className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
              {summaryText}
            </pre>
          </div>
          <div className="mt-3">
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigator.clipboard.writeText(summaryText)}
            >
              <Copy className="size-3.5" />
              Copiar
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
