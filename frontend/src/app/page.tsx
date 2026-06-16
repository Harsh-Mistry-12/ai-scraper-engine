import ChatSidebar from "@/components/ChatSidebar";
import ChatArea from "@/components/ChatArea";
import ConfigPanel from "@/components/ConfigPanel";

export default function Home() {
  return (
    <main className="flex h-screen w-full overflow-hidden p-4 gap-4">
      <div className="w-64 flex-shrink-0">
        <ChatSidebar />
      </div>
      
      <div className="flex-1 flex flex-col min-w-0 glass-panel rounded-xl overflow-hidden">
        <ChatArea />
      </div>
      
      <div className="w-80 flex-shrink-0">
        <ConfigPanel />
      </div>
    </main>
  );
}
