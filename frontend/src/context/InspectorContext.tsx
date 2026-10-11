import React, { createContext, useContext, useState, useCallback } from 'react';

export type InspectorStatus = 'idle' | 'routing' | 'executing' | 'responding' | 'completed' | 'error';

export interface TraceItem {
  id: string;
  timestamp: string;
  type: 'system' | 'user' | 'node' | 'tool' | 'done' | 'error';
  title: string;
  details?: string;
  color?: string;
}

interface InspectorContextType {
  traces: TraceItem[];
  status: InspectorStatus;
  activeNode: string;
  lastTool: string | null;
  historyLen: number;
  addTrace: (item: {
    type: TraceItem['type'];
    title: string;
    details?: string;
    color?: string;
  }) => void;
  setStatus: (status: InspectorStatus) => void;
  setActiveNode: (node: string) => void;
  setLastTool: (tool: string | null) => void;
  setHistoryLen: React.Dispatch<React.SetStateAction<number>>;
  clearTraces: () => void;
  resetForPersona: (personaName: string, customerId: string) => void;
}

const InspectorContext = createContext<InspectorContextType | undefined>(undefined);

const formatCurrentTime = (): string => {
  const d = new Date();
  return d.toTimeString().split(' ')[0];
};

const INITIAL_TRACES: TraceItem[] = [
  {
    id: 'init-1',
    timestamp: formatCurrentTime(),
    type: 'system',
    title: 'System initialized',
    details: 'LLM_PROVIDER: mock · Multi-Agent Graph ready',
    color: 'text-emerald-400'
  },
  {
    id: 'init-2',
    timestamp: formatCurrentTime(),
    type: 'system',
    title: 'Security guardrails active',
    details: 'Object-Level Auth & HITL 2-phase verification loaded',
    color: 'text-blue-400'
  }
];

export const InspectorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [traces, setTraces] = useState<TraceItem[]>(INITIAL_TRACES);
  const [status, setStatus] = useState<InspectorStatus>('idle');
  const [activeNode, setActiveNode] = useState<string>('supervisor');
  const [lastTool, setLastTool] = useState<string | null>(null);
  const [historyLen, setHistoryLen] = useState<number>(0);

  const addTrace = useCallback(
    (item: {
      type: TraceItem['type'];
      title: string;
      details?: string;
      color?: string;
    }) => {
      const newTrace: TraceItem = {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        timestamp: formatCurrentTime(),
        ...item
      };
      setTraces(prev => [...prev.slice(-49), newTrace]); // keep latest 50
    },
    []
  );

  const clearTraces = useCallback(() => {
    setTraces([]);
  }, []);

  const resetForPersona = useCallback((personaName: string, customerId: string) => {
    setStatus('idle');
    setActiveNode('supervisor');
    setLastTool(null);
    setHistoryLen(0);
    setTraces([
      {
        id: `persona-${Date.now()}`,
        timestamp: formatCurrentTime(),
        type: 'system',
        title: `Switched context: ${personaName.toUpperCase()}`,
        details: `Customer ID: ${customerId} · Session active`,
        color: 'text-emerald-400'
      }
    ]);
  }, []);

  return (
    <InspectorContext.Provider
      value={{
        traces,
        status,
        activeNode,
        lastTool,
        historyLen,
        addTrace,
        setStatus,
        setActiveNode,
        setLastTool,
        setHistoryLen,
        clearTraces,
        resetForPersona
      }}
    >
      {children}
    </InspectorContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useInspector = (): InspectorContextType => {
  const context = useContext(InspectorContext);
  if (!context) {
    throw new Error('useInspector must be used within an InspectorProvider');
  }
  return context;
};
