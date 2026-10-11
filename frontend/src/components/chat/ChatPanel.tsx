import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
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
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const sessionIdRef = useRef<string>(uuidv4());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    sessionIdRef.current = uuidv4();
    setMessages([]);
  }, [persona]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !token) return;

    const userMsg: Message = { id: uuidv4(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsStreaming(true);

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

      if (!response.body) throw new Error("No response body");
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
                  setMessages(prev => prev.map(m => 
                    m.id === modelMsgId ? { ...m, content: m.content + data.content } : m
                  ));
                } else if (data.type === 'tool_call') {
                  setMessages(prev => prev.map(m => 
                    m.id === modelMsgId ? { ...m, tools: [...(m.tools || []), data.name] } : m
                  ));
                } else if (data.type === 'tool_response') {
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
                    setMessages(prev => prev.map(m => 
                      m.id === modelMsgId ? {
                        ...m,
                        confirmAction: {
                          actionId: String(payload.action_id),
                          type: String(data.name || 'pending_action'),
                          details: payload as Record<string, unknown>
                        }
                      } : m
                    ));
                  }
                } else if (data.type === 'done') {
                  done = true;
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
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white relative">
      <div className="p-4 border-b border-slate-200 shadow-sm bg-white z-10 flex justify-between items-center">
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
