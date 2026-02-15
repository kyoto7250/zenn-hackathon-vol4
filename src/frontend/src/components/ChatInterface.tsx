import { useState, useEffect, useRef } from 'react';
import { createSession, sendMessage } from '../services/api';
import type { Message } from '../types';
import { Send, Bot, User } from 'lucide-react';
import './ChatInterface.css';

interface ChatInterfaceProps {
    onScenarioGenerated: (scenarioId: string) => void;
}

export default function ChatInterface({ onScenarioGenerated }: ChatInterfaceProps) {
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isComposing, setIsComposing] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Initialize session
        createSession('New Session').then((session) => {
            setSessionId(session.id);
            setMessages([{
                id: 'welcome',
                role: 'assistant',
                content: 'Hello! Describe a Kubernetes scenario you want to visualize.',
                created_at: new Date().toISOString()
            }]);
        });
    }, []);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if (!input.trim() || !sessionId || loading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const response = await sendMessage(sessionId, userMsg.content);
            setMessages(prev => [...prev, {
                id: response.message.id,
                role: 'assistant',
                content: response.message.content,
                created_at: response.message.created_at
            }]);

            if (response.scenario_id) {
                onScenarioGenerated(response.scenario_id);
            }
        } catch (error) {
            console.error(error);
            setMessages(prev => [...prev, {
                id: 'error',
                role: 'system',
                content: 'Error processing request.',
                created_at: new Date().toISOString()
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="chat-container">
            <div className="messages-area">
                {messages.map((msg) => (
                    <div key={msg.id} className={`message ${msg.role}`}>
                        <div className="avatar">
                            {msg.role === 'assistant' ? <Bot size={16} /> : <User size={16} />}
                        </div>
                        <div className="content">{msg.content}</div>
                    </div>
                ))}
                {loading && <div className="loading">Thinking...</div>}
                <div ref={messagesEndRef} />
            </div>
            <div className="input-area">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onCompositionStart={() => setIsComposing(true)}
                    onCompositionEnd={() => setIsComposing(false)}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && !isComposing) {
                            handleSend();
                        }
                    }}
                    placeholder="e.g. Deploy 3 nginx pods"
                    disabled={loading}
                />
                <button onClick={handleSend} disabled={loading || !input.trim()}>
                    <Send size={16} />
                </button>
            </div>
        </div>
    );
}
