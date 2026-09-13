import React from "react";
import { FileText, ChevronRight, CheckCircle2, AlertCircle, UploadCloud, Sparkles, Loader2 } from "lucide-react";
import { renderMarkdown } from "../utils/markdown";
import ChatInput from "./ChatInput";

export default function ChatSection({
  messages,
  selectedModel,
  streaming,
  inputText,
  setInputText,
  handleSendMessage,
  handleKeyPress,
  clickSuggestedPrompt,
  chatEndRef,
  indexedDocsCount,
  openKnowledgeBase
}) {
  React.useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streaming]);

  return (
    <section className="w-full h-full bg-background flex flex-col relative">
      
      {/* Chat Pane Header */}
      <div className="h-16 border-b border-border px-6 flex items-center justify-between z-20 w-full bg-background/95 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <button onClick={openKnowledgeBase} className="flex items-center gap-2 hover:bg-surface-variant px-2 py-1.5 rounded-lg transition-colors">
            <span className="font-serif text-base font-semibold text-on-surface">
              Knowledge Base
            </span>
            <span className="text-[10px] font-mono bg-surface-variant text-on-surface-variant px-1.5 py-0.5 rounded border border-border">
              {indexedDocsCount} Docs
            </span>
          </button>
        </div>
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-surface-variant border border-border">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse-dot"></span>
          <span className="text-xs font-sans font-semibold text-on-surface-variant uppercase tracking-wider">
            {selectedModel || 'No Model'}
          </span>
        </div>
      </div>

      {/* Chat Thread Messages */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-8 pt-8 pb-6 flex flex-col gap-8 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center max-w-2xl mx-auto w-full text-center mt-[-10vh]">
            <div className="w-16 h-16 bg-primary/10 text-primary rounded-2xl flex items-center justify-center mb-6">
              <FileText className="w-8 h-8" />
            </div>
            <h1 className="text-3xl font-serif font-semibold text-on-surface mb-3">Ask-the-Syllabus Bot</h1>
            <p className="text-on-surface-variant mb-8 max-w-md mx-auto text-sm leading-relaxed">
              Your AI assistant for syllabus and course materials. Upload your course PDFs and ask questions grounded in your academic documents.
            </p>
            {indexedDocsCount === 0 && (
              <button 
                onClick={openKnowledgeBase}
                className="px-6 py-3 bg-primary text-white rounded-xl font-medium shadow-sm hover:bg-primary-hover transition-colors flex items-center gap-2"
              >
                <UploadCloud className="w-4 h-4" />
                Upload Documents
              </button>
            )}
          </div>
        ) : (
          <div className="max-w-[840px] w-full mx-auto flex flex-col gap-8">
            {messages.map((msg, index) => (
              <div 
                key={index}
                className={`flex gap-4 ${msg.sender === "user" ? "justify-end" : "justify-start"} w-full`}
              >
                {/* Bot Avatar */}
                {msg.sender === "bot" && (
                  <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0 mt-1 bg-primary/10 border border-primary/20">
                    <span className="font-serif text-xs font-semibold text-primary">SB</span>
                  </div>
                )}

                {/* Message Bubble */}
                <div className={`flex flex-col gap-2 ${msg.sender === "user" ? "items-end" : "items-start"} max-w-[85%]`}>
                  
                  {msg.sender === "user" ? (
                    <div className="bg-surface-variant text-on-surface px-5 py-3.5 rounded-2xl rounded-tr-sm text-[15px] shadow-sm">
                      <div className="font-sans leading-relaxed whitespace-pre-wrap">
                        {msg.text}
                      </div>
                    </div>
                  ) : (
                    <div className="w-full">
                      {/* Thinking Loader dots when streaming starts before first token */}
                      {msg.isStreaming && !msg.text && (
                        <div className="flex items-center gap-3 py-3 px-4 bg-surface-container/60 rounded-xl border border-border text-on-surface-variant text-sm">
                          <Loader2 className="w-4 h-4 text-primary animate-spin" />
                          <span className="font-medium text-xs text-on-surface-variant">Thinking and retrieving context...</span>
                          <div className="flex gap-1 items-center ml-2">
                            <div className="w-1.5 h-1.5 bg-primary/80 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                            <div className="w-1.5 h-1.5 bg-primary/80 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                            <div className="w-1.5 h-1.5 bg-primary/80 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                          </div>
                        </div>
                      )}

                      {/* Rendered Text Response */}
                      {msg.text && (
                        <div>
                          <div 
                            className="prose prose-slate dark:prose-invert max-w-none text-[15px] font-serif text-on-surface leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.text) }}
                          />
                          
                          {/* Real-time typing / streaming indicator while answering */}
                          {msg.isStreaming && (
                            <div className="flex items-center gap-2 mt-3 py-1 text-xs text-primary font-medium">
                              <span className="h-2 w-2 rounded-full bg-primary animate-ping"></span>
                              <span>Generating answer...</span>
                              <div className="flex gap-1 items-center ml-1">
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                                <div className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                              </div>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Expandable RAG Details / Citations - STRICTLY DISPLAYED AFTER COMPLETION OF RESULT */}
                      {!msg.isStreaming && !msg.isError && msg.sources && msg.sources.length > 0 && (
                        <details className="mt-5 group bg-surface-container rounded-xl border border-border overflow-hidden shadow-sm animate-in fade-in slide-in-from-top-2 duration-300">
                          <summary className="px-4 py-2.5 text-xs font-semibold text-on-surface-variant cursor-pointer flex items-center justify-between hover:bg-surface-variant transition-colors outline-none">
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                              <span>Grounded in {msg.sources.length} retrieved sources</span>
                            </div>
                            <ChevronRight className="w-4 h-4 transition-transform group-open:rotate-90" />
                          </summary>
                          <div className="p-4 border-t border-border bg-background flex flex-col gap-3">
                            <div className="flex justify-between items-center mb-1">
                              <span className="text-[10px] uppercase font-bold text-on-surface-variant tracking-wider">RAG Details</span>
                              {msg.responseTime && (
                                <span className="text-[10px] font-mono bg-surface-variant px-1.5 py-0.5 rounded text-on-surface-variant">
                                  {msg.responseTime}
                                </span>
                              )}
                            </div>
                            <div className="grid grid-cols-1 gap-3 max-h-64 overflow-y-auto custom-scrollbar pr-2">
                              {msg.sources.map((src, idx) => (
                                <div key={idx} className="p-3.5 rounded-xl bg-surface-container border border-border text-xs">
                                  <div className="flex justify-between items-center mb-2">
                                    <span className="font-semibold text-primary flex items-center gap-1.5">
                                      <FileText className="w-3.5 h-3.5" />
                                      <span className="truncate max-w-[200px]">{src.source}</span>
                                    </span>
                                    <span className="bg-primary/10 text-primary px-2 py-0.5 rounded-full text-[10px] font-medium border border-primary/20">
                                      Page {src.page}
                                    </span>
                                  </div>
                                  <p className="text-on-surface-variant font-serif leading-relaxed line-clamp-4 hover:line-clamp-none transition-all">
                                    "{src.content}"
                                  </p>
                                </div>
                              ))}
                            </div>
                          </div>
                        </details>
                      )}
                      
                      {!msg.isStreaming && !msg.isError && msg.text && (!msg.sources || msg.sources.length === 0) && (
                        <div className="mt-4 flex items-start gap-2 p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl max-w-sm">
                          <AlertCircle className="w-4 h-4 text-orange-500 shrink-0 mt-0.5" />
                          <div>
                            <span className="text-xs font-semibold text-orange-600 block mb-0.5">Out of Knowledge Base</span>
                            <span className="text-[11px] text-orange-600/80 leading-tight block">
                              I couldn't find enough information in your uploaded documents to fully ground this answer.
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                </div>
              </div>
            ))}
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <ChatInput 
        inputText={inputText}
        setInputText={setInputText}
        handleSendMessage={handleSendMessage}
        handleKeyPress={handleKeyPress}
        streaming={streaming}
        clickSuggestedPrompt={clickSuggestedPrompt}
        hasMessages={messages.length > 0}
      />

    </section>
  );
}
