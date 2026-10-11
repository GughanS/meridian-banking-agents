import React, { useEffect, useState } from 'react';
import { useAuth, type Persona } from '../../context/AuthContext';
import { User, Wallet, Bell } from 'lucide-react';

export const DashboardPanel: React.FC = () => {
  const { persona, switchPersona, isLoading, token } = useAuth();
  const [alerts, setAlerts] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    if (!token) return;
    setAlerts([]);
  }, [token]);

  // Using fetch for SSE to pass Authorization header
  useEffect(() => {
    if (!token) return;
    
    let isMounted = true;
    const abortController = new AbortController();

    const listenToEvents = async () => {
      try {
        const response = await fetch('http://localhost:8000/stream/events', {
          headers: { 'Authorization': `Bearer ${token}` },
          signal: abortController.signal
        });
        
        if (!response.body) return;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        
        while (isMounted) {
          const { value, done } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.replace('data: ', ''));
                if (data.type === 'FRAUD_ALERT') {
                  setAlerts(prev => [data, ...prev]);
                }
              } catch {
                // Non-JSON stream lines can be ignored
              }
            }
          }
        }
      } catch (err) {
        if (isMounted) console.error("Event stream error", err);
      }
    };
    
    listenToEvents();
    
    return () => {
      isMounted = false;
      abortController.abort();
    };
  }, [token]);

  return (
    <div className="flex flex-col h-full bg-slate-50 border-r border-slate-200">
      <div className="p-6 border-b border-slate-200 bg-white">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center text-blue-700">
            <User size={20} />
          </div>
          <div>
            <h2 className="text-sm font-medium text-slate-500 uppercase tracking-wider">Persona</h2>
            <select
              value={persona}
              onChange={(e) => switchPersona(e.target.value as Persona)}
              className="font-semibold text-lg bg-transparent focus:outline-none cursor-pointer hover:bg-slate-50 rounded px-1 -ml-1 transition-colors"
              disabled={isLoading}
            >
              <option value="arjun">Arjun (Tech Worker)</option>
              <option value="priya">Priya (Small Business)</option>
              <option value="rahul">Rahul (Student)</option>
            </select>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-5 text-white shadow-lg relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/3" />
          <div className="relative z-10">
            <div className="flex items-center gap-2 text-slate-300 mb-2">
              <Wallet size={16} />
              <p className="text-sm">Total Balance</p>
            </div>
            <h3 className="text-3xl font-light tracking-tight">₹ 1,24,500.00</h3>
            <div className="mt-4 text-xs text-slate-400">
              Account ending in 4021
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider">Quick Actions</h3>
          <div className="grid grid-cols-2 gap-3">
            {['Transfer', 'Pay Bills', 'Cards', 'Loans'].map((action) => (
              <button key={action} className="p-3 text-sm font-medium bg-white border border-slate-200 rounded-lg shadow-sm hover:border-blue-300 hover:text-blue-600 transition-colors text-left">
                {action}
              </button>
            ))}
          </div>
        </div>

        {alerts.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-slate-900 mb-4 uppercase tracking-wider flex items-center gap-2">
              <Bell size={16} className="text-red-500" /> Live Alerts
            </h3>
            <div className="space-y-3">
              {alerts.map((alert, i) => (
                <div key={i} className="bg-red-50 border border-red-200 p-4 rounded-lg">
                  <h4 className="font-semibold text-red-800 text-sm mb-1">{alert.title}</h4>
                  <p className="text-red-600 text-xs">{alert.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
