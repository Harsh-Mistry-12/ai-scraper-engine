export default function ConfigPanel() {
  return (
    <div className="h-full w-full glass-panel rounded-xl p-5 flex flex-col overflow-y-auto">
      <h3 className="font-semibold text-gray-200 mb-6 flex items-center gap-2">
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-400"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
        Configuration
      </h3>
      
      <div className="space-y-6">
        {/* Input Settings */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Input Settings</label>
          <div className="bg-white/5 rounded-lg border border-white/5 p-3">
            <p className="text-sm text-gray-300 mb-2">Upload a file (URLs, IDs, etc.)</p>
            <div className="border-2 border-dashed border-white/10 rounded-lg p-4 text-center cursor-pointer hover:border-blue-500/50 hover:bg-blue-500/5 transition-all">
              <span className="text-xs text-gray-400">Drag & drop or click to upload<br/>(CSV, XLSX, JSON)</span>
            </div>
          </div>
        </div>

        {/* Output Format */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Output Format</label>
          <select className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500/50 appearance-none">
            <option value="json">JSON</option>
            <option value="csv">CSV</option>
            <option value="xlsx">Excel (XLSX)</option>
            <option value="xml">XML</option>
          </select>
        </div>

        {/* Scraping Strategy (Read-only / Selected by AI) */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Current Strategy</label>
          <div className="bg-black/20 rounded-lg border border-white/5 p-3 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse"></div>
            <span className="text-sm text-gray-300">Awaiting URL...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
