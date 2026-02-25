import type { ImageArtifact } from "../../types";

const TYPE_LABELS: Record<ImageArtifact["type"], string> = {
  character: "Character",
  opening: "Opening Frame",
  closing: "Closing Frame",
};

interface ImagesArtifactProps {
  images: ImageArtifact[];
}

export function ImagesArtifact({ images }: ImagesArtifactProps) {
  if (images.length === 0) {
    return (
      <div className="artifact-placeholder">
        <span className="artifact-placeholder-icon">🖼️</span>
        <p>Images will appear here as they are generated.</p>
      </div>
    );
  }

  return (
    <div className="images-artifact">
      <div className="artifact-label">Images</div>
      <div className="image-grid">
        {images.map((img, i) => (
          <div key={i} className="image-card">
            <div className="image-type-tag">{TYPE_LABELS[img.type]}</div>
            {img.url ? (
              <img src={img.url} alt={img.prompt} className="image-preview" />
            ) : (
              <div className="image-pending">
                <div className="spinner" />
                <p>Generating…</p>
              </div>
            )}
            <p className="image-prompt">{img.prompt}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
