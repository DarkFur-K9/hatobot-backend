import { motion } from 'motion/react';
import { Zap, Shield, Clock } from 'lucide-react';

const features = [
  {
    icon: Zap,
    title: "Instant Booking",
    description: "No calls, no waiting. See live availability and secure your turf in seconds."
  },
  {
    icon: Shield,
    title: "Premium Quality",
    description: "FIFA-certified artificial grass with shock pads for maximum performance and safety."
  },
  {
    icon: Clock,
    title: "24/7 Access",
    description: "Floodlights that turn night into day. Play whenever the passion strikes."
  }
];

export function Features() {
  return (
    <section id="features" className="py-32 px-6 relative z-10 bg-midnight">
      <div className="max-w-7xl mx-auto">
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          className="text-center mb-20"
        >
          <h2 className="font-display text-4xl md:text-5xl font-bold mb-6">Why Choose Us</h2>
          <div className="w-24 h-1 bg-electric mx-auto rounded-full neon-glow" />
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 50 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-50px" }}
              transition={{ delay: index * 0.1, duration: 0.6, ease: "easeOut" }}
              className="glass-panel p-8 rounded-3xl group hover:border-electric/50 transition-colors duration-500"
            >
              <div className="w-14 h-14 rounded-2xl bg-midnight-light flex items-center justify-center mb-6 group-hover:bg-electric/10 transition-colors duration-500">
                <feature.icon className="w-6 h-6 text-electric" />
              </div>
              <h3 className="font-display text-2xl font-semibold mb-4">{feature.title}</h3>
              <p className="text-white/60 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
