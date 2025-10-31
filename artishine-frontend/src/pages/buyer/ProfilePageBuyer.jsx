import React, { useState } from 'react';
import PrimaryButton from '../../components/PrimaryButton';
import Navigation from '../../components/Navigation';
import { User } from 'lucide-react';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const ProfilePageBuyer = () => {
  const [profile, setProfile] = useState({
    name: 'Priya Sharma',
    email: 'priya@example.com',
    phone: '+91 98765 43210',
    address: '123 MG Road, Bangalore, Karnataka 560001',
  });

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
            <h1 className="text-3xl text-amber-900 font-serif font-bold mb-2">My Profile</h1>
            <p className="text-amber-700 font-semibold">Manage your account information</p>
          </div>
          <div className="space-y-6">
            <div className="text-center">
              {/* --- 6. AVATAR COLORS UPDATED --- */}
              <div className="w-24 h-24 bg-amber-500 rounded-full mx-auto mb-4 flex items-center justify-center">
                <User className="h-12 w-12 text-white" />
              </div>
              <PrimaryButton variant="outline" size="sm">Upload Photo</PrimaryButton>
            </div>
            
            {/* --- 7. CARD AND FORM COLORS UPDATED --- */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Full Name</label>
                <input type="text" value={profile.name} onChange={(e) => setProfile((prev) => ({ ...prev, name: e.target.value }))} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Email</label>
                <input type="email" value={profile.email} onChange={(e) => setProfile((prev) => ({ ...prev, email: e.target.value }))} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Phone</label>
                <input type="tel" value={profile.phone} onChange={(e) => setProfile((prev) => ({ ...prev, phone: e.target.value }))} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Default Delivery Address</label>
                <textarea value={profile.address} onChange={(e) => setProfile((prev) => ({ ...prev, address: e.target.value }))} rows={3} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300 resize-none" />
              </div>
              <PrimaryButton size="lg" className="w-full">Save Changes</PrimaryButton>
            </div>
          </div>
        </div>
      </div>
      <Navigation userRole="buyer" />
    </div>
  );
};

export default ProfilePageBuyer;