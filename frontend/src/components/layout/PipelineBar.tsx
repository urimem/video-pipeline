import type { PipelineStep } from "../../types";

interface Step {
  key: PipelineStep;
  label: string;
  icon: string;
}

const STEPS: Step[] = [
  { key: "script", label: "Script", icon: "✍️" },
  { key: "images", label: "Images", icon: "🖼️" },
  { key: "video", label: "Video", icon: "🎬" },
  { key: "complete", label: "Done", icon: "✅" },
];

const STEP_ORDER: PipelineStep[] = ["script", "images", "video", "complete"];

export function PipelineBar({ currentStep }: { currentStep: PipelineStep }) {
  const currentIdx = STEP_ORDER.indexOf(currentStep);

  return (
    <div className="pipeline-bar">
      {STEPS.map((step, i) => {
        const isCompleted = i < currentIdx;
        const isActive = i === currentIdx;
        return (
          <div key={step.key} className="pipeline-step-wrapper">
            <div
              className={[
                "pipeline-step",
                isCompleted ? "completed" : "",
                isActive ? "active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <span className="step-icon">{step.icon}</span>
              <span className="step-label">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={["step-connector", isCompleted ? "filled" : ""].filter(Boolean).join(" ")}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
