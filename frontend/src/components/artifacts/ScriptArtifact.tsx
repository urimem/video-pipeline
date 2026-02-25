interface ScriptArtifactProps {
  script: string | null;
}

export function ScriptArtifact({ script }: ScriptArtifactProps) {
  if (!script) {
    return (
      <div className="artifact-placeholder">
        <span className="artifact-placeholder-icon">✍️</span>
        <p>Your script will appear here as you develop it with the agent.</p>
      </div>
    );
  }

  return (
    <div className="script-artifact">
      <div className="artifact-label">Script</div>
      <pre className="script-content">{script}</pre>
    </div>
  );
}
