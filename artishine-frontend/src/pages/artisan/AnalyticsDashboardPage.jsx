import React from 'react';
import sampleData from '../../data/sampleData';
import StatCard from '../../components/StatCard';
import Navigation from '../../components/Navigation';
import { Eye, Heart, Instagram, MessageCircle, ThumbsUp, TrendingUp } from 'lucide-react';

// --- 1. IMPORT THE CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const AnalyticsDashboardPage = () => {
  const analytics = sampleData.analytics;
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
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS UPDATED FOR LIGHT BACKGROUND --- */}
            <h1 className="text-3xl font-serif font-bold mb-2 text-amber-900">Analytics Dashboard</h1>
            <p className="text-amber-700 font-semibold">Track your business performance</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {/* --- 6. UPDATED 'text-primary' TO AMBER --- */}
            <StatCard title="Weekly Sales" value={`₹${analytics.weeklySales.toLocaleString()}`} icon={<TrendingUp className="h-6 w-6 text-amber-600" />} trend="12%" color="amber-600" />
            <StatCard title="Total Views" value={analytics.totalViews.toLocaleString()} icon={<Eye className="h-6 w-6 text-blue-500" />} trend="8%" color="blue-500" />
            <StatCard title="Products Liked" value={analytics.productsLiked.toString()} icon={<ThumbsUp className="h-6 w-6 text-green-500" />} trend="15%" color="green-500" />
            <StatCard title="Instagram Reach" value={`${analytics.instagramLikes + analytics.instagramComments}`} icon={<Instagram className="h-6 w-6 text-pink-500" />} trend="5%" color="pink-500" />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* --- 7. UPDATED CARD STYLES AND TEXT COLORS --- */}
            <div className="bg-white/50 backdrop-blur-sm rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-serif font-bold mb-6 text-amber-900">Weekly Sales Trend</h3>
              <div className="space-y-4">
                {analytics.chartData.map((day) => (
                  <div key={day.day} className="flex items-center justify-between">
                    <span className="text-sm font-medium text-amber-800">{day.day}</span>
                    <div className="flex items-center space-x-2 flex-1 mx-4">
                      <div className="flex-1 bg-amber-200 rounded-full h-2">
                        <div className="bg-amber-500 h-2 rounded-full transition-all duration-500" style={{ width: `${(day.sales / 2000) * 100}%` }} />
                      </div>
                    </div>
                    <span className="text-sm font-bold text-amber-900">₹{day.sales}</span>
                  </div>
                ))}
              </div>
            </div>
            {/* --- 7. UPDATED CARD STYLES AND TEXT COLORS --- */}
            <div className="bg-white/50 backdrop-blur-sm rounded-2xl shadow-lg p-6">
              <h3 className="text-xl font-serif font-bold mb-6 text-amber-900">Instagram Performance</h3>
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Heart className="h-5 w-5 text-red-500" />
                    <span className="text-amber-800">Likes</span>
                  </div>
                  <span className="text-2xl font-bold text-amber-900">{analytics.instagramLikes}</span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <MessageCircle className="h-5 w-5 text-blue-500" />
                    <span className="text-amber-800">Comments</span>
                  </div>
                  <span className="text-2xl font-bold text-amber-900">{analytics.instagramComments}</span>
                </div>
                <div className="pt-4 border-t border-amber-200">
                  <p className="text-sm text-amber-700">Your Instagram posts are performing well! Keep sharing your beautiful creations.</p>
                </div>
              </div>
            </div>
          </div>

          {/* --- 7. UPDATED CARD STYLES AND TEXT COLORS --- */}
          <div className="bg-white/50 backdrop-blur-sm rounded-2xl shadow-lg p-6">
            <h3 className="text-xl font-serif font-bold mb-4 text-amber-900">Business Insights</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium text-green-600">What's Working Well</h4>
                <ul className="space-y-2 text-sm text-amber-700">
                  <li>• Your terracotta bowls are very popular</li>
                  <li>• Thursday and Friday are your best sales days</li>
                  <li>• Instagram engagement is growing steadily</li>
                </ul>
              </div>
              <div className="space-y-3">
                <h4 className="font-medium text-blue-600">Opportunities</h4>
                <ul className="space-y-2 text-sm text-amber-700">
                  <li>• Consider creating more ceramic pieces</li>
                  <li>• Weekend sales could be improved</li>
                  <li>• Video content might boost engagement</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
      <Navigation userRole="artisan" />
    </div>
  );
};

export default AnalyticsDashboardPage;