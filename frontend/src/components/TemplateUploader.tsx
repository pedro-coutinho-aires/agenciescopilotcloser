"use client";

import { useRef, useState } from "react";
import { CheckCircle2, Loader2, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { generateTemplate } from "@/lib/api";

interface Props {
  type: "proposal" | "contract";
  onTemplateGenerated: () => void;
}

export function TemplateUploader({ type, onTemplateGenerated }: Props) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [generatedName, setGeneratedName] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const label = type === "proposal" ? "proposta" : "contrato";

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    e.target.value = "";

    setLoading(true);
    setError(null);
    setGeneratedName(null);

    try {
      const result = await generateTemplate(
        file,
        file.name.replace(/\.[^.]+$/, ""),
        type
      );
      setGeneratedName(result.name);
      onTemplateGenerated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar template");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center gap-2">
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt,.html"
        className="hidden"
        onChange={handleFileChange}
      />

      <Button
        variant="outline"
        size="sm"
        disabled={loading}
        onClick={() => fileInputRef.current?.click()}
      >
        {loading ? (
          <>
            <Loader2 className="size-3.5 animate-spin" />
            Gerando template...
          </>
        ) : (
          <>
            <Upload className="size-3.5" />
            Upload template de {label}
          </>
        )}
      </Button>

      {generatedName && !loading && (
        <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
          <CheckCircle2 className="size-3.5" />
          {generatedName}
        </span>
      )}

      {error && (
        <span className="text-xs text-destructive">{error}</span>
      )}
    </div>
  );
}
