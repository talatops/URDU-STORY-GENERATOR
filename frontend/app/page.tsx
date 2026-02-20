'use client';

import { useState, useRef, useEffect } from 'react';

export default function Home() {
  const [prefix, setPrefix] = useState('');
  const [story, setStory] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const storyEndRef = useRef<HTMLDivElement>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const scrollToBottom = () => {
    storyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [story]);

  const generateStory = async () => {
    if (!prefix.trim()) {
      setError('Please enter a starting phrase');
      return;
    }

    setIsGenerating(true);
    setError(null);
    setStory('');

    try {
      const response = await fetch(`${apiUrl}/generate/stream?prefix=${encodeURIComponent(prefix)}&max_length=200&temperature=0.75`, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data.trim()) {
              try {
                const parsed = JSON.parse(data);
                if (parsed.error) {
                  setError(parsed.error);
                  setIsGenerating(false);
                  return;
                }
                if (parsed.done) {
                  if (parsed.final) {
                    setStory(parsed.final);
                  }
                  setIsGenerating(false);
                  return;
                }
                if (parsed.text) {
                  setStory(parsed.text);
                }
              } catch (e) {
                // Ignore JSON parse errors
              }
            }
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      setIsGenerating(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      generateStory();
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          {/* Header */}
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-gray-800 dark:text-white mb-2">
              اردو کہانی جنریٹر
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              Urdu Story Generator - Create beautiful children's stories
            </p>
          </div>

          {/* Input Section */}
          <div className="mb-6">
            <label htmlFor="prefix" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Starting Phrase (شروع کریں):
            </label>
            <textarea
              id="prefix"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="مثال: ایک بار ایک بادشاہ تھا..."
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent dark:bg-gray-700 dark:text-white resize-none"
              rows={3}
              dir="rtl"
              disabled={isGenerating}
            />
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Try: ایک بار ایک بادشاہ تھا • ایک کتا تھا • ایک چوہا تھا • ایک چالاک لومڑی تھی
            </p>
            <div className="mt-2 flex justify-between items-center">
              <button
                onClick={generateStory}
                disabled={isGenerating || !prefix.trim()}
                className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isGenerating ? 'Generating...' : 'Generate Story'}
              </button>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Press Enter to generate
              </span>
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-200 rounded-lg">
              <strong>Error:</strong> {error}
            </div>
          )}

          {/* Story Display */}
          <div className="mt-6">
            <h2 className="text-2xl font-semibold text-gray-800 dark:text-white mb-4">
              Generated Story:
            </h2>
            <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-6 min-h-[300px] max-h-[600px] overflow-y-auto border border-gray-200 dark:border-gray-700">
              {story ? (
                <div className="text-lg text-gray-800 dark:text-gray-200 leading-relaxed" dir="rtl">
                  {story}
                  {isGenerating && (
                    <span className="inline-block w-2 h-5 bg-indigo-600 animate-pulse ml-1">|</span>
                  )}
                </div>
              ) : (
                <div className="text-gray-400 dark:text-gray-500 text-center py-12">
                  {isGenerating ? (
                    <div className="flex flex-col items-center">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
                      <p>Generating your story...</p>
                    </div>
                  ) : (
                    <p>Your generated story will appear here</p>
                  )}
                </div>
              )}
              <div ref={storyEndRef} />
            </div>
          </div>

          {/* Footer */}
          <div className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>Powered by Trigram Language Model & Word Tokenizer</p>
          </div>
        </div>
      </div>
    </main>
  );
}
