import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

// --- This path is corrected to '..' ---
import AnimatedBackground from '../components/AnimatedBackground'; 

const HomePage = () => {
  const navigate = useNavigate();

  // --- Removed the 'useEffect' block ---

  return (
    <div className="min-h-screen overflow-hidden relative">
      
      {/* --- Added the new background component --- */}
      <AnimatedBackground />

      {/* --- Removed the old decorative blobs --- */}

      {/* Navigation */}
      <nav className="relative z-10 container mx-auto px-6 py-6">
        <div className="flex items-center justify-between">
          <div className="text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-800 to-amber-900 cursor-none" data-cursor="pointer">
            Artishine
          </div>
          <div className="space-x-5">
            <button 
              onClick={() => window.location.href = '/login'}
              className="px-6 py-2.5 text-xl font-bold text-amber-900 hover:text-amber-700 transition-colors cursor-none border-2 border-amber-800 rounded-lg hover:bg-amber-50/50"
              data-cursor="pointer"
            >
              Sign In
            </button>
            <button 
              onClick={() => window.location.href = '/register'}
              className="px-6 py-2.5 bg-gradient-to-r text-xl from-amber-700 to-amber-800 text-white font-medium rounded-lg hover:from-amber-800 hover:to-amber-900 transition-all shadow-lg hover:shadow-amber-200 cursor-none"
              data-cursor="pointer"
            >
              Join Now
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative z-10 container mx-auto px-6 py-16 md:py-24 lg:py-32">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <motion.h1 
            className="text-4xl md:text-6xl lg:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-amber-900 to-amber-700 leading-tight"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Discover Handcrafted Treasures from Artisans Near You
          </motion.h1>
          
          <motion.p 
            className="text-xl font-extrabold text-amber-900/90 mb-12 max-w-2xl mx-auto leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            Connect with skilled artisans and explore unique, handmade products that tell a story.
          </motion.p>
          
          <motion.div
            className="flex flex-col sm:flex-row justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
          >
            <button 
              onClick={() => navigate('/register')}
              className="px-10 py-4 bg-gradient-to-r from-amber-600 to-amber-700 text-white text-lg font-semibold rounded-full hover:from-amber-700 hover:to-amber-800 transition-all shadow-lg hover:shadow-xl hover:-translate-y-0.5 cursor-none"
              data-cursor="pointer"
            >
              Explore Crafts
            </button>
            <button 
              onClick={() => navigate('/register')}
              className="px-10 py-4 text-amber-900 border-2 border-amber-800 text-lg font-semibold rounded-full hover:bg-amber-50/50 transition-all cursor-none"
              data-cursor="pointer"
            >
              Meet Artisans
            </button>
          </motion.div>
        </div>
      </main>

      {/* Features Section */}
      <section className="relative z-10 py-16 md:py-24">
        <div className="container mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-amber-900 mb-16">
            Why Choose Artishine?
          </h2>
          
          {/* This 'div' block is now clean */}
          <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
            {[
              {
                icon: '🖌️',
                title: 'Authentic Handmade',
                description: 'Each piece is carefully crafted by skilled artisans with traditional techniques.'
              },
              {
                icon: '🌍',
                title: 'Local and Global Reach',
                description: 'Discover unique crafts from artisans around the world, all in one place.'
              },
              {
                icon: '💫',
                title: 'Support Local',
                description: 'Your purchase directly supports independent artisans and their communities.'
              }
            ].map((feature, index) => (
              <motion.div 
                key={index}
                className="p-8 bg-white/60 backdrop-blur-sm rounded-2xl text-center shadow-lg hover:shadow-xl transition-all hover:-translate-y-1 border border-amber-100"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-100px" }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                data-cursor="pointer"
              >
                <div className="text-5xl mb-6">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-amber-800 mb-3">{feature.title}</h3>
                <p className="text-amber-900/80">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 bg-amber-900/90 text-amber-100 py-12 mt-16">
        <div className="container mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-2xl font-bold mb-4 md:mb-0">Artishine</div>
            <div className="flex space-x-6">
              <a href="#" className="hover:text-amber-300 transition-colors">About</a>
              <a href="#" className="hover:text-amber-300 transition-colors">Contact</a>
              <a href="#" className="hover:text-amber-300 transition-colors">FAQ</a>
              <a href="#" className="hover:text-amber-3Openingm-colors">Terms</a>
            </div>
          </div>
          <div className="border-t border-amber-800 mt-8 pt-8 text-center md:text-left">
            <p>© {new Date().getFullYear()} Artishine. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;