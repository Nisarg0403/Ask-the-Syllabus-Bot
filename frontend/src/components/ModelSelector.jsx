import React from 'react';
import { ChevronDown, Check, Cpu } from 'lucide-react';

export default function ModelSelector({ models, selectedModel, setSelectedModel, online }) {
  const [isOpen, setIsOpen] = React.useState(false);

  const recommendedModels = ['qwen3', 'llama3'];

  return (
    <div className="relative w-full">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between bg-surface-variant px-3 py-2 rounded-lg border border-border hover:border-primary transition-colors text-sm"
      >
        <div className="flex items-center gap-2">
          <Cpu size={16} className={online ? "text-primary" : "text-gray-400"} />
          <span className="font-medium truncate max-w-[150px]">
            {selectedModel || 'Select Model'}
          </span>
        </div>
        <ChevronDown size={16} className={`text-on-surface-variant transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-1 w-full bg-card border border-border rounded-lg shadow-lg z-50 overflow-hidden">
          <div className="max-h-60 overflow-y-auto py-1">
            {models.length === 0 ? (
              <div className="px-3 py-2 text-sm text-on-surface-variant">No local models found</div>
            ) : (
              models.map(model => {
                const isRecommended = recommendedModels.some(rm => model.toLowerCase().includes(rm));
                return (
                  <button
                    key={model}
                    onClick={() => {
                      setSelectedModel(model);
                      setIsOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 flex items-center justify-between text-sm hover:bg-surface-variant transition-colors ${selectedModel === model ? 'bg-surface-container' : ''}`}
                  >
                    <div>
                      <div className="font-medium">{model}</div>
                      {isRecommended && <div className="text-xs text-primary mt-0.5">Recommended</div>}
                    </div>
                    {selectedModel === model && <Check size={14} className="text-primary" />}
                  </button>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
