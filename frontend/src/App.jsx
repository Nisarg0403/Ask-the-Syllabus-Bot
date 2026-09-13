import React, { useState, useEffect, useRef } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import KnowledgeBase from "./components/KnowledgeBase";
import ChatSection from "./components/ChatSection";
import SettingsPanel from "./components/SettingsPanel";
import {
  fetchModels,
  fetchDocuments,
  fetchDbStatus,
  uploadDocument,
  deleteDocument,
  resetDatabase,
  querySyllabus
} from "./services/api";

export default function App() {
  // Global configuration states
  const [selectedModel, setSelectedModel] = useState("");
  const [localModels, setLocalModels] = useState([]);
  const [ollamaOnline, setOllamaOnline] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  // UI States
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [showKnowledgeBase, setShowKnowledgeBase] = useState(false); // Toggle for mobile or specific view

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
  const [messages, setMessages] = useState([]);
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
    loadModels();
    loadDocuments();
    loadDbStatus();
  }, []);

  const loadModels = async () => {
    try {
      const data = await fetchModels();
      setOllamaOnline(data.online);
      setLocalModels(data.models);
      
      if (data.online && data.models.length > 0) {
        const preferred = data.models.find(m => m.includes("qwen3") || m.includes("llama3"));
        setSelectedModel(preferred || data.models[0]);
      }
    } catch (e) {
      setOllamaOnline(false);
    }
  };

  const loadDocuments = async () => {
    try {
      const data = await fetchDocuments();
      setIndexedDocs(data.documents || []);
    } catch (e) {
      console.error("Error loading documents:", e);
    }
  };

  const loadDbStatus = async () => {
    try {
      const data = await fetchDbStatus();
      setDbActive(data.active);
      setDbSize(data.size);
    } catch (e) {
      console.error("Error loading DB status:", e);
    }
  };

  const handleFileUpload = async (e) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);
    setUploadStatus("Uploading file...");
    setUploadProgress(20);

    try {
      setUploadProgress(50);
      setUploadStatus("Extracting content and generating vector embeddings...");
      
      await uploadDocument(files[0], chunkSize, chunkOverlap);

      setUploadProgress(100);
      setUploadStatus("Document indexed successfully!");
      
      setTimeout(() => {
        setUploading(false);
        setUploadStatus("");
        setUploadProgress(0);
        loadDocuments();
        loadDbStatus();
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

  const handleDeleteDocument = async (filename) => {
    if (!confirm(`Are you sure you want to delete ${filename}?`)) return;
    try {
      await deleteDocument(filename);
      loadDocuments();
      loadDbStatus();
    } catch (e) {
      alert(`Error occurred deleting document: ${e.message}`);
    }
  };

  const handleResetDatabase = async () => {
    if (!confirm("Are you sure you want to completely delete your knowledge base? This will wipe all files, embeddings, and clear the chat.")) return;
    try {
      await resetDatabase();
      loadDocuments();
      loadDbStatus();
      setMessages([]);
    } catch (e) {
      alert("Error resetting database.");
    }
  };

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputText;
    if (!text.trim() || streaming) return;

    setInputText("");
    
    const userMsg = {
      sender: "user",
      text: text,
      timeString: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setMessages(prev => [...prev, userMsg]);
    setStreaming(true);

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
      const res = await querySyllabus({
        query: text,
        provider: "Ollama",
        model: selectedModel,
        api_key: "",
        k: docsToRetrieve,
        temperature: temperature
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
    <div className="flex h-screen w-full text-on-surface bg-background overflow-hidden relative font-sans">
      <Sidebar 
        fileInputRef={fileInputRef}
        handleFileUpload={handleFileUpload}
        selectedModel={selectedModel}
        setSelectedModel={setSelectedModel}
        localModels={localModels}
        ollamaOnline={ollamaOnline}
        dbActive={dbActive}
        dbSize={dbSize}
        handleResetDatabase={handleResetDatabase}
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        openSettings={() => setIsSettingsOpen(true)}
      />
      
      <main className="ml-[280px] w-[calc(100%-280px)] h-screen flex overflow-hidden">
        <ChatSection 
          messages={messages}
          selectedModel={selectedModel}
          streaming={streaming}
          inputText={inputText}
          setInputText={setInputText}
          handleSendMessage={handleSendMessage}
          handleKeyPress={handleKeyPress}
          clickSuggestedPrompt={clickSuggestedPrompt}
          chatEndRef={chatEndRef}
          indexedDocsCount={indexedDocs.length}
          openKnowledgeBase={() => setShowKnowledgeBase(true)}
        />
      </main>

      {showKnowledgeBase && (
        <KnowledgeBase 
          onClose={() => setShowKnowledgeBase(false)}
          fileInputRef={fileInputRef}
          uploading={uploading}
          uploadStatus={uploadStatus}
          uploadProgress={uploadProgress}
          indexedDocs={indexedDocs}
          handleDeleteDocument={handleDeleteDocument}
        />
      )}

      <SettingsPanel
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        chunkSize={chunkSize}
        setChunkSize={setChunkSize}
        chunkOverlap={chunkOverlap}
        setChunkOverlap={setChunkOverlap}
        docsToRetrieve={docsToRetrieve}
        setDocsToRetrieve={setDocsToRetrieve}
        temperature={temperature}
        setTemperature={setTemperature}
      />
    </div>
  );
}
