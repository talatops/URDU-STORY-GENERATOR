'use client';

import { useState, useRef, useEffect } from 'react';

const FUNNY_LOADING_MESSAGES = [
  'شہزادی کو تلاش کر رہے ہیں...',
  'الفاظ کو اکٹھا کر رہے ہیں...',
  'کہانی کی جن کو بیدار کر رہے ہیں...',
  'الفاظ کو ترتیب دے رہے ہیں...',
  'جادوئی قلم چل رہی ہے...',
  'کہانی پک رہی ہے، تھوڑا انتظار کریں!',
  'الفاظ دوڑ رہے ہیں...',
  'کہانی کی بو آ رہی ہے... تقریباً تیار!',
  'شہزادے کو جگا رہے ہیں...',
  'الفاظ گھر آ رہے ہیں...',
];

const SUGGESTIONS = [
  'ایک بار ایک بادشاہ تھا',
  'ایک کتا تھا',
  'ایک چوہا تھا',
  'ایک چالاک لومڑی تھی',
  'ایک شہزادی تھی',
  'ایک ڈریگن تھا',
  'ایک جادوگر تھا',
  'ایک پرندہ تھا',
];

export default function Home() {
  const [prefix, setPrefix] = useState('');
  const [story, setStory] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadingMessage, setLoadingMessage] = useState(FUNNY_LOADING_MESSAGES[0]);
  const storyEndRef = useRef<HTMLDivElement>(null);
  const storyContainerRef = useRef<HTMLDivElement>(null);

  const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

  const scrollToBottom = () => {
    storyEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [story]);

  // Cycle through funny loading messages
  useEffect(() => {
    if (!isGenerating) return;
    const idx = Math.floor(Math.random() * FUNNY_LOADING_MESSAGES.length);
    setLoadingMessage(FUNNY_LOADING_MESSAGES[idx]);
    const interval = setInterval(() => {
      setLoadingMessage((prev) => {
        const others = FUNNY_LOADING_MESSAGES.filter((m) => m !== prev);
        return others[Math.floor(Math.random() * others.length)];
      });
    }, 2500);
    return () => clearInterval(interval);
  }, [isGenerating]);

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
      const msg = err instanceof Error ? err.message : 'An error occurred';
      setError(msg.includes('fetch') || msg.includes('Failed') || msg.includes('Network')
        ? `${msg} — Check that NEXT_PUBLIC_API_URL is set in Vercel and redeploy.`
        : msg);
      setIsGenerating(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      generateStory();
    }
  };

  const pickSuggestion = (s: string) => {
    setPrefix(s);
    setError(null);
  };

  return (
    <main className="min-h-screen overflow-y-auto bg-gradient-to-b from-amber-50 via-orange-50 to-rose-100 dark:from-stone-950 dark:via-amber-950/30 dark:to-rose-950/20">
      {/* Decorative floating elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <span className="absolute top-20 left-10 text-6xl opacity-20 animate-float">📖</span>
        <span className="absolute top-40 right-16 text-5xl opacity-20 animate-float-delayed">✨</span>
        <span className="absolute bottom-40 left-20 text-4xl opacity-20 animate-float">🌟</span>
        <span className="absolute bottom-20 right-24 text-5xl opacity-20 animate-float-delayed">🪄</span>
      </div>

      <div className="relative container mx-auto px-4 py-6 max-w-3xl space-y-12 pb-24">
        {/* Hero Section - Scrollable top */}
        <section className="scroll-mt-6 pt-4">
          <div className="text-center space-y-3 animate-fade-in">
            <h1 className="text-5xl md:text-6xl font-bold bg-gradient-to-r from-amber-600 via-orange-500 to-rose-500 bg-clip-text text-transparent drop-shadow-sm">
              اردو کہانی جنریٹر
            </h1>
            <p className="text-lg text-amber-800/80 dark:text-amber-200/80 font-medium">
              Urdu Story Generator
            </p>
            <p className="text-sm text-amber-700/70 dark:text-amber-300/70 max-w-md mx-auto">
              بچوں کی کہانیاں بنائیں — جادو ایک کلک میں! 🧙‍♂️
            </p>
          </div>
        </section>

        {/* Input Section */}
        <section className="scroll-mt-6">
          <div className="bg-white/80 dark:bg-stone-900/80 backdrop-blur-sm rounded-2xl shadow-xl shadow-amber-200/30 dark:shadow-stone-900/50 border border-amber-200/50 dark:border-amber-800/30 p-6">
            <label htmlFor="prefix" className="block text-sm font-semibold text-amber-800 dark:text-amber-200 mb-2">
              شروع کریں — اپنا جملہ لکھیں ✍️
            </label>
            <textarea
              id="prefix"
              value={prefix}
              onChange={(e) => setPrefix(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="مثال: ایک بار ایک بادشاہ تھا..."
              className="w-full px-4 py-3 border-2 border-amber-200 dark:border-amber-700/50 rounded-xl focus:ring-2 focus:ring-amber-400 focus:border-amber-400 dark:bg-stone-800 dark:text-amber-50 resize-none transition-all placeholder:text-amber-400/50"
              rows={3}
              dir="rtl"
              disabled={isGenerating}
            />

            {/* Quick suggestion chips - scrollable */}
            <div className="mt-3">
              <p className="text-xs font-medium text-amber-700/80 dark:text-amber-300/80 mb-2">
                یا یہاں سے منتخب کریں 👇
              </p>
              <div className="flex flex-wrap gap-2 overflow-x-auto pb-1 scrollbar-thin">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => pickSuggestion(s)}
                    className="px-3 py-1.5 text-sm rounded-full bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 border border-amber-300/50 dark:border-amber-700/50 hover:bg-amber-200 dark:hover:bg-amber-800/50 hover:scale-105 transition-all whitespace-nowrap"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>

            <div className="mt-4 flex flex-col sm:flex-row justify-between items-center gap-3">
              <button
                onClick={generateStory}
                disabled={isGenerating || !prefix.trim()}
                className="px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold rounded-xl shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none transition-all hover:scale-105 active:scale-95"
              >
                {isGenerating ? '⏳ جنریٹ ہو رہا ہے...' : '🚀 کہانی بنائیں'}
              </button>
              <span className="text-xs text-amber-600/70 dark:text-amber-400/70">
                Enter دبائیں — تیز! ⚡
              </span>
            </div>
          </div>
        </section>

        {/* Error Display */}
        {error && (
          <section className="scroll-mt-6 animate-shake">
            <div className="p-4 bg-red-100 dark:bg-red-900/40 border-2 border-red-300 dark:border-red-700 rounded-xl text-red-800 dark:text-red-200">
              <strong>اوہ! 😅</strong> {error}
            </div>
          </section>
        )}

        {/* Story Display - Scrollable book-like area */}
        <section className="scroll-mt-6">
          <h2 className="text-xl font-bold text-amber-800 dark:text-amber-200 mb-3 flex items-center gap-2">
            <span>📜</span> آپ کی کہانی
          </h2>
          <div
            ref={storyContainerRef}
            className="relative min-h-[320px] max-h-[70vh] overflow-y-auto overflow-x-hidden rounded-2xl border-2 border-amber-200/60 dark:border-amber-800/40 bg-gradient-to-b from-amber-50/90 to-orange-50/70 dark:from-stone-900/90 dark:to-amber-950/30 p-8 shadow-inner scroll-smooth"
          >
            {story ? (
              <div className="text-lg md:text-xl text-amber-900 dark:text-amber-100 leading-loose font-medium" dir="rtl">
                {story}
                {isGenerating && (
                  <span className="inline-block w-2 h-6 bg-amber-500 animate-blink ml-1 align-middle" />
                )}
              </div>
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center px-6">
                {isGenerating ? (
                  <>
                    <div className="text-6xl mb-4 animate-bounce">📚</div>
                    <p className="text-amber-700 dark:text-amber-300 font-medium animate-pulse">
                      {loadingMessage}
                    </p>
                    <div className="mt-4 flex gap-1">
                      {[0, 1, 2].map((i) => (
                        <span
                          key={i}
                          className="w-2 h-2 rounded-full bg-amber-500 animate-ping"
                          style={{ animationDelay: `${i * 200}ms` }}
                        />
                      ))}
                    </div>
                  </>
                ) : (
                  <>
                    <p className="text-5xl mb-4 opacity-40">📖</p>
                    <p className="text-amber-600/80 dark:text-amber-400/80">
                      کہانی یہاں ظاہر ہوگی
                    </p>
                    <p className="text-sm text-amber-500/60 dark:text-amber-500/60 mt-1">
                      اوپر ایک جملہ لکھیں اور &quot;کہانی بنائیں&quot; دبائیں! 🎉
                    </p>
                  </>
                )}
              </div>
            )}
            <div ref={storyEndRef} />
          </div>
        </section>

        {/* Footer - Playful */}
        <footer className="text-center text-sm text-amber-600/70 dark:text-amber-500/70 pt-4">
          <p>Powered by Trigram Language Model & Word Tokenizer</p>
          <p className="mt-1 text-xs opacity-75">کہانیاں بنانے والا جادو 🪄</p>
        </footer>
      </div>
    </main>
  );
}
