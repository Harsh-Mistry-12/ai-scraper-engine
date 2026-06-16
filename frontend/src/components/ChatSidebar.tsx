export default function ChatSidebar() {
  return (
    <div className="h-full w-full glass-panel rounded-xl p-4 flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          Scraper Engine
        </h2>
      </div>
      
      <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors mb-6 flex items-center justify-center gap-2">
        <span>+</span> New Scraping Task
      </button>

      <div className="flex-1 overflow-y-auto">
        <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider font-semibold">Recent</h3>
        <div className="space-y-2">
          {/* Placeholder for history */}
          <div className="p-3 rounded-lg bg-white/5 cursor-pointer hover:bg-white/10 transition-colors border border-white/5">
            <p className="text-sm font-medium truncate text-gray-200">Amazon Product Data</p>
            <p className="text-xs text-gray-500 mt-1">2 hours ago</p>
          </div>
        </div>
      </div>
    </div>
  );
}
