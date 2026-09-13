import React, { useState } from "react";
import { Send, Paperclip, Sparkles, Search } from "lucide-react";

const COMMON_SYLLABUS_QUERIES = [
  "What is the grading breakdown and policy?",
  "What are the three types of topics mentioned in the examination?",
  "What topics are covered in Unit 3?",
  "What is the late assignment submission policy?",
  "What are the prerequisites and recommended textbooks?",
  "Explain backpropagation according to the uploaded notes.",
  "Which topics are included in the final module?"
];

export default function ChatInput({
  inputText,
  setInputText,
  handleSendMessage,
  handleKeyPress,
  streaming,
  clickSuggestedPrompt,
  hasMessages
}) {
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Filter autocomplete suggestions based on user input
  const filteredSuggestions = inputText.trim().length >= 2
    ? COMMON_SYLLABUS_QUERIES.filter(q => 
        q.toLowerCase().includes(inputText.toLowerCase())
      )
    : [];

  const handleSelectSuggestion = (suggestion) => {
    setInputText(suggestion);
    setShowSuggestions(false);
  };

  return (
    <div className="p-6 bg-gradient-to-t from-background via-background to-transparent relative z-20">
      <div className="max-w-[840px] w-full mx-auto flex flex-col gap-4">
      
        {/* Suggested Quick Prompt Chips (ONLY rendered on empty home state) */}
        {!hasMessages && (
          <div className="flex gap-2 overflow-x-auto pb-1 custom-scrollbar scroll-smooth">
            <button 
              onClick={() => clickSuggestedPrompt("What topics are covered in Unit 3?")}
              className="whitespace-nowrap px-4 py-2 text-xs rounded-full border border-border text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/50 transition-all duration-200 font-medium shadow-sm"
            >
              What topics are covered in Unit 3?
            </button>
            <button 
              onClick={() => clickSuggestedPrompt("Explain backpropagation according to the uploaded notes.")}
              className="whitespace-nowrap px-4 py-2 text-xs rounded-full border border-border text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/50 transition-all duration-200 font-medium shadow-sm"
            >
              Explain backpropagation
            </button>
            <button 
              onClick={() => clickSuggestedPrompt("Which topics are included in the final module?")}
              className="whitespace-nowrap px-4 py-2 text-xs rounded-full border border-border text-on-surface-variant hover:text-primary hover:border-primary/50 bg-surface-container/50 transition-all duration-200 font-medium shadow-sm"
            >
              Final module topics
            </button>
          </div>
        )}

        {/* Autocomplete Popup List */}
        {showSuggestions && filteredSuggestions.length > 0 && (
          <div className="bg-card border border-border rounded-xl shadow-xl overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-150 relative z-30">
            <div className="px-3 py-2 bg-surface-container/50 border-b border-border flex items-center gap-2 text-[11px] font-semibold text-on-surface-variant uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-primary" />
              <span>Suggested Syllabus Queries</span>
            </div>
            <div className="max-h-48 overflow-y-auto custom-scrollbar divide-y divide-border/40">
              {filteredSuggestions.map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectSuggestion(query)}
                  className="w-full text-left px-4 py-2.5 text-xs text-on-surface hover:bg-primary/10 hover:text-primary transition-colors flex items-center gap-2 font-medium"
                >
                  <Search className="w-3.5 h-3.5 text-on-surface-variant shrink-0" />
                  <span className="truncate">{query}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Main Textarea Input Bar */}
        <div className="relative group rounded-xl bg-card border border-border shadow-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/20 transition-all duration-200 flex flex-col">
          <textarea 
            value={inputText}
            onChange={(e) => {
              setInputText(e.target.value);
              setShowSuggestions(true);
            }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
            onKeyDown={(e) => {
              if (e.key === "Escape") setShowSuggestions(false);
              handleKeyPress(e);
            }}
            className="w-full bg-transparent text-[15px] text-on-surface py-4 pl-4 pr-4 resize-none focus:outline-none focus:ring-0 border-none placeholder:text-on-surface-variant/70 min-h-[56px] max-h-[200px]" 
            placeholder="Ask a question grounded in your academic documents..." 
            rows="1" 
            disabled={streaming}
          />
          
          <div className="flex items-center justify-between px-3 pb-3">
            <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-lg hover:bg-surface-variant">
              <Paperclip className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-3">
              <span className="text-[10px] text-on-surface-variant font-medium hidden sm:inline-block">
                Shift + Enter for new line
              </span>
              <button 
                onClick={() => {
                  setShowSuggestions(false);
                  handleSendMessage();
                }}
                disabled={streaming || !inputText.trim()}
                className={`h-9 w-9 rounded-lg flex items-center justify-center transition-all ${
                  streaming || !inputText.trim()
                    ? "bg-surface-variant text-on-surface-variant cursor-not-allowed"
                    : "bg-primary text-white hover:bg-primary-hover shadow-md"
                }`}
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        
        <div className="text-center">
          <span className="text-[10px] text-on-surface-variant/80 font-medium">
            Syllabus Bot can make mistakes. Always verify important academic details with your professor.
          </span>
        </div>
      </div>
    </div>
  );
}

