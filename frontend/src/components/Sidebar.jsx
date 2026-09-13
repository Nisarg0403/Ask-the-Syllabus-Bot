import React from "react";
import { 
  School, 
  UploadCloud, 
  Brain, 
  Database, 
  Trash2, 
  Sun, 
  Moon,
  MessageSquarePlus,
  BookOpen
} from "lucide-react";
import ModelSelector from "./ModelSelector";

export default function Sidebar({
  fileInputRef,
  handleFileUpload,
  selectedModel,
  setSelectedModel,
  localModels,
  ollamaOnline,
  dbActive,
  dbSize,
  handleResetDatabase,
  darkMode,
  setDarkMode,
  openSettings,
  openEvaluation
}) {
  return (
    <nav className="fixed h-full w-[280px] left-0 top-0 bg-surface-container border-r border-outline-variant flex flex-col py-6 z-40 transition-colors">
      
      {/* Brand Header */}
      <div className="px-5 mb-6 flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-primary text-white flex items-center justify-center shrink-0 shadow-sm">
          <School className="w-5 h-5" />
        </div>
        <div>
          <h2 className="font-serif text-lg font-semibold text-on-surface leading-tight tracking-tight">Syllabus Bot</h2>
          <span className="text-xs text-on-surface-variant font-medium flex items-center gap-1.5 mt-0.5">
            <span className="h-2 w-2 rounded-full bg-primary/80 animate-pulse-dot"></span>
            Academic Assistant
          </span>
        </div>
      </div>

      <div className="px-5 mb-6">
        <button 
          onClick={() => {}} // Reset chat
          className="w-full py-2.5 px-4 bg-background border border-border text-on-surface rounded-xl font-medium text-sm flex items-center gap-2 hover:border-primary hover:text-primary transition-colors shadow-sm"
        >
          <MessageSquarePlus className="w-4 h-4" />
          New Chat
        </button>
      </div>

      <div className="px-5 mb-2 text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
        Model Settings
      </div>
      <div className="px-5 mb-6">
        <ModelSelector 
          models={localModels} 
          selectedModel={selectedModel} 
          setSelectedModel={setSelectedModel} 
          online={ollamaOnline}
        />
        <button 
          onClick={openSettings}
          className="w-full mt-3 py-2 px-3 bg-surface-variant text-on-surface rounded-lg font-medium text-sm flex items-center gap-2 hover:bg-outline-variant transition-colors"
        >
          <Brain className="w-4 h-4 text-primary" />
          RAG Parameters
        </button>
        <button 
          onClick={openEvaluation}
          className="w-full mt-2 py-2 px-3 bg-primary/10 text-primary border border-primary/20 rounded-lg font-medium text-sm flex items-center gap-2 hover:bg-primary/20 transition-colors"
        >
          <BookOpen className="w-4 h-4 text-primary" />
          Evaluations & Benchmarks
        </button>
      </div>

      <div className="px-5 mb-2 text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
        Knowledge Base
      </div>
      <div className="px-5 mb-4">
        <button 
          onClick={() => fileInputRef.current?.click()}
          className="w-full py-2 px-3 bg-primary text-white rounded-lg font-medium text-sm flex items-center justify-center gap-2 hover:bg-primary-hover transition-colors shadow-sm"
        >
          <UploadCloud className="w-4 h-4" />
          Upload PDF
        </button>
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileUpload} 
          accept=".pdf" 
          className="hidden" 
        />
      </div>

      {/* Database Status Panel */}
      <div className="mt-auto px-5 pt-4 border-t border-outline-variant">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-on-surface-variant flex items-center gap-2 font-medium">
            <Database className="w-4 h-4" />
            Vector Store
          </span>
          <span className={`text-[10px] px-2 py-0.5 rounded-full font-mono font-medium ${dbActive ? 'bg-primary/10 text-primary' : 'bg-surface-variant text-on-surface-variant'}`}>
            {dbActive ? "READY" : "EMPTY"}
          </span>
        </div>
        <div className="flex justify-between items-center text-sm text-on-surface-variant mb-4">
          <span>Storage:</span>
          <span className="font-mono text-primary font-medium">{dbSize}</span>
        </div>
        <button 
          onClick={handleResetDatabase}
          className="w-full py-2 text-sm border border-red-500/20 text-red-500 hover:bg-red-500/10 hover:border-red-500/40 rounded-lg transition-colors flex justify-center items-center gap-2"
        >
          <Trash2 className="w-4 h-4" />
          Clear Database
        </button>
      </div>

      {/* Theme Toggle Button */}
      <div className="px-5 mt-4 flex items-center justify-between border-t border-outline-variant pt-4">
        <span className="text-sm text-on-surface-variant font-medium">Theme Mode</span>
        <button 
          onClick={() => setDarkMode(!darkMode)}
          className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg bg-surface-variant hover:bg-outline-variant"
        >
          {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>

    </nav>
  );
}
