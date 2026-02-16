/**
 * ForgeExportButton — Reusable export button for any Forge stage or project.
 * Supports JSON, Markdown, PDF, and ZIP formats.
 */
import React, { useState, useCallback } from "react";
import { forgeApi } from "@/services/api";
import type { ExportFormat } from "@/types/forge";

interface ForgeExportButtonProps {
  projectId: string;
  /** Label shown on the button */
  label?: string;
  /** CSS class for the button */
  className?: string;
}

const FORMAT_OPTIONS: { value: ExportFormat; label: string; icon: string }[] = [
  { value: "json", label: "JSON", icon: "{ }" },
  { value: "markdown", label: "Markdown", icon: "MD" },
  { value: "pdf", label: "PDF", icon: "PDF" },
  { value: "zip", label: "ZIP Archive", icon: "ZIP" },
];

export const ForgeExportButton: React.FC<ForgeExportButtonProps> = ({
  projectId,
  label = "Export",
  className = "",
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = useCallback(
    async (format: ExportFormat) => {
      setIsExporting(true);
      try {
        const result = await forgeApi.exportPlaybook(projectId, format);

        // Create download from blob or URL
        if (result.blob) {
          const url = URL.createObjectURL(result.blob);
          const a = document.createElement("a");
          a.href = url;
          a.download =
            result.filename ||
            `forge_export_${projectId.substring(0, 8)}.${format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else if (result.downloadUrl) {
          window.open(result.downloadUrl, "_blank");
        }
      } catch (error) {
        console.error("Export failed:", error);
      } finally {
        setIsExporting(false);
        setIsOpen(false);
      }
    },
    [projectId],
  );

  return (
    <div className="relative inline-block">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={isExporting}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 ${className}`}
      >
        {isExporting ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        ) : (
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
            />
          </svg>
        )}
        {label}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 z-10">
          <div className="py-1">
            {FORMAT_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => handleExport(opt.value)}
                className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
              >
                <span className="text-xs font-mono text-gray-400 w-6">
                  {opt.icon}
                </span>
                {opt.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
