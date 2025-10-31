import React, { useState } from 'react';
import { Edit, Trash2 } from 'lucide-react';
import PrimaryButton from './PrimaryButton';
import { motion, AnimatePresence } from 'framer-motion';

// --- 1. IMPORT THE NEW CSS FILE ---
import './ProductManagementCard.css';

const ProductManagementCard = ({ product, onEdit, onDelete }) => {
  const [isHovered, setIsHovered] = useState(false);
  return (
    // --- 2. ADD THE 'glowing-product-card' WRAPPER ---
    <div className="glowing-product-card">
      
      {/* --- 3. ADDED 'bg-white', 'rounded-2xl', 'shadow-lg' ---
        This makes your card visible on the light canvas background.
        'overflow-hidden' is preserved to clip the image.
      */}
      <div
        className="relative card-warm card-hover group overflow-hidden w-full bg-white rounded-2xl shadow-lg"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="aspect-square">
          <img src={product.imageUrl} alt={product.title} className="w-full h-full object-cover" />
          <AnimatePresence>
            {isHovered && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 bg-black/70 flex items-center justify-center space-x-4" // Changed from bg-charcoal
              >
                <PrimaryButton onClick={onEdit} variant="outline" size="sm" icon={<Edit className="h-4 w-4" />}>
                  Edit
                </PrimaryButton>
                <PrimaryButton onClick={onDelete} variant="wood" size="sm" icon={<Trash2 className="h-4 w-4" />}>
                  Delete
                </PrimaryButton>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* --- 4. UPDATED TEXT COLORS TO AMBER THEME --- */}
        <div className="p-4">
          <h3 className="font-serif font-bold text-lg mb-1 text-amber-900">{product.title}</h3>
          <p className="text-amber-700 text-sm mb-2">{product.category}</p>
          <div className="flex items-center justify-between">
            <span className="text-xl font-bold text-amber-600">₹{product.price}</span>
            <span className="text-xs text-amber-600">ID: {product.id}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductManagementCard;