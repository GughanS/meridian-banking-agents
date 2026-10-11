import React, { useRef, useEffect } from 'react';
import { Activity, Terminal, Database, ShieldCheck, RotateCcw } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useInspector, type InspectorStatus } from '../../context/InspectorContext';

export const AgentInspector: React.FC = () => {
  const { persona } = useAuth();
  const {
    traces,
    status,
    activeNode,
    lastTool,
    historyLen,
    clearTraces
  } = useInspector();

  const traceEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    traceEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [traces, status]);


  const customerId =
    persona === 'virat'
      ? 'cust_virat_4521'
      : persona === 'rohit'
      ? 'cust_rohit_1122'
      : 'cust_mahi_3344';

  const renderStatusBadge = (s: InspectorStatus) => {
    switch (s) {
      case 'routing':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-purple-400 animate-ping"></span>
            ROUTING
          </span>
        );
      case 'executing':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse"></span>
            EXECUTING
          </span>
        );
      case 'responding':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
            STREAMING
          </span>
        );
      case 'completed':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            COMPLETED
          </span>
        );
      case 'error':
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-rose-500/20 text-rose-300 border border-rose-500/30 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400"></span>
            ERROR
          </span>
        );
      case 'idle':
      default:
        return (
          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-800 text-slate-400 border border-slate-700 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
            IDLE
          </span>
        );
    }
  };

  return (
    <div className="w-full h-full bg-slate-900 text-slate-300 flex flex-col font-mono text-xs select-none">
      {/* Header with height matching ChatPanel header */}
      <div className="h-[72px] px-4 border-b border-slate-800 bg-slate-950 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2 text-blue-400">
          <Activity size={16} />
          <h2 className="font-semibold tracking-wider text-slate-200">AGENT INSPECTOR</h2>
        </div>
        {renderStatusBadge(status)}
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {/* Execution Trace */}
        <div className="space-y-2">
          <div className="flex items-center justify-between mb-2">
            <div className="text-slate-400 uppercase tracking-widest text-[10px] font-bold flex items-center gap-1.5">
              <Terminal size={12} className="text-blue-400" /> Execution Trace
            </div>
            {traces.length > 0 && (
              <button
                onClick={clearTraces}
                title="Clear execution trace"
                className="text-slate-500 hover:text-slate-300 p-1 rounded hover:bg-slate-800 transition-colors flex items-center gap-1 text-[10px]"
              >
                <RotateCcw size={10} />
                <span>Reset</span>
              </button>
            )}
          </div>

          <div className="pl-3 border-l border-slate-800 space-y-2.5 max-h-60 overflow-y-auto pr-1">
            {traces.length === 0 ? (
              <div className="text-slate-500 text-[11px] italic">No traces recorded.</div>
            ) : (
              traces.map(trace => (
                <div key={trace.id} className="text-[11px] leading-snug">
                  <div className="flex items-center gap-1.5 text-[10px]">
                    <span className="text-slate-500">{trace.timestamp}</span>
                    <span className={`font-semibold ${trace.color || 'text-slate-400'}`}>
                      &gt; {trace.title}
                    </span>
                  </div>
                  {trace.details && (
                    <div
                      className="text-slate-400 ml-2 mt-0.5 text-[10px] truncate"
                      title={trace.details}
                    >
                      {trace.details}
                    </div>
                  )}
                </div>
              ))
            )}

            {/* Dynamic Status / Progress Indicators */}
            {status === 'routing' && (
              <div className="text-purple-400 text-[11px] flex items-center gap-1.5 animate-pulse">
                <span>&gt;</span>
                <span>Supervisor routing intent...</span>
              </div>
            )}
            {status === 'executing' && (
              <div className="text-amber-400 text-[11px] flex items-center gap-1.5 animate-pulse">
                <span>&gt;</span>
                <span>Executing tool {lastTool ? `"${lastTool}"` : 'call'}...</span>
              </div>
            )}
            {status === 'responding' && (
              <div className="text-cyan-400 text-[11px] flex items-center gap-1.5 animate-pulse">
                <span>&gt;</span>
                <span>Generating agent response...</span>
              </div>
            )}
            {status === 'idle' && (
              <div className="text-slate-500 text-[10px] italic">
                &gt; Ready. Awaiting user input.
              </div>
            )}

            <div ref={traceEndRef} />
          </div>
        </div>

        {/* Live Context State */}
        <div className="space-y-2 pt-3 border-t border-slate-800/80">
          <div className="text-slate-400 uppercase tracking-widest text-[10px] font-bold mb-2 flex items-center gap-2">
            <Database size={12} className="text-emerald-400" /> Context State
          </div>
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800 text-emerald-300/90 overflow-hidden font-mono text-[11px]">
            <pre className="whitespace-pre">
{JSON.stringify(
  {
    customer_id: customerId,
    active_node: activeNode,
    status: status,
    last_tool: lastTool,
    history_len: historyLen
  },
  null,
  2
)}
            </pre>
          </div>
        </div>

        {/* Security & Verification Policies */}
        <div className="space-y-2 pt-3 border-t border-slate-800/80">
          <div className="text-slate-400 uppercase tracking-widest text-[10px] font-bold mb-2 flex items-center gap-2">
            <ShieldCheck size={12} className="text-blue-400" /> Security Policies
          </div>
          <div className="flex flex-col gap-1.5 text-[11px]">
            <div className="flex items-center justify-between bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
              <span className="text-slate-400">Object-Level Auth</span>
              <span className="text-emerald-400 font-semibold text-[10px] bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60">
                Active (JWT)
              </span>
            </div>
            <div className="flex items-center justify-between bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
              <span className="text-slate-400">Human-In-The-Loop</span>
              <span className="text-emerald-400 font-semibold text-[10px] bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60">
                Enforced
              </span>
            </div>
            <div className="flex items-center justify-between bg-slate-950 px-2.5 py-1.5 rounded border border-slate-800">
              <span className="text-slate-400">Deterministic Engine</span>
              <span className="text-blue-400 font-semibold text-[10px] bg-blue-950/60 px-1.5 py-0.5 rounded border border-blue-800/60">
                Decimal Math
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
