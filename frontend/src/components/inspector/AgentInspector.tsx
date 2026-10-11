import React from 'react';
import { Activity, Terminal, Database, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const AgentInspector: React.FC = () => {
  const { persona } = useAuth();
  const customerId = persona === 'arjun' ? 'cust_arjun_4521' : persona === 'priya' ? 'cust_priya_1122' : 'cust_rahul_3344';

  return (
    <div className="w-80 h-full bg-slate-900 text-slate-300 flex flex-col font-mono text-xs border-l border-slate-800">
      <div className="p-4 border-b border-slate-800 bg-slate-950 flex items-center gap-2 text-blue-400">
        <Activity size={16} />
        <h2 className="font-semibold tracking-wider">AGENT INSPECTOR</h2>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        
        <div className="space-y-2">
          <div className="text-slate-500 uppercase tracking-widest text-[10px] font-bold mb-3 flex items-center gap-2">
            <Terminal size={12} /> Execution Trace
          </div>
          <div className="pl-3 border-l border-slate-700 space-y-3">
            <div>
              <div className="text-green-400 mb-1">&gt; System initialized...</div>
              <div className="text-slate-500">LLM_PROVIDER: mock</div>
              <div className="text-slate-500">STATE: Supervisor</div>
            </div>
            <div>
              <div className="text-blue-400 mb-1">&gt; Received user input</div>
              <div className="text-slate-400 truncate">Routing intent...</div>
            </div>
            <div className="animate-pulse text-yellow-400">
              &gt; Waiting for agent execution...
            </div>
          </div>
        </div>

        <div className="space-y-2 pt-4 border-t border-slate-800">
          <div className="text-slate-500 uppercase tracking-widest text-[10px] font-bold mb-3 flex items-center gap-2">
            <Database size={12} /> Context State
          </div>
          <div className="bg-slate-950 p-3 rounded border border-slate-800 text-green-300/80 overflow-hidden">
            <pre>
{`{
  "customer_id": "${customerId}",
  "active_node": "supervisor",
  "history_len": 4
}`}
            </pre>
          </div>
        </div>

        <div className="space-y-2 pt-4 border-t border-slate-800">
          <div className="text-slate-500 uppercase tracking-widest text-[10px] font-bold mb-3 flex items-center gap-2">
            <ShieldCheck size={12} /> Security Policies
          </div>
          <div className="flex flex-col gap-2">
            <span className="bg-green-900/30 text-green-400 px-2 py-1 rounded inline-block w-fit border border-green-900/50">Object-Level Auth: Active</span>
            <span className="bg-green-900/30 text-green-400 px-2 py-1 rounded inline-block w-fit border border-green-900/50">Human-in-the-loop: Enforced</span>
          </div>
        </div>
      </div>
    </div>
  );
};
