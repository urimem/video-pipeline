interface VideoArtifactProps {
  videoUrl: string | null;
}

export function VideoArtifact({ videoUrl }: VideoArtifactProps) {
  if (!videoUrl) {
    return (
      <div className="artifact-placeholder">
        <span className="artifact-placeholder-icon">🎬</span>
        <p>Your video is being rendered. This may take a moment…</p>
        <div className="spinner large" />
      </div>
    );
  }

  return (
    <div className="video-artifact">
      <div className="artifact-label">Video</div>
      <video
        className="video-player"
        src={videoUrl}
        controls
        autoPlay={false}
        playsInline
      />
      <a className="video-download" href={videoUrl} download>
        Download video
      </a>
    </div>
  );
}
