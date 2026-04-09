import { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { Link, useLocation } from 'react-router-dom';
import { cn } from '../lib/utils';
import { MagneticButton } from './MagneticButton';

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-6 md:px-12",
        scrolled ? "py-4" : "py-8"
      )}
    >
      <div
        className={cn(
          "max-w-7xl mx-auto flex items-center justify-between rounded-full transition-all duration-300",
          scrolled ? "glass-panel px-6 py-3" : "px-0 py-0"
        )}
      >
        <Link to="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-electric neon-glow flex items-center justify-center">
            <div className="w-3 h-3 bg-midnight rounded-full" />
          </div>
          <span className="font-display font-bold text-xl tracking-tight">Hatobot Turf</span>
        </Link>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-white/70">
          <Link 
            to="/" 
            className={cn("transition-colors hover:text-electric", location.pathname === '/' && "text-electric")}
          >
            Home
          </Link>
          <Link 
            to="/book" 
            className={cn("transition-colors hover:text-electric", location.pathname === '/book' && "text-electric")}
          >
            Book Now
          </Link>
          <a href="#contact" className="hover:text-electric transition-colors">Contact</a>
        </div>

        <MagneticButton className="px-6 py-2 text-sm" glow={false}>
          Sign In
        </MagneticButton>
      </div>
    </motion.nav>
  );
}
