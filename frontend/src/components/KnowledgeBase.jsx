import React from "react";
import { FolderOpen, UploadCloud, RefreshCw, FileText, Trash2, X } from "lucide-react";

export default function KnowledgeBase({
  onClose,
  fileInputRef,
  uploading,
  uploadStatus,
  uploadProgress,
  indexedDocs,
  handleDeleteDocument
}) {
  return (
    <div className="fixed inset-0 bg-on-surface/20 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-background w-full max-w-2xl h-[80vh] rounded-2xl shadow-2xl border border-border flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-surface-container/50">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <FolderOpen className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h2 className="font-semibold text-lg text-on-surface">Knowledge Base</h2>
              <p className="text-xs text-on-surface-variant font-medium">Manage your indexed syllabus documents</p>
            </div>
          </div>
          <button onClick={onClose} className="p-2 text-on-surface-variant hover:text-primary transition-colors hover:bg-surface-variant rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-6">
          
          {/* Upload Dropzone */}
          <div 
            onClick={() => !uploading && fileInputRef.current?.click()}
            className={`rounded-xl p-8 flex flex-col items-center justify-center text-center border-2 border-dashed ${uploading ? 'border-border bg-surface-container opacity-70 cursor-not-allowed' : 'border-border hover:border-primary bg-surface-container/30 hover:bg-surface-variant/50 cursor-pointer'} transition-all group relative overflow-hidden`}
          >
            <div className="h-14 w-14 rounded-full bg-background border border-border flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-300 shadow-sm">
              <UploadCloud className={`w-6 h-6 ${uploading ? 'text-on-surface-variant' : 'text-primary'}`} />
            </div>
            <h3 className="text-sm font-semibold text-on-surface mb-2">Drop Syllabus PDFs here or browse</h3>
            <p className="text-xs text-on-surface-variant max-w-xs leading-relaxed">
              Files are processed locally and added to your vector store.
            </p>
          </div>

          {/* Indexing Progress Indicator */}
          {uploading && (
            <div className="rounded-xl p-5 border border-primary/20 bg-primary/5 z-10 flex flex-col gap-3 animate-in fade-in slide-in-from-top-2">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 text-primary animate-spin" />
                  <span className="text-sm font-semibold text-primary">Processing Document...</span>
                </div>
                <span className="text-sm font-mono font-medium text-primary">{uploadProgress}%</span>
              </div>
              <div className="h-2 w-full bg-primary/10 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary rounded-full relative transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                >
                </div>
              </div>
              <p className="text-xs text-on-surface-variant font-medium truncate">{uploadStatus}</p>
            </div>
          )}

          {/* Indexed Document List */}
          <div className="flex flex-col flex-1">
            <h3 className="text-xs font-bold text-on-surface-variant mb-4 uppercase tracking-wider flex items-center justify-between">
              <span>Indexed Syllabi</span>
              <span className="bg-surface-variant px-2 py-0.5 rounded-full text-[10px]">{indexedDocs.length} total</span>
            </h3>
            
            <div className="flex flex-col gap-3 pb-6">
              {indexedDocs.length > 0 ? (
                indexedDocs.map((doc, idx) => (
                  <div 
                    key={idx} 
                    className="rounded-xl p-4 flex items-center gap-4 hover:bg-surface-variant/60 transition-colors border border-border bg-card shadow-sm group"
                  >
                    <div className="h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 border border-primary/20">
                      <FileText className="w-5 h-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="text-sm font-semibold text-on-surface truncate group-hover:text-primary transition-colors">
                        {doc.filename}
                      </h4>
                      <div className="flex items-center gap-2 text-xs text-on-surface-variant mt-1 font-medium">
                        <span>{doc.size}</span>
                        <span className="h-1 w-1 rounded-full bg-on-surface-variant/50"></span>
                        <span>Indexed {doc.indexed_at}</span>
                      </div>
                    </div>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDocument(doc.filename);
                      }}
                      className="p-2 text-on-surface-variant hover:text-red-500 hover:bg-red-50 transition-all rounded-lg"
                      title="Remove document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center border-2 border-dashed border-border rounded-xl bg-surface-container/30 flex flex-col items-center justify-center">
                  <div className="w-12 h-12 rounded-full bg-surface-variant flex items-center justify-center mb-3 text-on-surface-variant">
                    <FileText className="w-6 h-6" />
                  </div>
                  <p className="text-sm font-medium text-on-surface mb-1">No documents indexed yet</p>
                  <p className="text-xs text-on-surface-variant">Upload syllabus PDFs to build your knowledge base.</p>
                </div>
              )}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
