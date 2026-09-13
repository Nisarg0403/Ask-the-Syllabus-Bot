import React from "react";
import { 
  School, 
  UploadCloud, 
  Brain, 
  Database, 
  Trash2, 
  Sun, 
  Moon 
} from "lucide-react";
import { OPENROUTER_MODELS } from "../services/api";

export default function Sidebar({
  fileInputRef,
  handleFileUpload,
  llmProvider,
  handleProviderChange,
  selectedModel,
  setSelectedModel,
  localModels,
  ollamaOnline,
  openRouterKey,
  setOpenRouterKey,
  customModel,
  setCustomModel,
  chunkSize,
  setChunkSize,
  chunkOverlap,
  setChunkOverlap,
  docsToRetrieve,
  setDocsToRetrieve,
  temperature,
  setTemperature,
  dbActive,
  dbSize,
  handleResetDatabase,
  darkMode,
  setDarkMode
}) {
  return (
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
  );
}
