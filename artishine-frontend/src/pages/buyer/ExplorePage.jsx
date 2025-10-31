import React, { useState } from 'react';
import sampleData from '../../data/sampleData';
import TinderCard from 'react-tinder-card';
import ProductDiscoveryCard from '../../components/ProductDiscoveryCard';
import PrimaryButton from '../../components/PrimaryButton';
import Navigation from '../../components/Navigation';
import { Heart, Sparkles, X } from 'lucide-react';
import { motion } from 'framer-motion';

// --- 1. IMPORT THE NEW CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const ExplorePage = () => {
  const [currentProducts, setCurrentProducts] = useState(sampleData.products);
  const [cartItems, setCartItems] = useState([]);
  const [lastDirection, setLastDirection] = useState('');

  // --- No useEffect needed, the canvas component handles its own background color ---

  const swiped = (direction, productId) => {
    setLastDirection(direction);
    if (direction === 'right') {
      const product = currentProducts.find((p) => p.id === productId);
      if (product) setCartItems((prev) => [...prev, product]);
    }
  };

  const outOfFrame = (productId) => setCurrentProducts((prev) => prev.filter((p) => p.id !== productId));

  const addToCart = (product) => {
    setCartItems((prev) => [...prev, product]);
    setCurrentProducts((prev) => prev.filter((p) => p.id !== product.id));
  };

  return (
    // --- 2. ADD 'relative' TO THE MAIN WRAPPER ---
    <div className="min-h-screen pb-20 pt-20 relative">
      
      {/* --- 3. ADD THE CANVAS BACKGROUND WITH YOUR COLORS --- */}
      <CanvasBackground
        backgroundColor="#f9feffff"
        elementColors={['#ff620062', '#005cdc5a']}
      />

      {/* --- 4. ADD 'relative z-10' TO CONTENT --- */}
      <div className="p-6 relative z-10">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS CHANGED TO AMBER --- */}
            <h1 className="text-3xl text-amber-900 font-serif font-bold mb-2">Discover Crafts</h1>
            <p className="text-amber-700 font-semibold">Swipe right to add to cart, left to skip</p>
          </div>
          <div className="relative h-[85vh] mb-6">
            {currentProducts.length > 0 ? (
              currentProducts.map((product) => (
                <TinderCard key={product.id} onSwipe={(dir) => swiped(dir, product.id)} onCardLeftScreen={() => outOfFrame(product.id)} preventSwipe={['up', 'down']} className="absolute inset-0">
                  <ProductDiscoveryCard product={product} onAddToCart={() => addToCart(product)} />
                </TinderCard>
              ))
            ) : (
              // --- 6. EMPTY STATE COLORS UPDATED ---
              <div className="bg-white/80 backdrop-blur-sm h-full flex flex-col items-center justify-center text-center p-8 space-y-4 rounded-2xl shadow-lg">
                <Sparkles className="h-16 w-16 text-amber-500" />
                <h2 className="text-2xl font-serif font-bold text-amber-900">You've explored all crafts!</h2>
                <p className="text-amber-700 font-semibold">Check back later for new artisan creations</p>
                <PrimaryButton onClick={() => setCurrentProducts(sampleData.products)}>Restart Discovery</PrimaryButton>
              </div>
            )}
          </div>
          {currentProducts.length > 0 && (
            // --- 7. BUTTON COLORS UPDATED ---
            <div className="flex items-center justify-center space-x-8">
              <button onClick={() => swiped('left', currentProducts[currentProducts.length - 1]?.id)} className="w-16 h-16 rounded-full bg-white border-2 border-red-300 flex items-center justify-center hover:bg-red-50 transition-all duration-300 hover:scale-110 shadow-lg">
                <X className="h-8 w-8 text-red-500" />
              </button>
              <button onClick={() => swiped('right', currentProducts[currentProducts.length - 1]?.id)} className="w-16 h-16 rounded-full bg-amber-500 flex items-center justify-center hover:bg-amber-600 transition-all duration-300 hover:scale-110 shadow-lg">
                <Heart className="h-8 w-8 text-white" />
              </button>
            </div>
          )}
          {cartItems.length > 0 && (
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="fixed top-6 right-6 bg-amber-500 text-white w-12 h-12 rounded-full flex items-center justify-center font-bold shadow-lg z-10">
              {cartItems.length}
            </motion.div>
          )}
        </div>
      </div>
      <Navigation userRole="buyer" />
    </div>
  );
};

export default ExplorePage;