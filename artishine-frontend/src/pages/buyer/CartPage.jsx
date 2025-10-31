import React, { useState } from 'react';
import sampleData from '../../data/sampleData';
import { Trash2, ShoppingCart } from 'lucide-react';
import PrimaryButton from '../../components/PrimaryButton';
import Navigation from '../../components/Navigation';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const CartPage = () => {
  const [cartItems, setCartItems] = useState([sampleData.products[0], sampleData.products[2]]);
  const removeFromCart = (productId) => setCartItems((prev) => prev.filter((i) => i.id !== productId));
  const total = cartItems.reduce((sum, item) => sum + item.price, 0);

  return (
    // --- 2. ADD 'relative' TO THE MAIN WRAPPER ---
    <div className="min-h-screen pb-20 pt-20 relative">

      {/* --- 3. ADD THE CANVAS BACKGROUND WITH YOUR COLORS --- */}
      <CanvasBackground
        backgroundColor="#f9feffff"
        elementColors={['#ff620062', '#005cdc5a']}
      />

      {/* --- 4. ADD 'relative z-10' TO YOUR CONTENT WRAPPER --- */}
      <div className="p-6 relative z-10">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS UPDATED FOR LIGHT BACKGROUND --- */}
            <h1 className="text-3xl text-amber-900 font-serif font-bold mb-2">Your Cart</h1>
            <p className="text-amber-700 font-semibold">{cartItems.length} item{cartItems.length !== 1 ? 's' : ''} selected</p>
          </div>

          {cartItems.length > 0 ? (
            <div className="space-y-6">
              <div className="space-y-4">
                {cartItems.map((item) => (
                  // --- 6. CARD STYLES UPDATED ---
                  <div key={item.id} className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-4 flex items-center space-x-4">
                    <img src={item.imageUrl} alt={item.title} className="w-20 h-20 object-cover rounded-lg" />
                    <div className="flex-1">
                      {/* --- 7. TEXT COLORS UPDATED --- */}
                      <h3 className="font-serif font-bold text-lg text-amber-900">{item.title}</h3>
                      <p className="text-amber-700 text-sm">{item.category}</p>
                      <p className="text-amber-600 font-bold">₹{item.price}</p>
                    </div>
                    <button onClick={() => removeFromCart(item.id)} className="text-amber-600 hover:text-red-500 transition-colors p-2">
                      <Trash2 className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
              
              {/* --- 6. CARD STYLES UPDATED --- */}
              <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 space-y-4">
                <h3 className="font-serif font-bold text-xl text-amber-900">Order Summary</h3>
                <div className="space-y-2 text-amber-800"> {/* Default text color for summary */}
                  <div className="flex justify-between"><span>Subtotal</span><span>₹{total}</span></div>
                  <div className="flex justify-between"><span>Shipping</span><span>Free</span></div>
                  <div className="border-t border-amber-300 pt-2">
                    <div className="flex justify-between font-bold text-lg text-amber-900">
                      <span>Total</span>
                      <span className="text-amber-600">₹{total}</span>
                    </div>
                  </div>
                </div>
                <PrimaryButton size="lg" className="w-full" onClick={() => alert('Proceeding to checkout...')}>
                  Proceed to Checkout
                </PrimaryButton>
              </div>
            </div>
          ) : (
            // --- 7. EMPTY STATE COLORS UPDATED ---
            <div className="text-center py-12 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg">
              <ShoppingCart className="h-16 w-16 text-amber-600 mx-auto mb-4" />
              <h3 className="text-xl font-serif font-bold mb-2 text-amber-900">Your cart is empty</h3>
              <p className="text-amber-700 font-semibold mb-6">Discover beautiful crafts in the explore section</p>
              <PrimaryButton onClick={() => (window.location.href = '/explore')}>Start Shopping</PrimaryButton>
            </div>
          )}
        </div>
      </div>
      <Navigation userRole="buyer" />
    </div>
  );
};

export default CartPage;