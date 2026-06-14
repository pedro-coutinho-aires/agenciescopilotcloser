"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  leadName: string;
  message: string;
}

export function SendApprovalDialog({
  open,
  onClose,
  onConfirm,
  leadName,
  message,
}: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose(); }}>
      <DialogContent showCloseButton={false} className="max-w-md">
        <DialogHeader>
          <DialogTitle>Enviar mensagem para {leadName}?</DialogTitle>
        </DialogHeader>

        <div className="mt-2 rounded-xl bg-brand-muted/60 p-4 ring-1 ring-primary/20">
          <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground">
            {message}
          </p>
        </div>

        <div className="flex items-center justify-end gap-2 mt-2">
          <Button variant="outline" size="sm" onClick={onClose}>
            Cancelar
          </Button>
          <Button size="sm" onClick={() => { onConfirm(); onClose(); }}>
            Enviar
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
