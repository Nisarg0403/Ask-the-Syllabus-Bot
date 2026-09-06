import React, { useState, useEffect, useRef } from "react";
import { 
  School, 
  Brain, 
  Send, 
  RefreshCw, 
  FolderOpen, 
  UploadCloud, 
  FileText, 
  Trash2, 
  HelpCircle, 
  LogOut, 
  Sun, 
  Moon, 
  Search, 
  Bell, 
  History,
  FileCode,
  CheckCircle,
  Database
} from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

// Predefined OpenRouter models
const OPENROUTER_MODELS = [
  "meta-llama/llama-3-8b-instruct:free",
  "mistralai/mistral-7b-instruct:free",
  "qwen/qwen-2.5-7b-instruct:free",
  "google/gemini-flash-1.5",
  "anthropic/claude-3.5-sonnet"
];

// Helper to format simple markdown safely
function renderMarkdown(text) {
  if (!text) return "";
  
  // Replace HTML tag brackets to prevent injection
  let safeText = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold (**text**)
  safeText = safeText.replace(/\*\*(.*?)\*\*/g, '<strong class="text-on-surface font-semibold">$1</strong>');
  
  // Inline code (`code`)
  safeText = safeText.replace(/`(.*?)`/g, '<code class="bg-surface-variant px-1.5 py-0.5 rounded font-mono text-xs text-primary">$1</code>');

  // Bullet points
  const lines = safeText.split("\n");
  const processedLines = lines.map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith("- ")) {
      return `<li class="ml-4 list-disc text-on-surface-variant my-1.5">${trimmed.slice(2)}</li>`;
    }
    if (trimmed.startsWith("* ")) {
      return `<li class="ml-4 list-disc text-on-surface-variant my-1.5">${trimmed.slice(2)}</li>`;
    }
    return trimmed ? `<p class="mb-4 leading-relaxed">${trimmed}</p>` : "";
  });

  return processedLines.join("");
}

