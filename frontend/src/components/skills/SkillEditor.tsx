'use client';

import { useState } from 'react';
import { Check, X } from 'lucide-react';

interface SkillEditorProps {
  initialContent?: string;
  onSave: (content: string) => void;
  onCancel: () => void;
}

function renderMarkdownPreview(markdown: string) {
  const lines = markdown.split('\n');
  return lines.map((line, i) => {
    if (line.startsWith('# ')) {
      return (
        <div key={i} className="text-white font-bold text-lg mb-2 mt-4 first:mt-0">
          {line.slice(2)}
        </div>
      );
    }
    if (line.startsWith('## ')) {
      return (
        <div key={i} className="text-gray-200 font-semibold text-base mb-1 mt-3">
          {line.slice(3)}
        </div>
      );
    }
    if (line.startsWith('* ')) {
      return (
        <div key={i} className="text-gray-300 pl-4 ml-2 mb-1 text-sm flex items-start gap-2">
          <span className="text-emerald-400 mt-1">&#8226;</span>
          <span>{line.slice(2)}</span>
        </div>
      );
    }
    if (line.startsWith('- ')) {
      return (
        <div key={i} className="text-gray-300 pl-4 ml-2 mb-1 text-sm flex items-start gap-2">
          <span className="text-gray-500 mt-1">&#8211;</span>
          <span>{line.slice(2)}</span>
        </div>
      );
    }
    if (line.trim() === '') {
      return <div key={i} className="h-2" />;
    }
    return (
      <div key={i} className="text-gray-300 text-sm mb-0.5">
        {line}
      </div>
    );
  });
}

export function SkillEditor({ initialContent = '', onSave, onCancel }: SkillEditorProps) {
  const [content, setContent] = useState(initialContent);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex gap-0 min-h-0">
        <div className="flex-[7] flex flex-col border-r border-gray-700">
          <div className="px-4 py-2 bg-gray-800 border-b border-gray-700">
            <span className="text-xs font-medium text-gray-400 uppercase">Editor</span>
          </div>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="flex-1 w-full px-4 py-3 bg-gray-950 text-gray-200 text-sm font-mono focus:outline-none resize-none border-none"
            placeholder="Enter markdown content..."
            spellCheck={false}
          />
        </div>
        <div className="flex-[3] flex flex-col">
          <div className="px-4 py-2 bg-gray-800 border-b border-gray-700">
            <span className="text-xs font-medium text-gray-400 uppercase">Preview</span>
          </div>
          <div className="flex-1 overflow-y-auto px-4 py-3 bg-gray-900">
            {content.trim() ? (
              renderMarkdownPreview(content)
            ) : (
              <p className="text-gray-500 text-sm italic">Nothing to preview</p>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-center justify-end gap-3 px-4 py-3 bg-gray-800 border-t border-gray-700">
        <button
          onClick={onCancel}
          className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors flex items-center gap-2"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
        <button
          onClick={() => onSave(content)}
          disabled={!content.trim()}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-gray-700 rounded text-sm text-white transition-colors flex items-center gap-2"
        >
          <Check className="w-4 h-4" />
          Save
        </button>
      </div>
    </div>
  );
}
