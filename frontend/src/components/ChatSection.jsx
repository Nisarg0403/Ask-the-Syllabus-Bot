import React from "react";
import { FileText, Send } from "lucide-react";
import { renderMarkdown } from "../utils/markdown";

export default function ChatSection({
  messages,
  llmProvider,
  selectedModel,
  streaming,
  inputText,
  setInputText,
  handleSendMessage,
  handleKeyPress,
  clickSuggestedPrompt,
  chatEndRef
}) {
  return (
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
                  // Bot response flat-stack style
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
  );
}
