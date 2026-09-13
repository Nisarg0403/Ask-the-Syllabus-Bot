import React from "react";
import { Search, Bell, History } from "lucide-react";

export default function Header() {
  return (
    <header className="fixed top-0 right-0 w-[calc(100%-280px)] z-50 bg-background/80 backdrop-blur-md border-b border-outline-variant flex justify-between items-center h-16 px-container-padding">
      <div className="flex items-center gap-4">
        <h1 className="font-serif text-xl font-semibold text-on-surface">
          Ask-the-Syllabus Bot
        </h1>
      </div>
      <div className="flex items-center gap-3">
        <div className="relative hidden lg:block group rounded-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant w-4 h-4" />
          <input 
            className="bg-surface-variant border border-outline-variant text-on-surface rounded-full py-1.5 pl-9 pr-4 text-xs focus:outline-none focus:border-primary/60 w-48 focus:w-60 transition-all duration-300 placeholder:text-on-surface-variant" 
            placeholder="Search syllabus..." 
            type="text"
          />
        </div>
        <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-variant/40">
          <Bell className="w-4.5 h-4.5" />
        </button>
        <button className="p-2 text-on-surface-variant hover:text-primary transition-colors rounded-full hover:bg-surface-variant/40">
          <History className="w-4.5 h-4.5" />
        </button>
        <div className="h-8 w-8 rounded-full bg-surface-variant flex items-center justify-center border border-outline-variant cursor-pointer">
          <span className="font-serif text-xs font-semibold text-primary">A</span>
        </div>
      </div>
    </header>
  );
}
