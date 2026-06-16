"use client";
import { PIPELINE_STEPS, PipelineStepKey } from "@/lib/types";
interface PipelineState {
    [key: string]: {
        status: "pending" | "running" | "completed" | "error";
        detail: string;
        progress?: number;
    };
}
interface PipelineProgressProps {
    state: PipelineState;
}
export default function PipelineProgress({ state }: PipelineProgressProps) {
    const getStepStatus = (key: string) => {
        return state[key]?.status || "pending";
    };
    const getStepDetail = (key: string) => {
        return state[key]?.detail || "";
    };
    const getStepProgress = (key: string) => {
        return state[key]?.progress;
    };
    const getStatusIcon = (status: string) => {
        switch (status) {
            case "completed":
                return "✓";
            case "running":
                return "●";
            case "error":
                return "✕";
            default:
                return "○";
        }
    };
    return (
        <div className="pipeline-progress" id="pipeline-progress">
            <div className="pipeline-title">Scraping Pipeline</div>
            {PIPELINE_STEPS.map((step) => {
                const status = getStepStatus(step.key);
                const detail = getStepDetail(step.key);
                const progress = getStepProgress(step.key);
                return (
                    <div key={step.key} className={`pipeline-step ${status}`}>
                        <div className="pipeline-step-icon">
                            {getStatusIcon(status)}
                        </div>
                        <div className="pipeline-step-content">
                            <div className="pipeline-step-name">
                                {step.icon} {step.name}
                            </div>
                            {detail && (
                                <div className="pipeline-step-detail">{detail}</div>
                            )}
                            {status === "running" && progress != null && (
                                <div className="pipeline-progress-bar">
                                    <div
                                        className="pipeline-progress-bar-fill"
                                        style={{ width: `${Math.round(progress * 100)}%` }}
                                    />
                                </div>
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
