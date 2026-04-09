import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { format, addDays } from 'date-fns';
import { Check, Calendar as CalendarIcon, ChevronRight } from 'lucide-react';
import { cn } from '../lib/utils';
import { MagneticButton } from './MagneticButton';

const SPORTS = ['Football', 'Cricket', 'Pickleball'];

const TURF_SLOTS = [
  "06:00 AM - 07:00 AM",
  "07:00 AM - 08:00 AM",
  "08:00 AM - 09:00 AM",
  "09:00 AM - 10:00 AM",
  "04:00 PM - 05:00 PM",
  "05:00 PM - 06:00 PM",
  "06:00 PM - 07:00 PM",
  "07:00 PM - 08:00 PM",
  "08:00 PM - 09:00 PM",
  "09:00 PM - 10:00 PM",
];

const API_BASE = ""; // Relative since same domain

export function BookingSection() {
  const [selectedSport, setSelectedSport] = useState(SPORTS[0]);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Mock dates for next 7 days
  const dates = Array.from({ length: 7 }).map((_, i) => addDays(new Date(), i));
  const [slots, setSlots] = useState<{id: string, time: string, available: boolean}[]>([]);

  const fetchAvailability = async (date: Date) => {
    try {
      const dateStr = format(date, 'yyyy-MM-dd');
      const res = await fetch(`${API_BASE}/api/turf/availability?date=${dateStr}`);
      const bookedIndices = await res.json(); // { "0": {...}, "1": {...} }

      const updatedSlots = TURF_SLOTS.map((time, index) => ({
        id: index.toString(),
        time,
        available: !bookedIndices[index.toString()]
      }));
      setSlots(updatedSlots);
    } catch (err) {
      console.error("Failed to fetch availability:", err);
    }
  };

  useEffect(() => {
    fetchAvailability(selectedDate);
  }, [selectedDate]);

  const handleDateChange = (date: Date) => {
    setSelectedDate(date);
    setSelectedSlots([]);
    setError(null);
  };

  const toggleSlot = (id: string) => {
    setSelectedSlots(prev => 
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  const handleBook = async () => {
    if (selectedSlots.length === 0 || !name || !phone) {
        setError("Please fill in all details and select at least one slot.");
        return;
    }
    
    setIsLoading(true);
    setError(null);

    try {
      const dateStr = format(selectedDate, 'yyyy-MM-dd');
      const res = await fetch(`${API_BASE}/api/turf/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: dateStr,
          slots: selectedSlots,
          name,
          phone
        })
      });

      const result = await res.json();

      if (res.ok) {
        setIsBooked(true);
      } else {
        setError(result.error || "Something went wrong. Please try again.");
        // Refresh availability in case slots were taken
        fetchAvailability(selectedDate);
      }
    } catch (err) {
      setError("Failed to connect to server. Please check your internet.");
    } finally {
      setIsLoading(false);
    }
  };

  const getSelectedTimes = () => {
    return slots
      .filter(s => selectedSlots.includes(s.id))
      .map(s => s.time)
      .join(', ');
  };

  return (
    <section className="pt-40 pb-24 px-6 relative z-10 min-h-screen overflow-hidden">
      {/* Background Image */}
      <div className="absolute inset-0 z-0 fixed">
        <div className="absolute inset-0 bg-midnight/90 z-10" />
        <img 
          src="https://images.unsplash.com/photo-1589487391730-58f20eb2c308?q=80&w=2000&auto=format&fit=crop" 
          alt="Turf background" 
          className="w-full h-full object-cover opacity-30"
          referrerPolicy="no-referrer"
        />
      </div>

      <div className="max-w-5xl mx-auto relative z-10">
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6">Reserve Your Turf</h2>
          <p className="text-white/60 max-w-2xl mx-auto">Select your sport, pick a date, and lock in your time. You can select multiple slots.</p>
        </div>

        <AnimatePresence mode="wait">
          {!isBooked ? (
            <motion.div
              layout
              key="booking-form"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9, filter: "blur(10px)" }}
              transition={{ duration: 0.4 }}
              className="glass-panel rounded-[2rem] p-6 md:p-10"
            >
              {/* Sport Selector */}
              <div className="mb-10">
                <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">1. Select Sport</h3>
                <div className="flex flex-wrap gap-3">
                  {SPORTS.map(sport => (
                    <button
                      key={sport}
                      onClick={() => setSelectedSport(sport)}
                      className={cn(
                        "px-6 py-3 rounded-full font-medium transition-all duration-300",
                        selectedSport === sport 
                          ? "bg-electric text-midnight shadow-[0_0_15px_rgba(57,255,20,0.3)]" 
                          : "bg-white/5 text-white hover:bg-white/10"
                      )}
                    >
                      {sport}
                    </button>
                  ))}
                </div>
              </div>

              {/* Date Picker */}
              <div className="mb-10">
                <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">2. Select Date</h3>
                <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide -mx-6 px-6 md:mx-0 md:px-0">
                  {dates.map((date, i) => {
                    const isSelected = date.toDateString() === selectedDate.toDateString();
                    return (
                      <button
                        key={i}
                        onClick={() => handleDateChange(date)}
                        className={cn(
                          "flex-shrink-0 flex flex-col items-center justify-center w-20 h-24 rounded-2xl transition-all duration-300",
                          isSelected 
                            ? "bg-white text-midnight" 
                            : "bg-white/5 text-white hover:bg-white/10"
                        )}
                      >
                        <span className="text-xs font-semibold uppercase mb-1">{format(date, 'EEE')}</span>
                        <span className="font-display text-2xl font-bold">{format(date, 'd')}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* User Details */}
              <div className="mb-10 grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">4. Full Name</h3>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your name"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-electric transition-colors"
                  />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">5. Phone Number</h3>
                  <input
                    type="tel"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="e.g. 919884899024"
                    className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-electric transition-colors"
                  />
                </div>
              </div>

              {/* Time Slots */}
              <div className="mb-12">
                <h3 className="text-sm font-semibold text-white/50 uppercase tracking-wider mb-4">3. Select Time(s)</h3>
                {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {slots.map((slot) => {
                    const isSelected = selectedSlots.includes(slot.id);
                    return (
                      <motion.button
                        key={slot.id}
                        disabled={!slot.available}
                        onClick={() => toggleSlot(slot.id)}
                        whileHover={slot.available ? { scale: 1.05 } : {}}
                        whileTap={slot.available ? { scale: 0.95 } : {}}
                        className={cn(
                          "relative h-16 rounded-xl font-display font-medium text-lg transition-all duration-300 flex items-center justify-center overflow-hidden",
                          !slot.available && "opacity-40 cursor-not-allowed stripe-pattern border border-white/5",
                          slot.available && !isSelected && "bg-white/5 hover:bg-white/10 border border-white/10 hover:border-electric/50 hover:neon-glow",
                          isSelected && "bg-electric text-midnight neon-glow"
                        )}
                      >
                        {slot.time}
                      </motion.button>
                    );
                  })}
                </div>
              </div>

              {/* Action */}
              <div className="flex justify-end pt-6 border-t border-white/10">
                <MagneticButton 
                  onClick={handleBook}
                  disabled={selectedSlots.length === 0 || isLoading}
                  className={cn(
                    "flex items-center gap-2",
                    (selectedSlots.length === 0 || isLoading) && "opacity-50 cursor-not-allowed"
                  )}
                  glow={selectedSlots.length > 0 && !isLoading}
                >
                  {isLoading ? 'Processing...' : `Confirm ${selectedSlots.length > 0 ? selectedSlots.length : ''} Booking${selectedSlots.length > 1 ? 's' : ''}`} <ChevronRight className="w-5 h-5" />
                </MagneticButton>
              </div>
            </motion.div>
          ) : (
            <motion.div
              layout
              key="success-state"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ type: "spring", damping: 20, stiffness: 100 }}
              className="glass-panel rounded-[2rem] p-16 flex flex-col items-center justify-center text-center min-h-[500px]"
            >
              <motion.div 
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: "spring", damping: 12, stiffness: 200 }}
                className="w-24 h-24 rounded-full bg-electric flex items-center justify-center mb-8 neon-glow"
              >
                <Check className="w-12 h-12 text-midnight" strokeWidth={3} />
              </motion.div>
              <h3 className="font-display text-4xl font-bold mb-4">Booking Confirmed!</h3>
              <p className="text-white/60 text-lg max-w-md">
                You're all set for {selectedSport} on {format(selectedDate, 'MMMM do')} at {getSelectedTimes()}.
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
