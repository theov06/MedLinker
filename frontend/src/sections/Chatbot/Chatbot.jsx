// Chatbot.jsx - Database Consultation Interface
import { Send, Database, Zap, Cpu, Save, Upload, Trash2 } from "lucide-react";
import { useState, useEffect } from "react";
import { apiService } from "../../services/api";
import { formatAnswer, formatCitations, enhanceAnswer } from "../../utils/responseFormatter";
import { createFacilityNameMap, createRegionNameMap, enhanceAnswerWithNames } from "../../utils/facilityNameMapper";

const STORAGE_KEY = 'medlinker_chat_history';

export function Chatbot() {
    const initialMessage = { 
        id: 1, 
        sender: 'bot', 
        text: '👋 Hello! I\'m your Healthcare Facility Assistant.\n\nI can help you:\n• Find regions with critical healthcare gaps\n• Identify facilities offering specific services\n• Analyze medical desert scores\n• Discover missing healthcare capabilities\n\nAsk me anything about healthcare facilities and regions!', 
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };

    const [messages, setMessages] = useState([initialMessage]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [facilitiesCount, setFacilitiesCount] = useState(0);
    const [regionsCount, setRegionsCount] = useState(0);
    const [facilities, setFacilities] = useState([]);
    const [regions, setRegions] = useState([]);
    const [facilityNameMap, setFacilityNameMap] = useState(new Map());
    const [regionNameMap, setRegionNameMap] = useState(new Map());
    const [saveStatus, setSaveStatus] = useState('');

    useEffect(() => {
        // Load facility and region counts
        apiService.getFacilities()
            .then(data => {
                setFacilitiesCount(data.length);
                setFacilities(data);
                setFacilityNameMap(createFacilityNameMap(data));
            })
            .catch(err => console.error('Failed to load facilities:', err));
        
        apiService.getRegions()
            .then(data => {
                setRegionsCount(data.length);
                setRegions(data);
                setRegionNameMap(createRegionNameMap(data));
            })
            .catch(err => console.error('Failed to load regions:', err));

        // Load saved conversation from localStorage
        loadConversation();
    }, []);

    const saveConversation = () => {
        try {
            const conversationData = {
                messages,
                timestamp: new Date().toISOString(),
                facilitiesCount,
                regionsCount
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(conversationData));
            setSaveStatus('Saved!');
            setTimeout(() => setSaveStatus(''), 2000);
        } catch (error) {
            console.error('Failed to save conversation:', error);
            setSaveStatus('Save failed');
            setTimeout(() => setSaveStatus(''), 2000);
        }
    };

    const loadConversation = () => {
        try {
            const saved = localStorage.getItem(STORAGE_KEY);
            if (saved) {
                const conversationData = JSON.parse(saved);
                setMessages(conversationData.messages || [initialMessage]);
            }
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    };

    const clearConversation = () => {
        if (window.confirm('Are you sure you want to clear the conversation history?')) {
            setMessages([initialMessage]);
            localStorage.removeItem(STORAGE_KEY);
            setSaveStatus('Cleared');
            setTimeout(() => setSaveStatus(''), 2000);
        }
    };

    const exportConversation = () => {
        try {
            const conversationData = {
                messages,
                timestamp: new Date().toISOString(),
                facilitiesCount,
                regionsCount
            };
            const dataStr = JSON.stringify(conversationData, null, 2);
            const dataBlob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `medlinker-chat-${new Date().toISOString().split('T')[0]}.json`;
            link.click();
            URL.revokeObjectURL(url);
            setSaveStatus('Exported!');
            setTimeout(() => setSaveStatus(''), 2000);
        } catch (error) {
            console.error('Failed to export conversation:', error);
            setSaveStatus('Export failed');
            setTimeout(() => setSaveStatus(''), 2000);
        }
    };

    const importConversation = (event) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const conversationData = JSON.parse(e.target.result);
                setMessages(conversationData.messages || [initialMessage]);
                localStorage.setItem(STORAGE_KEY, JSON.stringify(conversationData));
                setSaveStatus('Imported!');
                setTimeout(() => setSaveStatus(''), 2000);
            } catch (error) {
                console.error('Failed to import conversation:', error);
                setSaveStatus('Import failed');
                setTimeout(() => setSaveStatus(''), 2000);
            }
        };
        reader.readAsText(file);
        event.target.value = ''; // Reset input
    };

    const quickQueries = [
        'Which regions have the highest desert score?',
        'What facilities offer surgery?',
        'Show regions lacking C-section services',
        'List all verified facilities'
    ];

    const sendMessage = async () => {
        if (!input.trim() || loading) return;

        const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const userMessage = { id: messages.length + 1, sender: 'user', text: input, timestamp };
        
        setMessages(prev => [...prev, userMessage]);
        setLoading(true);
        setInput('');

        try {
            // Call real backend API
            const response = await apiService.askQuestion(input);
            
            // Use backend response directly (backend now includes facility names)
            const botMessage = {
                id: messages.length + 2,
                sender: 'bot',
                text: response.answer,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                citations: response.citations,
                traceId: response.trace_id
            };

            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            const errorMessage = {
                id: messages.length + 2,
                sender: 'bot',
                text: `Error: ${error.message}. Please make sure the backend is running and data is available.`,
                timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setLoading(false);
        }
    };

    // Auto-save conversation after each message
    useEffect(() => {
        if (messages.length > 1) {
            saveConversation();
        }
    }, [messages]);

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
                    <div className="flex items-center gap-3">
                        <div className="text-[13px] text-secondary">
                            Real-time facility data • {facilitiesCount} facilities • {regionsCount} regions
                        </div>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={saveConversation}
                                className="px-3 py-1.5 text-[13px] border border-soft hover:bg-slate-50 transition-colors duration-150 flex items-center gap-1.5"
                                title="Save conversation"
                            >
                                <Save size={14} />
                                Save
                            </button>
                            <label className="px-3 py-1.5 text-[13px] border border-soft hover:bg-slate-50 transition-colors duration-150 flex items-center gap-1.5 cursor-pointer" title="Import conversation">
                                <Upload size={14} />
                                Import
                                <input
                                    type="file"
                                    accept=".json"
                                    onChange={importConversation}
                                    className="hidden"
                                />
                            </label>
                            <button
                                onClick={exportConversation}
                                className="px-3 py-1.5 text-[13px] border border-soft hover:bg-slate-50 transition-colors duration-150"
                                title="Export conversation"
                            >
                                Export
                            </button>
                            <button
                                onClick={clearConversation}
                                className="px-3 py-1.5 text-[13px] border border-soft hover:bg-red-50 hover:text-red-600 transition-colors duration-150 flex items-center gap-1.5"
                                title="Clear conversation"
                            >
                                <Trash2 size={14} />
                                Clear
                            </button>
                            {saveStatus && (
                                <span className="text-[13px] text-emerald-600 font-medium">{saveStatus}</span>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Message History */}
            <div className="flex-1 bg-panel border border-main mb-6 overflow-y-auto p-4">
                {messages.map((msg) => (
                    <div
                        key={msg.id}
                        className={`mb-4 ${msg.sender === 'user' ? 'text-right' : ''}`}
                    >
                        <div
                            className={`inline-block max-w-[80%] p-3 ${msg.sender === 'user'
                                ? 'bg-primary text-white'
                                : 'bg-slate-100 border border-soft'
                                }`}
                        >
                            <div className="whitespace-pre-line text-[14px]">{msg.text}</div>
                            {msg.citations && msg.citations.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-slate-300">
                                    <div className="text-[11px] font-semibold mb-1">Citations ({msg.citations.length}):</div>
                                    {msg.citations.map((citation, idx) => (
                                        <div key={idx} className="text-[11px] text-slate-600 mb-1">
                                            • {citation.snippet}
                                        </div>
                                    ))}
                                </div>
                            )}
                            <div className={`text-[11px] mt-1 ${msg.sender === 'user' ? 'text-white/70' : 'text-secondary'}`}>
                                {msg.timestamp}
                            </div>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="mb-4">
                        <div className="inline-block max-w-[80%] p-3 bg-slate-100 border border-soft">
                            <div className="text-[14px] text-secondary">Thinking...</div>
                        </div>
                    </div>
                )}
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
                            disabled={loading || !input.trim()}
                            className="px-4 py-2 bg-primary text-white hover-primary transition-colors duration-150 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <Send size={16} />
                            <span className="text-[13px] font-medium">{loading ? 'Sending...' : 'Send Query'}</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}