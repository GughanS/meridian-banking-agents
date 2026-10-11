import React from 'react';

interface AppLayoutProps {
  dashboard: React.ReactNode;
  chat: React.ReactNode;
  inspector: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ dashboard, chat, inspector }) => {
  return (
    <div className="flex flex-col h-screen w-full overflow-hidden bg-slate-100 text-slate-800">
      {/* Top Persistent Banner */}
      <header className="h-10 bg-slate-900 text-white px-4 flex items-center justify-between text-xs border-b border-slate-800 select-none shrink-0">
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded bg-blue-600 text-white flex items-center justify-center font-bold text-xs">M</span>
          <span className="font-semibold tracking-wide text-sm">Meridian Banking</span>
          <span className="text-slate-400 text-xs ml-2 hidden sm:inline">Autonomous Multi-Agent Core Banking</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-medium tracking-wide">
            SIMULATION ONLY · FICTIONAL DATA
          </span>
        </div>
      </header>

      {/* Main Content Panes */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Pane: Dashboard */}
        <div className="w-[320px] lg:w-[350px] xl:w-[380px] shrink-0 h-full border-r border-slate-200 bg-white flex flex-col">
          {dashboard}
        </div>

        {/* Middle Pane: Chat */}
        <div className="flex-1 min-w-0 h-full flex flex-col bg-white">
          {chat}
        </div>

        {/* Right Pane: Inspector */}
        <div className="w-[340px] lg:w-[380px] xl:w-[420px] shrink-0 h-full border-l border-slate-800 bg-slate-900 flex flex-col">
          {inspector}
        </div>
      </div>
    </div>
  );
};

