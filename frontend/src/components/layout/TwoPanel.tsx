import { ChatPanel } from "../chat/ChatPanel";
import { ArtifactPanel } from "../artifacts/ArtifactPanel";

interface TwoPanelProps {
  onSendMessage: (text: string) => void;
}

export function TwoPanel({ onSendMessage }: TwoPanelProps) {
  return (
    <div className="two-panel">
      <ChatPanel onSendMessage={onSendMessage} />
      <ArtifactPanel />
    </div>
  );
}
