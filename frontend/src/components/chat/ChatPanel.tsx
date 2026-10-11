import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useInspector } from '../../context/InspectorContext';
import { v4 as uuidv4 } from 'uuid';
import ReactMarkdown from 'react-markdown';
import { Send, Loader2 } from 'lucide-react';
import { ConfirmCard } from '../blocks/ConfirmCard';

interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  tools?: string[];
  confirmAction?: {
    actionId: string;
    type: string;
    details: Record<string, unknown>;
  };
}

export const ChatPanel: React.FC = () => {
  const { token, persona } = useAuth();
  const {
    addTrace,
    setStatus,
    setActiveNode,
    setLastTool,
    setHistoryLen,
    resetForPersona
  } = useInspector();

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const sessionIdRef = useRef<string>(uuidv4());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const activeNodeRef = useRef<string>('supervisor');

  useEffect(() => {
    sessionIdRef.current = uuidv4();
    setMessages([]);
    activeNodeRef.current = 'supervisor';
    const custId =
      persona === 'virat'
        ? 'cust_virat_4521'
        : persona === 'rohit'
        ? 'cust_rohit_1122'
        : 'cust_mahi_3344';
    resetForPersona(persona, custId);
  }, [persona, resetForPersona]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || !token) return;

      const userMsg: Message = { id: uuidv4(), role: 'user', content: text };
      setMessages(prev => [...prev, userMsg]);
      setIsStreaming(true);

      setStatus('routing');
      setActiveNode('supervisor');
      activeNodeRef.current = 'supervisor';
      setHistoryLen(prev => prev + 1);

      addTrace({
        type: 'user',
        title: 'User Input Received',
        details: `"${text.length > 50 ? text.slice(0, 50) + '...' : text}"`,
        color: 'text-blue-400'
      });
      addTrace({
        type: 'node',
        title: 'Supervisor Node Active',
        details: 'Routing user query to specialized domain agent...',
        color: 'text-purple-400'
      });

      try {
        const response = await fetch(`http://localhost:8000/chat/stream`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            session_id: sessionIdRef.current,
            message: userMsg.content
          })
        });

        if (!response.body) throw new Error('No response body');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let done = false;

        const modelMsgId = uuidv4();
        setMessages(prev => [...prev, { id: modelMsgId, role: 'model', content: '', tools: [] }]);

        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '');
                if (!dataStr) continue;
                try {
                  const data = JSON.parse(dataStr);
                  if (data.type === 'message') {
                    const rawNode = data.node || 'agent';
                    const formattedNode =
                      rawNode === 'customer_agent'
                        ? 'CustomerAgent'
                        : rawNode === 'credit_agent'
                        ? 'CreditAgent'
                        : rawNode === 'risk_agent'
                        ? 'RiskAgent'
                        : rawNode === 'supervisor'
                        ? 'Supervisor'
                        : rawNode;

                    if (activeNodeRef.current !== formattedNode) {
                      activeNodeRef.current = formattedNode;
                      setActiveNode(formattedNode);
                      addTrace({
                        type: 'node',
                        title: `Active Agent: ${formattedNode}`,
                        details: 'Synthesizing response stream...',
                        color: 'text-cyan-400'
                      });
                    }
                    setStatus('responding');
                    setMessages(prev =>
                      prev.map(m =>
                        m.id === modelMsgId ? { ...m, content: m.content + data.content } : m
                      )
                    );
                  } else if (data.type === 'tool_call') {
                    const toolName = String(data.name || 'core_engine');
                    setLastTool(toolName);
                    setStatus('executing');
                    addTrace({
                      type: 'tool',
                      title: `Tool Invoked: ${toolName}()`,
                      details: 'Executing deterministic core-banking tool...',
                      color: 'text-amber-400'
                    });
                    setMessages(prev =>
                      prev.map(m =>
                        m.id === modelMsgId ? { ...m, tools: [...(m.tools || []), toolName] } : m
                      )
                    );
                  } else if (data.type === 'tool_response') {
                    addTrace({
                      type: 'tool',
                      title: `Tool Result: ${data.name || 'executed'}`,
                      details: 'Execution verified · Object auth valid',
                      color: 'text-emerald-400'
                    });
                    let payload = data.content;
                    if (typeof payload === 'string') {
                      try {
                        payload = JSON.parse(payload);
                      } catch {
                        // ignore non-json strings
                      }
                    }
                    if (payload && typeof payload === 'object' && payload.data) {
                      payload = payload.data;
                    }
                    if (payload && typeof payload === 'object' && payload.action_id) {
                      setMessages(prev =>
                        prev.map(m =>
                          m.id === modelMsgId
                            ? {
                                ...m,
                                confirmAction: {
                                  actionId: String(payload.action_id),
                                  type: String(data.name || 'pending_action'),
                                  details: payload as Record<string, unknown>
                                }
                              }
                            : m
                        )
                      );
                    }
                  } else if (data.type === 'done') {
                    done = true;
                    setStatus('completed');
                    setHistoryLen(prev => prev + 1);
                    addTrace({
                      type: 'done',
                      title: 'Execution Completed',
                      details: 'Turn finished safely (Status: 200 OK)',
                      color: 'text-emerald-300'
                    });
                  }
                } catch {
                  // Non-JSON stream lines can be ignored
                }
              }
            }
          }
        }
      } catch (e) {
        console.error(e);
        setStatus('error');
        addTrace({
          type: 'error',
          title: 'Execution Error',
          details: e instanceof Error ? e.message : 'Unknown network or stream error',
          color: 'text-rose-400'
        });
      } finally {
        setIsStreaming(false);
      }
    },
    [token, setStatus, setActiveNode, setHistoryLen, addTrace, setLastTool]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token) return;
    const msg = input;
    setInput('');
    sendMessage(msg);
  };

  useEffect(() => {
    const handleQuickAction = (e: Event) => {
      const customEvent = e as CustomEvent<string>;
      if (customEvent.detail && token) {
        sendMessage(customEvent.detail);
      }
    };
    window.addEventListener('meridian:quick-action', handleQuickAction);
    return () => window.removeEventListener('meridian:quick-action', handleQuickAction);
  }, [token, sendMessage]);

  return (
    <div className="flex-1 flex flex-col h-full bg-white relative">
      <div className="h-[72px] px-6 border-b border-slate-200 bg-white z-10 flex justify-between items-center shrink-0">
        <div>
          <h2 className="text-lg font-semibold text-slate-800">Meridian AI Agent</h2>
          <p className="text-xs text-slate-500">Indicative simulation. Not real banking data.</p>
        </div>
      </div>

      
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50">
        {messages.length === 0 && (
          <div className="flex justify-center items-center h-full text-slate-400">
            Start a conversation...
          </div>
        )}
        
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-4 shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-br-sm' : 'bg-white border border-slate-200 text-slate-800 rounded-bl-sm'}`}>
              
              {msg.tools && msg.tools.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {msg.tools.map((t, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-slate-100 text-slate-600 rounded flex items-center gap-1 border border-slate-200">
                      <Loader2 size={12} className="animate-spin" /> {t}
                    </span>
                  ))}
                </div>
              )}
              
              <div className="prose prose-sm prose-slate max-w-none">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>

              {msg.confirmAction && (
                <ConfirmCard 
                  actionId={msg.confirmAction.actionId}
                  type={msg.confirmAction.type}
                  details={msg.confirmAction.details}
                  onResolved={() => {}}
                />
              )}
            </div>
          </div>
        ))}
        {isStreaming && (
           <div className="flex justify-start">
             <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-sm p-4 shadow-sm text-slate-400 flex items-center gap-2">
               <Loader2 className="animate-spin" size={16} /> Thinking...
             </div>
           </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-slate-200 bg-white">
        <form className="flex space-x-2" onSubmit={handleSubmit}>
          <input 
            type="text" 
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={isStreaming}
            placeholder={isStreaming ? "Agent is typing..." : "Type your message..."} 
            className="flex-1 border border-slate-300 rounded-full px-5 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-shadow disabled:bg-slate-50"
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isStreaming}
            className="bg-blue-600 text-white rounded-full p-3 font-medium hover:bg-blue-700 transition-colors disabled:bg-slate-300 flex items-center justify-center"
          >
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};
