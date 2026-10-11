import React from 'react';

interface AppLayoutProps {
  dashboard: React.ReactNode;
  chat: React.ReactNode;
  inspector: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ dashboard, chat, inspector }) => {
  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden bg-slate-100 text-slate-800">
      {/* Top Persistent Banner */}
      <header className="bg-slate-900 text-white px-4 py-2 flex items-center justify-between text-xs border-b border-slate-800 select-none">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-blue-600 text-white flex items-center justify-center font-bold text-xs">M</span>
          <span className="font-semibold tracking-wide text-sm">Meridian Banking</span>
          <span className="text-slate-400 text-xs ml-2">Autonomous Multi-Agent Core Banking</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium">
            SIMULATION ONLY · FICTIONAL DATA
          </span>
        </div>
      </header>

      {/* Main Content Panes */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: Dashboard */}
        <div className="w-1/4 h-full border-r border-slate-200 bg-white flex flex-col">
          {dashboard}
        </div>

        {/* Middle Pane: Chat */}
        <div className="w-2/4 h-full flex flex-col">
          {chat}
        </div>

        {/* Right Pane: Inspector */}
        <div className="w-1/4 h-full border-l border-slate-200 bg-slate-50 flex flex-col">
          {inspector}
        </div>
      </div>
    </div>
  );
};
