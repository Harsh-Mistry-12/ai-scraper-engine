"use client";
import { useState } from "react";
import { DataPreview as DataPreviewType, ValidationResult } from "@/lib/types";
import { getDownloadUrl } from "@/lib/api";
interface DataPreviewProps {
    preview: DataPreviewType;
    validation?: ValidationResult;
    onApprove: (format: string) => void;
    onRetry: () => void;
}
export default function DataPreview({
    preview,
    validation,
    onApprove,
    onRetry,
}: DataPreviewProps) {
    const [outputFormat, setOutputFormat] = useState("csv");
    return (
        <div className="data-preview" id="data-preview">
            <div className="data-preview-header">
                <div className="data-preview-title">📊 Data Preview</div>
                <div className="data-preview-count">
                    Showing {preview.preview_rows} of {preview.total_rows} rows
                </div>
            </div>
            {validation && (
                <div
                    style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        marginBottom: "12px",
                        fontSize: "13px",
                    }}
                >
                    <span
                        style={{
                            background:
                                validation.quality_score >= 70
                                    ? "rgba(52, 211, 153, 0.15)"
                                    : "rgba(251, 191, 36, 0.15)",
                            color:
                                validation.quality_score >= 70
                                    ? "var(--status-success)"
                                    : "var(--status-warning)",
                            padding: "4px 10px",
                            borderRadius: "var(--radius-full)",
                            fontWeight: 600,
                        }}
                    >
                        Quality: {validation.quality_score}/100
                    </span>
                    <span style={{ color: "var(--text-secondary)" }}>
                        {validation.summary}
                    </span>
                </div>
            )}
            <div className="data-preview-table-wrapper">
                <table className="data-preview-table">
                    <thead>
                        <tr>
                            {preview.columns.map((col) => (
                                <th key={col}>{col}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {preview.rows.map((row, i) => (
                            <tr key={i}>
                                {preview.columns.map((col) => (
                                    <td key={col} title={String(row[col] ?? "")}>
                                        {String(row[col] ?? "")}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="data-preview-actions">
                <div className="format-selector">
                    <label htmlFor="output-format">Format:</label>
                    <select
                        id="output-format"
                        value={outputFormat}
                        onChange={(e) => setOutputFormat(e.target.value)}
                    >
                        <option value="csv">CSV</option>
                        <option value="xlsx">Excel (XLSX)</option>
                        <option value="json">JSON</option>
                        <option value="xml">XML</option>
                    </select>
                </div>
                <button
                    className="btn btn-primary"
                    onClick={() => onApprove(outputFormat)}
                    id="approve-btn"
                >
                    ✓ Approve & Download
                </button>
                <button className="btn btn-secondary" onClick={onRetry} id="retry-btn">
                    ↻ Retry
                </button>
            </div>
        </div>
    );
}
