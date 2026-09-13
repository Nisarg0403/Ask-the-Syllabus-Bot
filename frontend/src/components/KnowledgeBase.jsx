import React from "react";
import { FolderOpen, UploadCloud, RefreshCw, FileText, Trash2 } from "lucide-react";

export default function KnowledgeBase({
  fileInputRef,
  uploading,
  uploadStatus,
  uploadProgress,
  indexedDocs,
  handleDeleteDocument
}) {
  return (
    <section className="w-1/2 h-full border-r border-outline-variant p-8 flex flex-col gap-6 overflow-y-auto relative bg-background">
      
      <h2 className="font-serif text-lg font-semibold flex items-center gap-2 text-on-surface">
        <FolderOpen className="w-5 h-5 text-primary" />
        Knowledge Base
      </h2>

      {/* Upload Dropzone */}
      <div 
        onClick={() => fileInputRef.current?.click()}
        className="rounded-xl p-8 flex flex-col items-center justify-center text-center border-dashed border border-outline-variant/80 bg-surface-container/30 hover:bg-surface-container/60 hover:border-primary/50 transition-colors cursor-pointer group z-10 relative overflow-hidden"
      >
        <div className="h-14 w-14 rounded-full bg-surface-variant flex items-center justify-center mb-4 group-hover:scale-105 transition-transform duration-300">
          <UploadCloud className="w-6 h-6 text-primary" />
        </div>
        <h3 className="text-sm font-medium text-on-surface mb-2">Drop Syllabus PDFs here or browse</h3>
        <p className="text-xs text-on-surface-variant max-w-xs leading-relaxed">
          Files are split into chunks and indexed locally. Max size: 50MB.
        </p>
      </div>

      {/* Indexing Progress Indicator */}
      {uploading && (
        <div className="rounded-xl p-4 border border-outline-variant bg-surface-container/40 z-10 flex flex-col gap-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <RefreshCw className="w-4 h-4 text-primary animate-spin" />
              <span className="text-xs font-medium text-on-surface">Processing...</span>
            </div>
            <span className="text-xs font-mono text-primary">{uploadProgress}%</span>
          </div>
          <p className="text-[10px] text-on-surface-variant truncate">{uploadStatus}</p>
          <div className="h-1.5 w-full bg-outline-variant/40 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary rounded-full relative transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            >
            </div>
          </div>
        </div>
      )}

      {/* Indexed Document List */}
      <div className="flex-1 flex flex-col z-10">
        <h3 className="text-[10px] font-semibold text-on-surface-variant mb-3 uppercase tracking-wider font-sans">
          Indexed Syllabi ({indexedDocs.length})
        </h3>
        <div className="flex flex-col gap-2">
          {indexedDocs.length > 0 ? (
            indexedDocs.map((doc, idx) => (
              <div 
                key={idx} 
                className="rounded-xl p-3.5 flex items-center gap-3.5 hover:bg-surface-variant/40 transition-colors border border-outline-variant/60 bg-surface-container/20 group"
              >
                <div className="h-9 w-9 rounded-lg bg-surface-variant flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-primary/80" />
                </div>
                <div className="flex-1 min-w-0">
                  <h4 className="text-xs font-semibold text-on-surface truncate group-hover:text-primary transition-colors">
                    {doc.filename}
                  </h4>
                  <div className="flex items-center gap-2 text-[10px] text-on-surface-variant mt-0.5">
                    <span>{doc.size}</span>
                    <span className="h-1 w-1 rounded-full bg-outline-variant"></span>
                    <span>{doc.indexed_at}</span>
                  </div>
                </div>
                <button 
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteDocument(doc.filename);
                  }}
                  className="p-1.5 text-on-surface-variant hover:text-error hover:bg-error/10 transition-all rounded-lg active:scale-95"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-on-surface-variant border border-dashed border-outline-variant/60 rounded-xl bg-surface-container/10">
              No documents indexed yet. Build your knowledge base above!
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
