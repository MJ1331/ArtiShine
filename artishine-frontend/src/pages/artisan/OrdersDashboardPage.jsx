import React, { useState } from 'react';
import sampleData from '../../data/sampleData';
import OrderCard from '../../components/OrderCard';
import Navigation from '../../components/Navigation';
import { Package } from 'lucide-react';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const OrdersDashboardPage = () => {
  const [activeTab, setActiveTab] = useState('new');
  const [orders, setOrders] = useState(sampleData.orders);

  const tabs = [
    { id: 'new', label: 'New', count: orders.filter((o) => o.status === 'new').length },
    { id: 'progress', label: 'In Progress', count: orders.filter((o) => o.status === 'progress').length },
    { id: 'completed', label: 'Completed', count: orders.filter((o) => o.status === 'completed').length },
  ];

  const filteredOrders = orders.filter((order) => order.status === activeTab);
  const handleStatusUpdate = (orderId, newStatus) => setOrders((prev) => prev.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o)));

  return (
    // --- 2. ADD 'relative' TO THE MAIN WRAPPER ---
    <div className="min-h-screen pb-20 pt-20 relative">

      {/* --- 3. ADD THE CANVAS BACKGROUND WITH YOUR COLORS --- */}
      <CanvasBackground
        backgroundColor="#f9feffff" // Using the light color you requested
        elementColors={['#ff620062', '#005cdc5a']} // Using the element colors you requested
      />

      {/* --- 4. ADD 'relative z-10' TO YOUR CONTENT WRAPPER --- */}
      <div className="p-6 relative z-10">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS UPDATED FOR LIGHT BACKGROUND --- */}
            <h1 className="text-3xl font-serif font-bold mb-2 text-amber-900">Orders Dashboard</h1>
            <p className="text-amber-700 font-semibold">Manage your incoming orders</p>
          </div>

          {/* --- 6. TAB COLORS UPDATED FOR AMBER THEME --- */}
          <div className="flex space-x-1 mb-8 bg-amber-100 p-1 rounded-lg">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-3 px-4 rounded-lg font-semibold font-medium transition-all duration-300 ${
                  activeTab === tab.id
                    ? 'bg-amber-500/90 text-white shadow-md' // Active tab
                    : 'text-amber-700 hover:bg-amber-500/10' // Inactive tab
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          <div className="space-y-4">
            {filteredOrders.length > 0 ? (
              filteredOrders.map((order) => <OrderCard key={order.id} order={order} onStatusUpdate={handleStatusUpdate} />)
            ) : (
              // --- 7. EMPTY STATE COLORS UPDATED ---
              <div className="text-center py-12 bg-amber-50/50 rounded-lg">
                <Package className="h-16 w-16 text-amber-600 mx-auto mb-4" />
                <h3 className="text-xl font-serif font-bold mb-2 text-amber-900">No orders in this category</h3>
                <p className="text-amber-700">Orders will appear here when customers place them</p>
              </div>
            )}
          </div>
        </div>
      </div>
      <Navigation userRole="artisan" />
    </div>
  );
};

export default OrdersDashboardPage;