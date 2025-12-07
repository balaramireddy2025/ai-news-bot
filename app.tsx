import React, { useEffect, useState } from 'react';
import { Masthead } from './components/Masthead';
import { NewsCard } from './components/NewsCard';
import { SectionHeader } from './components/SectionHeader';
import { ArticleModal } from './components/ArticleModal';
import { fetchNews } from './services/newsService';
import { NewsItem } from './types';
import { Loader2, AlertCircle, PenTool, Mail, Zap } from 'lucide-react';

const App: React.FC = () => {
  const [news, setNews] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [selectedArticle, setSelectedArticle] = useState<NewsItem | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const data = await fetchNews();
        setNews(data);
      } catch (err) {
        setError('Failed to load the daily edition.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  useEffect(() => {
    if (selectedArticle) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
  }, [selectedArticle]);

  const handleArticleClick = (item: NewsItem) => {
    setSelectedArticle(item);
  };

  const heroStory = news[0];
  const sideStories = news.slice(1, 4);
  const gridStories = news.slice(4);

  return (
    <div className="min-h-screen bg-[#f2f0e6] font-hand text-ink selection:bg-black selection:text-white pb-20">
      
      {/* Top Border Strip */}
      <div className="h-4 bg-ink w-full bg-[url('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAYAAACp8Z5+AAAAIklEQVQIW2NkQAKrVq36zwjjgzjwqgABJGWgCNII4gBzAQBCTCFRAiW54wAAAABJRU5ErkJggg==')]"></div>

      {/* Breaking News Ticker */}
      <div className="bg-ink text-paper py-2 overflow-hidden border-b-4 border-ink shadow-sm relative z-20">
        <div className="animate-marquee whitespace-nowrap font-comic text-lg tracking-widest flex items-center gap-12">
            <span className="flex items-center gap-2"><Zap size={18} className="text-yellow-400 fill-yellow-400" /> BREAKING: AI REFUSES TO DRAW HANDS CORRECTLY</span>
            <span className="flex items-center gap-2"><Zap size={18} className="text-yellow-400 fill-yellow-400" /> CHATGPT RUNS FOR MAYOR IN SIMCITY</span>
            <span className="flex items-center gap-2"><Zap size={18} className="text-yellow-400 fill-yellow-400" /> NEW ALGORITHM PREDICTS MEME TRENDS</span>
            <span className="flex items-center gap-2"><Zap size={18} className="text-yellow-400 fill-yellow-400" /> SCIENTISTS TEACH ROBOT TO FEEL EXISTENTIAL DREAD</span>
            <span className="flex items-center gap-2"><Zap size={18} className="text-yellow-400 fill-yellow-400" /> NVIDIA STOCK USED AS GLOBAL CURRENCY</span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 md:px-8 mt-4">
        
        <Masthead />

        {loading && (
          <div className="flex flex-col items-center justify-center py-40 border-4 border-ink border-dashed rounded-lg opacity-60">
            <Loader2 className="w-16 h-16 animate-spin text-ink mb-6" />
            <h2 className="font-ink text-3xl tracking-widest">DRAWING THE CARTOONS...</h2>
          </div>
        )}

        {error && (
          <div className="bg-white border-4 border-wash-red p-8 shadow-[8px_8px_0px_0px_#d9534f] flex flex-col items-center justify-center text-center space-y-4 my-8">
            <AlertCircle size={48} className="text-wash-red" />
            <span className="font-ink text-3xl text-ink">THE PRESS IS JAMMED!</span>
            <span className="font-hand text-xl">{error}</span>
          </div>
        )}

        {!loading && !error && (
          <>
            {/* --- LAYOUT GRID --- */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">
                
                {/* Left Column (Main) */}
                <div className="lg:col-span-8">
                    <SectionHeader title="Today's Front Page" color="red" />
                    {heroStory && (
                        <NewsCard 
                            item={heroStory} 
                            variant="hero" 
                            onClick={handleArticleClick} 
                        />
                    )}
                    
                    {/* Horizontal Divider */}
                    <div className="relative py-8 my-8 text-center">
                        <div className="absolute top-1/2 left-0 w-full h-1 bg-ink opacity-20"></div>
                        <span className="relative bg-[#f2f0e6] px-6 font-ink text-2xl text-gray-400 transform -rotate-2 inline-block border-2 border-gray-300">
                            MEANWHILE IN TECH...
                        </span>
                    </div>

                    <SectionHeader title="The Daily Strip" color="blue" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        {gridStories.slice(0, 4).map(item => (
                            <NewsCard 
                                key={item.id} 
                                item={item} 
                                variant="standard" 
                                onClick={handleArticleClick} 
                            />
                        ))}
                    </div>
                </div>

                {/* Right Column (Sidebar) */}
                <div className="lg:col-span-4 flex flex-col space-y-12">
                    
                    {/* "Editor's Desk" Widget */}
                    <div className="bg-white border-4 border-ink p-6 shadow-[8px_8px_0px_0px_#1a1a1a] transform rotate-1">
                        <div className="flex items-center justify-center -mt-10 mb-4">
                            <div className="bg-wash-yellow border-4 border-ink rounded-full p-3 shadow-sm">
                                <PenTool size={32} />
                            </div>
                        </div>
                        <h3 className="font-ink text-2xl text-center mb-2">Editor's Scratchpad</h3>
                        <ul className="font-hand text-lg space-y-2 list-disc list-inside marker:text-wash-red">
                            <li>Check sources on GPT-5 rumors.</li>
                            <li>Buy more cyan ink.</li>
                            <li>Is crypto dead again? Check graph.</li>
                            <li>Feed the server hamsters.</li>
                        </ul>
                    </div>

                    {/* Subscription Box (Replaced Ads) */}
                    <div className="bg-wash-blue/20 border-4 border-ink p-6 relative overflow-hidden group hover:shadow-[8px_8px_0px_0px_#a8d1e7] transition-shadow duration-300">
                        {/* Decorative Tape */}
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-24 h-6 bg-yellow-100/80 border border-gray-300 transform -rotate-2 shadow-sm"></div>
                        
                        <div className="flex flex-col items-center text-center">
                            <Mail size={40} className="mb-3 text-ink" />
                            <h3 className="font-ink text-3xl mb-2 leading-none">JOIN THE CLUB!</h3>
                            <p className="font-hand text-lg mb-4 leading-tight">
                                Get our finest satirical cartoons delivered straight to your inbox every morning.
                            </p>
                            <div className="w-full space-y-2">
                                <input 
                                    type="email" 
                                    placeholder="your@email.com" 
                                    className="w-full bg-white border-2 border-ink p-3 font-hand text-lg focus:outline-none focus:ring-2 focus:ring-wash-yellow shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] placeholder:text-gray-400" 
                                />
                                <button className="w-full bg-ink text-white font-comic text-xl py-2 hover:bg-wash-red hover:translate-y-[-2px] transition-all border-2 border-transparent hover:border-ink shadow-[4px_4px_0px_0px_rgba(0,0,0,0.2)]">
                                    SUBSCRIBE
                                </button>
                            </div>
                            <p className="text-xs mt-3 text-gray-500 font-sans">No spam, just jams.</p>
                        </div>
                    </div>

                    {/* Sidebar News */}
                    <div>
                        <SectionHeader title="Short Sketches" color="yellow" />
                        <div className="bg-white border-4 border-ink p-2 shadow-[6px_6px_0px_0px_#f0ad4e]">
                            {sideStories.map((item) => (
                                <NewsCard 
                                    key={item.id} 
                                    item={item} 
                                    variant="sidebar" 
                                    onClick={handleArticleClick} 
                                />
                            ))}
                        </div>
                    </div>

                </div>
            </div>

            {/* --- BOTTOM SECTION (Archive) --- */}
            {gridStories.length > 4 && (
                <div className="mt-20 pt-12 border-t-8 border-double border-ink relative">
                    {/* Decorative Star */}
                    <div className="absolute top-[-2rem] left-1/2 -translate-x-1/2 bg-wash-red border-4 border-ink w-16 h-16 rounded-full flex items-center justify-center font-ink text-white text-2xl z-10 shadow-sm">
                        ★
                    </div>

                    <SectionHeader title="The Archive Pile" color="purple" align="center" />
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                        {gridStories.slice(4).map(item => (
                            <div key={item.id} className="opacity-70 hover:opacity-100 hover:scale-105 transition-all duration-300 transform">
                                <NewsCard 
                                    item={item} 
                                    variant="standard" 
                                    onClick={handleArticleClick} 
                                />
                            </div>
                        ))}
                    </div>
                </div>
            )}
          </>
        )}

        {/* --- FOOTER --- */}
        <footer className="mt-24 text-center border-t-4 border-ink pt-8 pb-12 opacity-80 bg-ink text-paper -mx-4 md:-mx-8 px-4 md:px-8">
            <h2 className="font-ink text-4xl mb-4">AI COMIC DAILY NEWS</h2>
            <div className="font-hand text-xl space-x-6 mb-6">
                <a href="#" className="underline decoration-2 decoration-wash-red hover:text-wash-red transition-colors">About Us</a>
                <a href="#" className="underline decoration-2 decoration-wash-blue hover:text-wash-blue transition-colors">Submissions</a>
                <a href="#" className="underline decoration-2 decoration-wash-yellow hover:text-wash-yellow transition-colors">Complaints Dept</a>
            </div>
            <p className="font-hand text-sm opacity-60">
                &copy; {new Date().getFullYear()} AI Comic Daily News. Printed on recycled pixels.
            </p>
        </footer>

      </div>

      <ArticleModal 
        item={selectedArticle} 
        onClose={() => setSelectedArticle(null)} 
      />
    </div>
  );
};

export default App;
