// Chatbot.jsx - Database Consultation Interface
import { Send, Database, Zap, Cpu } from "lucide-react";
import { useState } from "react";

export function Chatbot() {
    const [messages, setMessages] = useState([
        { id: 1, sender: 'bot', text: 'Hello. I can help you query the healthcare facility database. Ask about bed capacity, equipment status, or doctor availability.', timestamp: '14:30' },
        { id: 2, sender: 'user', text: 'Show facilities in California with ICU bed occupancy below 60%', timestamp: '14:31' },
        { id: 3, sender: 'system', text: 'Query executed: SELECT * FROM facilities WHERE state = "CA" AND icu_occupancy < 60', timestamp: '14:31' },
        { id: 4, sender: 'bot', text: 'Found 12 facilities in California with ICU occupancy < 60%:\n1. Stanford Hospital - 48% occupancy\n2. UCLA Medical - 52%\n3. Cedars-Sinai - 55%\n...', timestamp: '14:31' },
    ]);
    const [input, setInput] = useState('');

    const quickQueries = [
        'List facilities with MRI machine shortage',
        'Show bed occupancy by state',
        'Find clinics with doctor ratio < 1:100',
        'Equipment maintenance due this month'
    ];

    const sendMessage = () => {
        if (!input.trim()) return;

        const newMessages = [
            ...messages,
            { id: messages.length + 1, sender: 'user', text: input, timestamp: '14:32' },
            { id: messages.length + 2, sender: 'system', text: `Query executed: ${input.toUpperCase().slice(0, 50)}...`, timestamp: '14:32' },
            { id: messages.length + 3, sender: 'bot', text: 'Processing your request... I found 8 facilities matching your criteria.', timestamp: '14:32' },
        ];

        setMessages(newMessages);
        setInput('');
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    return (
        <div className="h-full flex flex-col p-6">
            {/* Header */}
            <div className="mb-6">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-primary-soft flex items-center justify-center">
                            <Database size={20} className="text-primary" />
                        </div>
                        <div>
                            <h1 className="text-[20px] font-semibold">Database Assistant</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <div className="w-2 h-2 bg-emerald-500" />
                                <span className="text-[13px] text-secondary">Connected to Live DB</span>
                            </div>
                        </div>
                    </div>
                    <div className="text-[13px] text-secondary">
                        Real-time facility data • 2.4M records
                    </div>
                </div>
            </div>

            {/* Message History */}
            <div className="flex-1 bg-panel border border-main mb-6 overflow-y-auto p-4">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`mb-4 ${msg.sender === 'user' ? 'text-right' : msg.sender === 'system' ? 'text-center' : ''}`}
                    >
                        {msg.sender === 'system' ? (
                            <div className="inline-block px-3 py-1 bg-slate-100 border border-soft">
                                <span className="text-[12px] text-secondary italic">{msg.text}</span>
                            </div>
                        ) : (
                            <div
                                className={`inline-block max-w-[80%] p-3 ${msg.sender === 'user'
                                    ? 'bg-primary text-white'
                                    : 'bg-slate-100 border border-soft'
                                    }`}
                            >
                                <div className="whitespace-pre-line text-[14px]">{msg.text}</div>
                                <div className={`text-[11px] mt-1 ${msg.sender === 'user' ? 'text-white/70' : 'text-secondary'}`}>
                                    {msg.timestamp}
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            {/* Quick Queries */}
            <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                    <Zap size={14} className="text-secondary" />
                    <span className="text-[13px] text-secondary">Quick queries</span>
                </div>
                <div className="flex flex-wrap gap-2">
                    {quickQueries.map((query, idx) => (
                        <button
                            key={idx}
                            className="px-3 py-1.5 text-[13px] text-secondary border border-soft hover:bg-slate-50 transition-colors duration-150"
                            onClick={() => setInput(query)}
                        >
                            {query}
                        </button>
                    ))}
                </div>
            </div>

            {/* Input Area */}
            <div className="border border-main bg-panel">
                <div className="p-3">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="Ask about facility capacity, equipment status, doctor availability, or run custom SQL queries..."
                        className="w-full h-20 p-3 border border-soft bg-white text-[14px] resize-none focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                    />
                    <div className="flex items-center justify-between mt-3">
                        <div className="flex items-center gap-2">
                            <Cpu size={14} className="text-secondary" />
                            <span className="text-[12px] text-secondary">AI-powered analysis</span>
                        </div>
                        <button
                            onClick={sendMessage}
                            className="px-4 py-2 bg-primary text-white hover-primary transition-colors duration-150 flex items-center gap-2"
                        >
                            <Send size={16} />
                            <span className="text-[13px] font-medium">Send Query</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}