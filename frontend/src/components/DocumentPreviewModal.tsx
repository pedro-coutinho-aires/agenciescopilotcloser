"use client";

import { Download, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { ProcessedDocument } from "@/types";

interface Props {
  open: boolean;
  onClose: () => void;
  document: ProcessedDocument | null;
  downloadUrl: string;
}

export function DocumentPreviewModal({
  open,
  onClose,
  document,
  downloadUrl,
}: Props) {
  if (!document) return null;

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent showCloseButton={false} className="max-w-2xl max-h-[80vh] flex flex-col gap-0 p-0 overflow-hidden">
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border shrink-0">
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <DialogTitle className="text-base font-semibold leading-snug">
                {document.document_type}
              </DialogTitle>
              <p className="mt-0.5 text-xs text-muted-foreground truncate">
                {document.file_name}
              </p>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="shrink-0 size-8"
            >
              <X className="size-4" />
            </Button>
          </div>
        </DialogHeader>

        <Tabs defaultValue="resumo" className="flex flex-1 flex-col overflow-hidden min-h-0">
          <TabsList className="mx-6 mt-3 shrink-0 w-auto grid grid-cols-3">
            <TabsTrigger value="resumo" className="text-xs">Resumo</TabsTrigger>
            <TabsTrigger value="documento" className="text-xs">Documento</TabsTrigger>
            <TabsTrigger value="dados" className="text-xs">Dados Extraidos</TabsTrigger>
          </TabsList>

          <div className="flex-1 overflow-auto min-h-0 px-6 pb-4 mt-3">
            <TabsContent value="resumo" className="mt-0">
              <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50">
                <p className="text-sm leading-relaxed whitespace-pre-wrap">
                  {document.document_resume || "Nenhum resumo disponivel."}
                </p>
              </div>
            </TabsContent>

            <TabsContent value="documento" className="mt-0">
              <div
                className="rounded-xl bg-white p-4 ring-1 ring-border/50 text-sm leading-relaxed prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{
                  __html: document.document_html || "<p>Sem conteudo HTML disponivel.</p>",
                }}
              />
            </TabsContent>

            <TabsContent value="dados" className="mt-0">
              {Object.keys(document.extracted_fields).length === 0 ? (
                <div className="rounded-xl bg-muted/40 p-4 ring-1 ring-border/50 text-center text-sm text-muted-foreground">
                  Nenhum campo extraido.
                </div>
              ) : (
                <div className="rounded-xl bg-muted/40 ring-1 ring-border/50 divide-y divide-border/60 overflow-hidden">
                  {Object.entries(document.extracted_fields).map(([key, value]) => (
                    <div key={key} className="flex items-start gap-3 px-4 py-2.5">
                      <span className="w-36 shrink-0 text-xs text-muted-foreground capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs font-medium flex-1">{value}</span>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
          </div>
        </Tabs>

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 px-6 py-4 border-t border-border shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={() => window.open(downloadUrl, "_blank")}
          >
            <Download className="size-3.5" />
            Download
          </Button>
          <Button size="sm" onClick={onClose}>
            Fechar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
