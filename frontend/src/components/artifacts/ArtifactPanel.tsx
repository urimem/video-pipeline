import { useSessionStore } from "../../store/sessionStore";
import { ScriptArtifact } from "./ScriptArtifact";
import { ImagesArtifact } from "./ImagesArtifact";
import { VideoArtifact } from "./VideoArtifact";

const STEP_ORDER = ["script", "images", "video", "complete"] as const;

export function ArtifactPanel() {
  const { pipelineStep, script, images, videoUrl } = useSessionStore();
  const currentIdx = STEP_ORDER.indexOf(pipelineStep);

  // Show an artifact section if we've reached or passed its step
  const showScript = currentIdx >= 0;
  const showImages = currentIdx >= 1;
  const showVideo = currentIdx >= 2;

  return (
    <div className="artifact-panel">
      <div className="artifact-panel-header">Artifacts</div>

      <div className="artifact-sections">
        {showScript && (
          <section
            className={`artifact-section ${pipelineStep === "script" ? "active" : ""}`}
          >
            <ScriptArtifact script={script} />
          </section>
        )}

        {showImages && (
          <section
            className={`artifact-section ${pipelineStep === "images" ? "active" : ""}`}
          >
            <ImagesArtifact images={images} />
          </section>
        )}

        {showVideo && (
          <section
            className={`artifact-section ${pipelineStep === "video" || pipelineStep === "complete" ? "active" : ""}`}
          >
            <VideoArtifact videoUrl={videoUrl} />
          </section>
        )}
      </div>
    </div>
  );
}
