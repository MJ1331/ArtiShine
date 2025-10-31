import React, { useState } from 'react';
import sampleData from '../../data/sampleData';
import PrimaryButton from '../../components/PrimaryButton';
import ProductManagementCard from '../../components/ProductManagementCard';
import Navigation from '../../components/Navigation';
import { Plus } from 'lucide-react';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const ManageProductsPage = () => {
  const [products] = useState(sampleData.products);
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
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              {/* --- 5. TEXT COLORS UPDATED FOR LIGHT BACKGROUND --- */}
              <h1 className="text-3xl font-serif font-bold mb-2 text-amber-900">My Products</h1>
              <p className="text-amber-700 font-semibold">Manage your digital storefront</p>
            </div>
            <PrimaryButton onClick={() => (window.location.href = '/upload')} icon={<Plus className="h-5 w-5" />}>
              Add Product
            </PrimaryButton>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {products.map((product) => (
              <ProductManagementCard key={product.id} product={product} onEdit={() => alert(`Edit ${product.title}`)} onDelete={() => alert(`Delete ${product.title}`)} />
            ))}
          </div>
        </div>
      </div>
      <Navigation userRole="artisan" />
    </div>
  );
};

export default ManageProductsPage;