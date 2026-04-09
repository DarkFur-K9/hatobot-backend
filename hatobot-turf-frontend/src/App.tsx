import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { Features } from './components/Features';
import { BookingSection } from './components/BookingSection';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-midnight text-white selection:bg-electric selection:text-midnight">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={
              <>
                <Hero />
                <Features />
              </>
            } />
            <Route path="/book" element={<BookingSection />} />
          </Routes>
        </main>
        
        <footer className="bg-midnight border-t border-white/10 py-12 px-6 text-center">
          <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-electric flex items-center justify-center">
                <div className="w-2 h-2 bg-midnight rounded-full" />
              </div>
              <span className="font-display font-bold tracking-tight">Hatobot Turf</span>
            </div>
            <p className="text-white/40 text-sm">
              © {new Date().getFullYear()} Hatobot Turf. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm text-white/60">
              <a href="#" className="hover:text-electric transition-colors">Terms</a>
              <a href="#" className="hover:text-electric transition-colors">Privacy</a>
            </div>
          </div>
        </footer>
      </div>
    </BrowserRouter>
  );
}
