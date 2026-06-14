"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { getMockData, createDeal, getDeal, simulateLeadChat, processDocument } from "@/lib/api";
import type { Lead, Property, ChatMessage, Deal } from "@/types";
import { ChatWindow } from "@/components/ChatWindow";
import { ClosePanel } from "@/components/ClosePanel";
import { CRMPanel } from "@/components/CRMPanel";

async function fetchFileAsFile(filename: string, _filepath: string): Promise<File> {
  // Fetch the mock doc from the backend
  const res = await fetch(`http://localhost:8000/api/mock-docs/${filename}`);
  const blob = await res.blob();
  return new File([blob], filename, { type: blob.type });
}

export default function Home() {
  const [lead, setLead] = useState<Lead | null>(null);
  const [property, setProperty] = useState<Property | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [deal, setDeal] = useState<Deal | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMockData()
      .then((data) => {
        setLead(data.lead);
        setProperty(data.property);
        setMessages(data.messages);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleOpenClose = useCallback(async () => {
    if (!lead || !property) return;
    if (deal) {
      setPanelOpen(true);
      return;
    }
    try {
      const newDeal = await createDeal(lead.id, property.id);
      setDeal(newDeal);
      setPanelOpen(true);
    } catch (err) {
      console.error("Failed to create deal:", err);
    }
  }, [lead, property, deal]);

  const refreshDeal = useCallback(async () => {
    if (!deal) return;
    try {
      const updated = await getDeal(deal.id);
      setDeal(updated);
    } catch (err) {
      console.error("Failed to refresh deal:", err);
    }
  }, [deal]);

  if (loading) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-background">
        <Loader2 className="size-8 animate-spin text-primary" />
        <p className="text-sm text-muted-foreground">Carregando conversa...</p>
      </div>
    );
  }

  if (!lead || !property) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-background px-6">
        <div className="flex size-12 items-center justify-center rounded-full bg-destructive/10">
          <AlertCircle className="size-6 text-destructive" />
        </div>
        <p className="max-w-sm text-center text-sm text-muted-foreground">
          Erro ao carregar dados. Verifique se o backend esta rodando.
        </p>
      </div>
    );
  }

  const sidebarOpen = panelOpen && !!deal;

  return (
    <div className="flex h-screen overflow-hidden bg-muted/30">
      {/* CRM Left Sidebar — always visible */}
      <div className="w-[280px] shrink-0 border-r border-border overflow-y-auto">
        <CRMPanel
          lead={lead}
          property={property}
          deal={deal}
          onLeadUpdate={setLead}
        />
      </div>

      {/* Chat — center, flexible */}
      <div className="flex min-w-0 flex-1 flex-col p-3">
        <div className="flex flex-1 flex-col overflow-hidden rounded-2xl bg-card shadow-sm ring-1 ring-border/60">
          <ChatWindow
            messages={messages}
            setMessages={setMessages}
            lead={lead}
            property={property}
            onOpenClosePanel={handleOpenClose}
            deal={deal}
            panelOpen={sidebarOpen}
            onLeadUpdated={setLead}
            refreshDeal={refreshDeal}
          />
        </div>
      </div>

      {/* Lais Close — right sidebar, toggled */}
      {sidebarOpen && deal && (
        <div className="w-[420px] shrink-0 border-l border-border overflow-y-auto">
          <ClosePanel
            deal={deal}
            lead={lead}
            property={property}
            messages={messages}
            onUpdateDeal={setDeal}
            refreshDeal={refreshDeal}
            onClose={() => setPanelOpen(false)}
            onSendInChat={async (fileName, text) => {
              const brokerMsg: ChatMessage = {
                id: `msg_${Date.now()}`,
                sender: "broker",
                text,
                created_at: new Date().toISOString(),
                attachments: fileName
                  ? [{ id: `att_${Date.now()}`, file_name: fileName, mime_type: "application/pdf" }]
                  : [],
              };
              const updatedMsgs = [...messages, brokerMsg];
              setMessages(updatedMsgs);

              // Trigger lead response
              try {
                const res = await simulateLeadChat({
                  deal_id: deal.id,
                  messages: updatedMsgs,
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

                // If lead is sending documents, process all of them
                if (res.send_documents && res.send_documents.length > 0) {
                  const attachments = [];
                  for (const doc of res.send_documents) {
                    try {
                      const docResult = await processDocument(
                        await fetchFileAsFile(doc.filename, doc.filepath),
                        deal.id,
                        lead.id
                      );
                      attachments.push(docResult.attachment);
                      if (Object.keys(docResult.updated_lead_fields).length > 0) {
                        setLead((prev) => prev ? { ...prev, ...docResult.updated_lead_fields } as Lead : prev);
                      }
                    } catch {
                      // Doc processing failed, still show the text message
                    }
                  }
                  leadMsg.attachments = attachments;
                  await refreshDeal();
                }

                setMessages((prev) => [...prev, leadMsg]);
              } catch {
                // Lead simulation failed silently
              }
            }}
          />
        </div>
      )}
    </div>
  );
}
