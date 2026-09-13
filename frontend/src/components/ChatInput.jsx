import React from "react";
import { Send, Paperclip } from "lucide-react";

export default function ChatInput({
  inputText,
  setInputText,
  handleSendMessage,
  handleKeyPress,
  streaming,
  clickSuggestedPrompt
}) {
  return (
    <div className="p-6 bg-gradient-to-t from-background via-background to-transparent relative z-20">
      <div className="max-w-[840px] w-full mx-auto flex flex-col gap-4">
      
        {/* Suggested Quick Prompt Chips */}
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

        {/* Main Textarea Input Bar */}
        <div className="relative group rounded-xl bg-card border border-border shadow-sm focus-within:border-primary focus-within:ring-1 focus-within:ring-primary/20 transition-all duration-200 flex flex-col">
          <textarea 
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
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
                onClick={() => handleSendMessage()}
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
