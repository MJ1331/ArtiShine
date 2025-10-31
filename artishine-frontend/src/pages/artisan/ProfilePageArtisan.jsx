import React, { useState } from 'react';
import PrimaryButton from '../../components/PrimaryButton';
import Navigation from '../../components/Navigation';
import { Instagram, Sparkles, User } from 'lucide-react';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const ProfilePageArtisan = () => {
  const [profile, setProfile] = useState({
    name: 'Meera Devi',
    email: 'meera@example.com',
    shopName: 'Clay Dreams Studio',
    location: 'Jaipur, Rajasthan',
    bio: 'Master potter with 30 years of experience, keeping ancient traditions alive',
    isInstagramConnected: true,
    instagramHandle: '@clayreamsstudio',
  });
  const [isGeneratingBio, setIsGeneratingBio] = useState(false);

  const handleGenerateBio = async () => {
    setIsGeneratingBio(true);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setProfile((prev) => ({
      ...prev,
      bio:
        'Master potter with three decades of experience, Meera Devi transforms humble clay into extraordinary art. Her work bridges ancient traditions with contemporary aesthetics, creating pieces that tell stories of heritage and innovation. Each creation from her studio reflects her deep understanding of ceramic arts and her commitment to preserving traditional craftsmanship for future generations.',
    }));
    setIsGeneratingBio(false);
  };

  return (
    // --- 2. ADD 'relative' TO THE MAIN WRAPPER ---
    <div className="min-h-screen pb-20 md:pb-6 pt-20 relative">

      {/* --- 3. ADD THE CANVAS BACKGROUND WITH YOUR COLORS --- */}
      <CanvasBackground
        backgroundColor="#f9feffff" // Using the light color you requested
        elementColors={['#ff620062', '#005cdc5a']} // Using the element colors you requested
      />

      {/* --- 4. ADD 'relative z-10' TO YOUR CONTENT WRAPPER --- */}
      <div className="p-6 relative z-10">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS UPDATED FOR LIGHT BACKGROUND --- */}
            <h1 className="text-3xl font-serif font-bold mb-2 text-amber-900">My Artisan Profile</h1>
            <p className="text-amber-700 font-semibold">Manage your artisan identity and shop details</p>
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
            <div className="bg-white/50 backdrop-blur-sm rounded-2xl shadow-lg p-6 space-y-6">
              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Name</label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => setProfile((prev) => ({ ...prev, name: e.target.value }))}
                  className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Shop Name</label>
                <input
                  type="text"
                  value={profile.shopName}
                  onChange={(e) => setProfile((prev) => ({ ...prev, shopName: e.target.value }))}
                  className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2 text-amber-900">Location</label>
                <input
                  type="text"
                  value={profile.location}
                  onChange={(e) => setProfile((prev) => ({ ...prev, location: e.target.value }))}
                  className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="text-sm font-medium text-amber-900">About My Craft</label>
                  <PrimaryButton
                    onClick={handleGenerateBio}
                    disabled={isGeneratingBio}
                    variant="outline"
                    size="sm"
                    icon={<Sparkles className="h-4 w-4" />}
                  >
                    {isGeneratingBio ? 'Generating...' : '✨ Generate Bio'}
                  </PrimaryButton>
                </div>
                <textarea
                  value={profile.bio}
                  onChange={(e) => setProfile((prev) => ({ ...prev, bio: e.target.value }))}
                  rows={6}
                  className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300 resize-none"
                  placeholder="Tell your story..."
                />
              </div>

              <div className="flex items-center justify-between p-4 border border-amber-300 rounded-lg bg-white/50">
                <div className="flex items-center space-x-3">
                  <Instagram className="h-6 w-6 text-amber-600" />
                  <div>
                    <p className="font-medium text-amber-900">
                      {profile.isInstagramConnected ? 'Connected to Instagram' : 'Connect Instagram'}
                    </p>
                    <p className="text-sm text-amber-700">
                      {profile.isInstagramConnected ? profile.instagramHandle : 'Auto-share your products'}
                    </p>
                  </div>
                </div>
                <PrimaryButton
                  variant={profile.isInstagramConnected ? 'wood' : 'terracotta'}
                  size="sm"
                >
                  {profile.isInstagramConnected ? 'Disconnect' : 'Connect'}
                </PrimaryButton>
              </div>

              <PrimaryButton size="lg" className="w-full">
                Save Changes
              </PrimaryButton>
            </div>
          </div>
        </div>
      </div>
      <Navigation userRole="artisan" />
    </div>
  );
};

export default ProfilePageArtisan;