export default function App() {
  // Global configuration states
  const [llmProvider, setLlmProvider] = useState("Ollama");
  const [selectedModel, setSelectedModel] = useState("");
  const [localModels, setLocalModels] = useState([]);
  const [ollamaOnline, setOllamaOnline] = useState(false);
  const [openRouterKey, setOpenRouterKey] = useState("");
  const [customModel, setCustomModel] = useState("");
  const [darkMode, setDarkMode] = useState(false);

  // RAG Sliders states
  const [chunkSize, setChunkSize] = useState(1024);
  const [chunkOverlap, setChunkOverlap] = useState(200);
  const [docsToRetrieve, setDocsToRetrieve] = useState(4);
  const [temperature, setTemperature] = useState(0.3);

  // Database metadata states
  const [dbActive, setDbActive] = useState(false);
  const [dbSize, setDbSize] = useState("0 MB");
  const [indexedDocs, setIndexedDocs] = useState([]);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");
  const [uploadProgress, setUploadProgress] = useState(0);

  // Chat states
  const [messages, setMessages] = useState([
    {
      sender: "bot",
      text: "Hello! I'm ready to answer questions about your loaded syllabi. Please upload PDF files in the Knowledge Base pane or make sure your database is ready.",
      sources: [],
      timeString: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [streaming, setStreaming] = useState(false);

  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  // Apply dark mode class
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
  }, [darkMode]);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load system data on startup
  useEffect(() => {
    fetchModels();
    fetchDocuments();
    fetchDbStatus();
  }, []);

  // Fetch Ollama models
  const fetchModels = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/models`);
      const data = await res.json();
      setOllamaOnline(data.online);
      setLocalModels(data.models);
      
      // Auto-set selected model if Ollama is online
      if (data.online && data.models.length > 0) {
        const preferred = data.models.find(m => m.includes("qwen3") || m.includes("llama3"));
        setSelectedModel(preferred || data.models[0]);
      } else {
        setSelectedModel(OPENROUTER_MODELS[0]);
      }
    } catch (e) {
      setOllamaOnline(false);
      setSelectedModel(OPENROUTER_MODELS[0]);
    }
  };

  // Fetch indexed documents list
  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/documents`);
      const data = await res.json();
      setIndexedDocs(data.documents || []);
    } catch (e) {
      console.error("Error loading documents:", e);
    }
  };

  // Fetch vector storage status
  const fetchDbStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      const data = await res.json();
      setDbActive(data.active);
      setDbSize(data.size);
    } catch (e) {
      console.error("Error loading DB status:", e);
    }
  };

  // LLM Provider changed
  const handleProviderChange = (provider) => {
    setLlmProvider(provider);
    if (provider === "Ollama") {
      if (localModels.length > 0) {
        setSelectedModel(localModels[0]);
      } else {
        setSelectedModel("llama3");
      }
    } else {
      setSelectedModel(OPENROUTER_MODELS[0]);
    }
  };

  // Upload file handler
  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadStatus("Uploading file...");
    setUploadProgress(20);

    const formData = new FormData();
    formData.append("file", files[0]);
    formData.append("chunk_size", chunkSize);
    formData.append("chunk_overlap", chunkOverlap);

    try {
      setUploadProgress(50);
      setUploadStatus("Extracting content and generating vector embeddings...");
      
      const res = await fetch(`${API_BASE}/api/upload`, {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Upload failed");
      }

      setUploadProgress(100);
      setUploadStatus("Document indexed successfully!");
      
      setTimeout(() => {
        setUploading(false);
        setUploadStatus("");
        setUploadProgress(0);
        fetchDocuments();
        fetchDbStatus();
      }, 1500);

    } catch (err) {
      setUploadStatus(`Error: ${err.message}`);
      setUploadProgress(0);
      setTimeout(() => {
        setUploading(false);
        setUploadStatus("");
      }, 4000);
    }
  };

  // Delete document handler
  const handleDeleteDocument = async (filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/documents/${filename}`, {
        method: "DELETE"
      });
      if (res.ok) {
        fetchDocuments();
        fetchDbStatus();
      } else {
        const err = await res.json();
        alert(`Failed to delete: ${err.detail}`);
      }
    } catch (e) {
      alert("Error occurred deleting document.");
    }
  };

  // Reset database handler
  const handleResetDatabase = async () => {
    if (!confirm("Are you sure you want to completely delete your knowledge base? This will wipe all files, embeddings, and clear the chat.")) return;
    try {
      const res = await fetch(`${API_BASE}/api/reset`, { method: "POST" });
      if (res.ok) {
        fetchDocuments();
        fetchDbStatus();
        setMessages([
          {
            sender: "bot",
            text: "Database has been reset. Please upload syllabus PDFs to begin anew.",
            sources: [],
            timeString: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          }
        ]);
      }
    } catch (e) {
      alert("Error resetting database.");
    }
  };

  // Query RAG streaming handler
  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputText;
    if (!text.trim() || streaming) return;

    setInputText("");
    
    // Add user message
    const userMsg = {
      sender: "user",
      text: text,
      timeString: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setStreaming(true);

    // Placeholder bot response
    const botMsgPlaceholder = {
      sender: "bot",
      text: "",
      sources: [],
      responseTime: "",
      timeString: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, botMsgPlaceholder]);

    const startTime = Date.now();

    try {
      const finalModel = (llmProvider === "OpenRouter" && customModel) ? customModel : selectedModel;
      const res = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          provider: llmProvider,
          model: finalModel,
          api_key: openRouterKey,
          k: docsToRetrieve,
          temperature: temperature
        })
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Query failed");
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let activeSources = [];
      let activeText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = null;

        for (let line of lines) {
          if (line.endsWith("\r")) {
            line = line.slice(0, -1);
          }
          if (!line) continue;

          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            let data = line.slice(5);
            if (data.startsWith(" ")) {
              data = data.slice(1);
            }
            
            if (currentEvent === "sources") {
              activeSources = JSON.parse(data.trim());
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                last.sources = activeSources;
                return updated;
              });
            } else if (currentEvent === "token") {
              activeText += data;
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                last.text = activeText;
                return updated;
              });
            } else if (currentEvent === "error") {
              const err = JSON.parse(data.trim());
              activeText = `Error: ${err.detail}`;
              setMessages(prev => {
                const updated = [...prev];
                const last = updated[updated.length - 1];
                last.text = activeText;
                return updated;
              });
            }
          }
        }
      }

      const responseTime = ((Date.now() - startTime) / 1000).toFixed(1) + "s";
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        last.responseTime = responseTime;
        return updated;
      });

    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        last.text = `Could not get response. ${err.message}`;
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clickSuggestedPrompt = (promptText) => {
    if (!streaming) {
      handleSendMessage(promptText);
    }
  };

  return (
    <div className="flex h-screen w-full text-on-surface bg-background overflow-hidden relative">
      
      {/* Top Header App Bar */}
      <header className="fixed top-0 right-0 w-[calc(100%-280px)] z-50 bg-background/80 backdrop-blur-md border-b border-outline-variant flex justify-between items-center h-16 px-container-padding">
        <div className="flex items-center gap-4">
          <h1 className="font-serif text-xl font-semibold text-on-surface">
            Ask-the-Syllabus Bot
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative hidden lg:block group rounded-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant w-4 h-4" />
            <input 
              className="bg-surface-variant border border-outline-variant text-on-surface rounded-full py-1.5 pl-9 pr-4 text-xs focus:outline-none focus:border-primary/60 w-48 focus:w-60 transition-all duration-300 placeholder:text-on-surface-variant" 
              placeholder="Search syllabus..." 
              type="text"
            />
          </div>
          <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-variant/40">
            <Bell className="w-4.5 h-4.5" />
          </button>
          <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-variant/40">
            <History className="w-4.5 h-4.5" />
          </button>
          <div className="h-8 w-8 rounded-full bg-surface-variant flex items-center justify-center border border-outline-variant cursor-pointer">
            <span className="font-serif text-xs font-semibold text-primary">A</span>
          </div>
        </div>
      </header>

      {/* Left Sidebar Navigation */}
      <nav className="fixed h-full w-[280px] left-0 top-0 bg-surface-container border-r border-outline-variant flex flex-col py-6 z-40">
        
        {/* Brand Header */}
        <div className="px-6 mb-6 flex items-center gap-3">
          <div className="h-9 w-9 rounded-xl bg-primary text-white flex items-center justify-center shrink-0 shadow-sm">
            <School className="w-5 h-5" />
          </div>
          <div>
            <h2 className="font-serif text-base font-semibold text-on-surface leading-tight">Syllabus Bot</h2>
            <span className="text-[10px] text-on-surface-variant font-medium flex items-center gap-1.5 mt-0.5">
              <span className="h-1.5 w-1.5 rounded-full bg-primary/60 animate-pulse-dot"></span>
              V2.0 Active
            </span>
          </div>
        </div>

        {/* Upload Action */}
        <div className="px-6 mb-4">
          <button 
            onClick={() => fileInputRef.current?.click()}
            className="w-full py-2 px-4 bg-primary text-white rounded-xl font-medium text-xs flex items-center justify-center gap-2 hover:bg-primary-hover transition-colors shadow-sm active:scale-[0.99]"
          >
            <UploadCloud className="w-4 h-4" />
            Upload Syllabus PDF
          </button>
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            accept=".pdf" 
            className="hidden" 
          />
        </div>

        {/* Settings Links */}
        <div className="flex-1 overflow-y-auto px-3 flex flex-col gap-1">
          <a className="flex items-center gap-3 px-3 py-2 rounded-xl text-on-surface font-semibold bg-surface-variant" href="#">
            <Brain className="w-4.5 h-4.5 text-primary" />
            <span className="text-xs">Parameters & Model</span>
          </a>

          {/* Configuration Form */}
          <div className="mt-4 px-3 flex flex-col gap-4">
            
            {/* LLM Provider Toggle */}
            <div>
              <label className="text-[10px] font-semibold text-on-surface-variant mb-1.5 block uppercase tracking-wider">
                LLM Backend
              </label>
              <div className="flex bg-surface-variant rounded-xl p-0.5 border border-outline-variant/60">
                <button 
                  onClick={() => handleProviderChange("Ollama")}
                  className={`flex-1 py-1 text-[11px] font-medium rounded-lg transition-all ${
                    llmProvider === "Ollama" 
                      ? "bg-background text-on-surface border border-outline-variant/40 shadow-sm" 
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  Ollama
                </button>
                <button 
                  onClick={() => handleProviderChange("OpenRouter")}
                  className={`flex-1 py-1 text-[11px] font-medium rounded-lg transition-all ${
                    llmProvider === "OpenRouter" 
                      ? "bg-background text-on-surface border border-outline-variant/40 shadow-sm" 
                      : "text-on-surface-variant hover:text-on-surface"
                  }`}
                >
                  OpenRouter
                </button>
              </div>
            </div>

            {/* Model Selection Dropdown */}
            {llmProvider === "Ollama" ? (
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-[10px] font-semibold text-on-surface-variant block uppercase tracking-wider">
                    Active Model
                  </label>
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full border ${
                    ollamaOnline 
                      ? "bg-surface-variant text-on-surface-variant border-outline-variant/60" 
                      : "bg-red-500/10 text-red-500 border-red-500/20"
                  }`}>
                    {ollamaOnline ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>
                {ollamaOnline && localModels.length > 0 ? (
                  <div className="relative rounded-lg">
                    <select 
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-surface-variant border border-outline-variant/80 text-xs text-on-surface rounded-xl py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-primary/80 cursor-pointer"
                    >
                      {localModels.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-sm">
                      expand_more
                    </span>
                  </div>
                ) : (
                  <div>
                    <input 
                      type="text" 
                      placeholder="e.g. llama3"
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-surface-variant border border-outline-variant text-xs text-on-surface rounded-xl py-2 px-3 focus:outline-none focus:border-primary/80"
                    />
                    <span className="text-[9px] text-on-surface-variant mt-1.5 block">Ollama server offline. Enter model manually.</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-3">
                {/* OpenRouter API Key */}
                <div>
                  <label className="text-[10px] font-semibold text-on-surface-variant mb-1 block uppercase tracking-wider">
                    API Key
                  </label>
                  <input 
                    type="password" 
                    placeholder="sk-or-..."
                    value={openRouterKey}
                    onChange={(e) => setOpenRouterKey(e.target.value)}
                    className="w-full bg-surface-variant border border-outline-variant text-xs text-on-surface rounded-xl py-2 px-3 focus:outline-none focus:border-primary/80 font-mono"
                  />
                </div>
                {/* OpenRouter Model Select */}
                <div>
                  <label className="text-[10px] font-semibold text-on-surface-variant mb-1 block uppercase tracking-wider">
                    Active Cloud Model
                  </label>
                  <div className="relative rounded-lg">
                    <select 
                      value={selectedModel}
                      onChange={(e) => setSelectedModel(e.target.value)}
                      className="w-full bg-surface-variant border border-outline-variant text-xs text-on-surface rounded-xl py-2 pl-3 pr-8 appearance-none focus:outline-none focus:border-primary/80 cursor-pointer"
                    >
                      {OPENROUTER_MODELS.map(m => (
                        <option key={m} value={m}>{m}</option>
                      ))}
                    </select>
                    <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none text-sm">
                      expand_more
                    </span>
                  </div>
                </div>
                {/* OpenRouter Custom Model Input */}
                <div>
                  <label className="text-[10px] font-semibold text-on-surface-variant mb-1 block uppercase tracking-wider">
                    Or Custom Model ID
                  </label>
                  <input 
                    type="text" 
                    placeholder="e.g. deepseek/deepseek-chat"
                    value={customModel}
                    onChange={(e) => setCustomModel(e.target.value)}
                    className="w-full bg-surface-variant border border-outline-variant text-xs text-on-surface rounded-xl py-2 px-3 focus:outline-none focus:border-primary/80 font-mono"
                  />
                </div>
              </div>
            )}

            {/* RAG Hyperparameters Sliders */}
            <div className="border-t border-outline-variant pt-4 flex flex-col gap-4">
              <h3 className="text-[10px] font-semibold text-on-surface-variant uppercase tracking-wider">
                RAG Tuning
              </h3>
              
              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant">Chunk Size</span>
                  <span className="text-primary font-mono font-medium">{chunkSize}</span>
                </div>
                <input 
                  type="range" 
                  min="256" 
                  max="2048" 
                  step="64"
                  value={chunkSize}
                  onChange={(e) => setChunkSize(parseInt(e.target.value))}
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant">Chunk Overlap</span>
                  <span className="text-primary font-mono font-medium">{chunkOverlap}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="500" 
                  step="25"
                  value={chunkOverlap}
                  onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant">Retrieve Count (k)</span>
                  <span className="text-primary font-mono font-medium">{docsToRetrieve}</span>
                </div>
                <input 
                  type="range" 
                  min="1" 
                  max="10" 
                  step="1"
                  value={docsToRetrieve}
                  onChange={(e) => setDocsToRetrieve(parseInt(e.target.value))}
                />
              </div>

              <div>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-on-surface-variant">Temperature</span>
                  <span className="text-primary font-mono font-medium">{temperature.toFixed(1)}</span>
                </div>
                <input 
                  type="range" 
                  min="0" 
                  max="1" 
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Database Status Panel */}
        <div className="mt-auto px-6 pt-4 border-t border-outline-variant">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-on-surface-variant flex items-center gap-1.5 font-medium">
              <Database className="w-3.5 h-3.5" />
              Vector Store
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-variant text-on-surface-variant border border-outline-variant/60 font-mono">
              {dbActive ? "ACTIVE" : "EMPTY"}
            </span>
          </div>
          <div className="flex justify-between items-center text-xs text-on-surface-variant mb-4">
            <span>Size:</span>
            <span className="font-mono text-primary font-medium">{dbSize}</span>
          </div>
          <button 
            onClick={handleResetDatabase}
            className="w-full py-2 text-xs border border-error/20 text-error hover:bg-error/5 hover:border-error/40 rounded-xl transition-all flex justify-center items-center gap-1.5 active:scale-[0.98]"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Reset Database
          </button>
        </div>

        {/* Theme Toggle Button */}
        <div className="px-6 mt-4 flex items-center justify-between border-t border-outline-variant/40 pt-4">
          <span className="text-xs text-on-surface-variant font-medium">Theme Mode</span>
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-xl bg-surface-variant hover:bg-surface-variant/80 border border-outline-variant/40"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>

      </nav>

      {/* Main Workspace (Split Screen) */}
      <main className="ml-[280px] mt-16 w-[calc(100%-280px)] h-[calc(100vh-64px)] flex overflow-hidden">
        
        {/* Left Pane: Document Ingestion / Storage */}
        <section className="w-1/2 h-full border-r border-outline-variant p-8 flex flex-col gap-6 overflow-y-auto relative bg-background">
          
          <h2 className="font-serif text-lg font-semibold flex items-center gap-2 text-on-surface">
            <FolderOpen className="w-5 h-5 text-primary" />
            Knowledge Base
          </h2>

          {/* Upload Dropzone */}
          <div 
            onClick={() => fileInputRef.current?.click()}
            className="rounded-xl p-8 flex flex-col items-center justify-center text-center border-dashed border border-outline-variant/80 bg-surface-container/30 hover:bg-surface-container/60 hover:border-primary/50 transition-colors cursor-pointer group z-10 relative overflow-hidden"
          >
            <div className="h-14 w-14 rounded-full bg-surface-variant flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-300">
              <UploadCloud className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-sm font-medium text-on-surface mb-2">Drop Syllabus PDFs here or browse</h3>
            <p className="text-xs text-on-surface-variant max-w-xs leading-relaxed">
              Files are split into chunks and indexed locally. Max size: 50MB.
            </p>
          </div>

          {/* Indexing Progress Indicator */}
          {uploading && (
            <div className="rounded-xl p-4 border border-outline-variant bg-surface-container/40 z-10 flex flex-col gap-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                  <span className="text-xs font-medium text-on-surface">Processing...</span>
                </div>
                <span className="text-xs font-mono text-primary">{uploadProgress}%</span>
              </div>
              <p className="text-[10px] text-on-surface-variant truncate">{uploadStatus}</p>
              <div className="h-1.5 w-full bg-outline-variant/40 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full relative transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                >
                </div>
              </div>
            </div>
          )}

          {/* Indexed Document List */}
          <div className="flex-1 flex flex-col z-10">
            <h3 className="text-[10px] font-semibold text-on-surface-variant mb-3 uppercase tracking-wider font-sans">
              Indexed Syllabi ({indexedDocs.length})
            </h3>
            <div className="flex flex-col gap-2">
              {indexedDocs.length > 0 ? (
                indexedDocs.map((doc, idx) => (
                  <div 
                    key={idx} 
                    className="rounded-xl p-3.5 flex items-center gap-3.5 hover:bg-surface-variant/40 transition-colors border border-outline-variant/60 bg-surface-container/20 group"
                  >
                    <div className="h-9 w-9 rounded-lg bg-surface-variant flex items-center justify-center shrink-0">
                      <FileText className="w-5 h-5 text-primary/80" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-xs font-semibold text-on-surface truncate group-hover:text-primary transition-colors">
                        {doc.filename}
                      </h4>
                      <div className="flex items-center gap-2 text-[10px] text-on-surface-variant mt-0.5">
                        <span>{doc.size}</span>
                        <span className="h-1 w-1 rounded-full bg-outline-variant"></span>
                        <span>{doc.indexed_at}</span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDocument(doc.filename);
                      }}
                      className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error/10 transition-all rounded-lg active:scale-95"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center text-xs text-on-surface-variant border border-dashed border-outline-variant/60 rounded-xl bg-surface-container/10">
                  No documents indexed yet. Build your knowledge base above!
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Right Pane: Syllabus Assistant Chat */}
        <section className="w-1/2 h-full bg-background flex flex-col relative border-l border-outline-variant/60">
          
          {/* Chat Pane Header */}
          <div className="h-14 border-b border-outline-variant/60 px-6 flex items-center justify-between z-20 absolute top-0 w-full bg-background/90 backdrop-blur-sm">
            <div className="flex items-center gap-2">
              <span className="font-serif text-sm font-medium text-on-surface">
                Syllabus Assistant
              </span>
            </div>
            <div className="flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-surface-variant border border-outline-variant/60">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-dot"></span>
              <span className="text-[9px] font-sans font-semibold text-on-surface-variant uppercase tracking-wider">
                {llmProvider === "OpenRouter" ? selectedModel.split("/").pop().toUpperCase() : selectedModel.toUpperCase()}
              </span>
            </div>
          </div>

          {/* Chat Thread Messages */}
          <div className="flex-1 overflow-y-auto px-8 pt-20 pb-6 flex flex-col gap-6 custom-scrollbar">
            <div className="max-w-[840px] w-full mx-auto flex flex-col gap-6">
              {messages.map((msg, index) => (
                <div 
                  key={index}
                  className={`flex gap-4 ${msg.sender === "user" ? "max-w-[85%] self-end" : "max-w-full"} transition-all duration-300`}
                >
                {/* Avatar Icon (User only) */}
                {msg.sender === "user" && (
                  <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-surface-variant border border-outline-variant">
                    <span className="font-serif text-xs font-semibold text-primary">U</span>
                  </div>
                )}

                {/* Message Bubble Column */}
                <div className={`flex flex-col gap-1 ${msg.sender === "user" ? "items-end" : "items-start"} w-full`}>
                  
                  {/* Bubble Content */}
                  {msg.sender === "user" ? (
                    <div className="bg-surface-variant border border-outline-variant/60 text-on-surface p-4 rounded-2xl rounded-tr-sm text-sm shadow-sm max-w-lg">
                      <div className="font-serif leading-relaxed text-xs">
                        {msg.text}
                      </div>
                    </div>
                  ) : (
                    // Bot response flat-stack style (no card, no bubble, clean serif text)
                    <div className="w-full py-2">
                      <div className="flex items-center gap-2 text-[10px] text-on-surface-variant mb-2">
                        <span className="font-semibold text-primary">Syllabus Bot</span>
                        {msg.responseTime && (
                          <span className="bg-surface-variant px-1.5 py-0.5 rounded border border-outline-variant/60">
                            {msg.responseTime}
                          </span>
                        )}
                      </div>
                      
                      {msg.text ? (
                        <div 
                          className="prose prose-invert prose-sm max-w-none text-[15px] font-serif text-on-surface leading-relaxed"
                          dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                        />
                      ) : (
                        <div className="flex gap-1 py-2">
                          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                          <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                        </div>
                      )}

                      {/* Expandable Citations for Bot messages */}
                      {msg.sources && msg.sources.length > 0 && (
                        <details className="mt-4 group bg-surface-container/20 rounded-xl border border-outline-variant overflow-hidden">
                          <summary className="px-3.5 py-2 text-[10px] font-semibold text-on-surface-variant cursor-pointer flex items-center justify-between hover:bg-surface-variant/40 transition-colors outline-none">
                            <div className="flex items-center gap-2">
                              <FileText className="w-3.5 h-3.5 text-primary" />
                              <span>View {msg.sources.length} Retrieved Sources</span>
                            </div>
                            <span className="material-symbols-outlined text-[14px] transition-transform group-open:rotate-180">
                              expand_more
                            </span>
                          </summary>
                          <div className="p-3.5 border-t border-outline-variant bg-surface-container/10 flex flex-col gap-2 max-h-48 overflow-y-auto">
                            {msg.sources.map((src, idx) => (
                              <div key={idx} className="p-3 rounded-lg bg-background border border-outline-variant text-[11px] leading-relaxed">
                                <div className="flex justify-between items-center mb-1.5 text-primary">
                                  <span className="font-semibold truncate max-w-[70%]">{src.source}</span>
                                  <span className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[10px]">Page {src.page}</span>
                                </div>
                                <p className="text-on-surface-variant italic font-serif leading-relaxed whitespace-pre-wrap">
                                  "{src.content}"
                                </p>
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  )}

                </div>
              </div>
            ))}
            </div>
            <div ref={chatEndRef} />
          </div>

          {/* Bottom Chat Input Area */}
          <div className="p-6 bg-gradient-to-t from-background via-background to-transparent relative z-20">
            <div className="max-w-[840px] w-full mx-auto">
            
            {/* Suggested Quick Prompt Chips */}
            <div className="flex gap-2 mb-4 overflow-x-auto pb-1 custom-scrollbar scroll-smooth">
              <button 
                onClick={() => clickSuggestedPrompt("What is the grading policy?")}
                className="whitespace-nowrap px-3.5 py-2 text-[11px] rounded-full border border-outline-variant text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/30 transition-all duration-300 font-medium"
              >
                What is the grading policy?
              </button>
              <button 
                onClick={() => clickSuggestedPrompt("List all exam dates")}
                className="whitespace-nowrap px-3.5 py-2 text-[11px] rounded-full border border-outline-variant text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/30 transition-all duration-300 font-medium"
              >
                List all exam dates
              </button>
              <button 
                onClick={() => clickSuggestedPrompt("Are there any required textbooks?")}
                className="whitespace-nowrap px-3.5 py-2 text-[11px] rounded-full border border-outline-variant text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/30 transition-all duration-300 font-medium"
              >
                Are there required textbooks?
              </button>
            </div>

            {/* Main Textarea Input Bar */}
            <div className="relative group rounded-xl bg-surface-variant border border-outline-variant focus-within:border-primary/60 transition-colors duration-200">
              <textarea 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyPress}
                className="w-full bg-transparent text-sm text-on-surface py-3.5 pl-4 pr-12 resize-none focus:outline-none focus:ring-0 border-none placeholder:text-on-surface-variant" 
                placeholder="Ask about your syllabus..." 
                rows="1" 
                style={{ minHeight: "48px" }}
                disabled={streaming}
              />
              <button 
                onClick={() => handleSendMessage()}
                disabled={streaming || !inputText.trim()}
                className={`absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 rounded-lg flex items-center justify-center transition-colors ${
                  streaming || !inputText.trim()
                    ? "text-on-surface-variant bg-transparent cursor-not-allowed"
                    : "bg-primary text-white hover:bg-primary-hover shadow-sm"
                }`}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            
            <div className="text-center mt-3">
              <span className="text-[10px] text-on-surface-variant uppercase tracking-wider font-semibold">
                AI can make mistakes. Verify important academic details.
              </span>
            </div>
            </div>

          </div>

        </section>

      </main>
    </div>
  );
}
