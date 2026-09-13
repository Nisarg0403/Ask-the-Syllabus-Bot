import React from "react";
import { X, Sliders } from "lucide-react";

export default function SettingsPanel({
  isOpen,
  onClose,
  chunkSize,
  setChunkSize,
  chunkOverlap,
  setChunkOverlap,
  docsToRetrieve,
  setDocsToRetrieve,
  temperature,
  setTemperature,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-on-surface/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-card w-full max-w-md rounded-xl shadow-2xl border border-border flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-primary" />
            <h3 className="font-semibold text-lg">RAG Settings</h3>
          </div>
          <button onClick={onClose} className="text-on-surface-variant hover:text-primary transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 flex flex-col gap-6">
          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Chunk Size</span>
              <span className="text-primary font-mono bg-primary/10 px-2 rounded-md">{chunkSize}</span>
            </div>
            <input 
              type="range" 
              min="256" max="2048" step="64"
              value={chunkSize}
              onChange={(e) => setChunkSize(parseInt(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Chunk Overlap</span>
              <span className="text-primary font-mono bg-primary/10 px-2 rounded-md">{chunkOverlap}</span>
            </div>
            <input 
              type="range" 
              min="0" max="500" step="25"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(parseInt(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Top-K Retrieval</span>
              <span className="text-primary font-mono bg-primary/10 px-2 rounded-md">{docsToRetrieve}</span>
            </div>
            <input 
              type="range" 
              min="1" max="10" step="1"
              value={docsToRetrieve}
              onChange={(e) => setDocsToRetrieve(parseInt(e.target.value))}
              className="w-full accent-primary"
            />
          </div>

          <div>
            <div className="flex justify-between text-sm mb-2">
              <span className="font-medium">Temperature</span>
              <span className="text-primary font-mono bg-primary/10 px-2 rounded-md">{temperature.toFixed(1)}</span>
            </div>
            <input 
              type="range" 
              min="0" max="1" step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="w-full accent-primary"
            />
          </div>
        </div>

        <div className="px-6 py-4 bg-surface-variant border-t border-border flex justify-end">
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-primary text-white rounded-lg text-sm font-medium hover:bg-primary-hover transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
