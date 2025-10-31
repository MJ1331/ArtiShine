import React, { useState } from 'react';
import { Sparkles, Instagram } from 'lucide-react';
import ImageUploader from '../../components/ImageUploader';
import AudioRecorder from '../../components/AudioRecorder';
import PrimaryButton from '../../components/PrimaryButton';
import Navigation from '../../components/Navigation';
import { toast, ToastContainer } from 'react-toastify';
import { useNavigate } from 'react-router-dom';

// --- 1. IMPORT THE NEW CANVAS BACKGROUND ---
import CanvasBackground from '../../components/CanvasBackground';

const UploadProductPage = () => {
  const [step, setStep] = useState(1);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageFiles, setImageFiles] = useState([]);
  const [audioFile, setAudioFile] = useState(null);
  const [generatedContent, setGeneratedContent] = useState({ title: '', tagline: '', story: '' });
  const [postToInstagram, setPostToInstagram] = useState(false);
  const navigate = useNavigate();

  // --- No changes to your functions ---
  const handleImageSelect = (files) => {
    setImageFiles(files);
    const urls = files.map((file) => URL.createObjectURL(file));
    setSelectedImages(urls);
  };

  const handleStartRecording = () => {
    setIsRecording(true);
    setRecordingDuration(0);
    const timer = setInterval(() => setRecordingDuration((prev) => prev + 1), 1000);
    setTimeout(() => {
      setIsRecording(false);
      clearInterval(timer);
      setStep(3);
      setAudioFile(new Blob([], { type: 'audio/wav' }));
    }, 5000);
  };

  const handleGenerateStory = async () => {
    setIsGenerating(true);
    await new Promise((resolve) => setTimeout(resolve, 3000));
    setGeneratedContent({
      title: 'Handcrafted Ceramic Masterpiece',
      tagline: 'Where ancient traditions meet modern beauty',
      story:
        'This beautiful ceramic piece represents hours of careful craftsmanship, shaped by hands that have learned techniques passed down through generations. Each curve and line tells a story of dedication, patience, and artistic vision.',
    });
    setIsGenerating(false);
    setStep(4);
  };

  return (
    // --- 2. ADD 'relative' TO THE MAIN WRAPPER ---
    <div className="min-h-screen pb-20 pt-20 relative">
      
      {/* --- 3. ADD THE CANVAS BACKGROUND WITH YOUR COLORS --- */}
      <CanvasBackground
        backgroundColor="#f9feffff"
        elementColors={['#ff620062', '#005cdc5a']}
      />

      <ToastContainer />
      
      {/* --- 4. ADD 'relative z-10' TO YOUR CONTENT WRAPPER --- */}
      <div className="p-6 relative z-10">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-8">
            {/* --- 5. TEXT COLORS CHANGED TO AMBER --- */}
            <h1 className="text-3xl font-serif font-bold mb-2 text-amber-900">Share Your Craft</h1>
            <p className="text-amber-700 font-semibold">Let AI help tell your story</p>
          </div>

          <div className="flex items-center justify-center mb-8 space-x-4">
            {[1, 2, 3, 4].map((stepNum) => (
              <div key={stepNum} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                    step >= stepNum
                      ? 'bg-amber-500 text-white' // Changed from bg-primary
                      : 'bg-amber-200 text-amber-700' // Changed from bg-muted
                  }`}
                >
                  {stepNum}
                </div>
                {stepNum < 4 && (
                  <div
                    className={`w-16 h-0.5 mx-2 transition-all duration-300 ${
                      step > stepNum ? 'bg-amber-500' : 'bg-amber-200' // Changed from bg-primary/bg-muted
                    }`}
                  />
                )}
              </div>
            ))}
          </div>

          {step === 1 && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-serif font-bold mb-2 text-amber-900">Step 1: Add Photos</h2>
                <p className="text-amber-700 font-semibold">Show us your beautiful creation</p>
              </div>
              <ImageUploader onImageSelect={handleImageSelect} previews={selectedImages} />
              {selectedImages.length > 0 && (
                <PrimaryButton
                  className="mt-6 w-full"
                  size="lg"
                  onClick={() => setStep(2)}
                >
                  Next
                </PrimaryButton>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl text-amber-900 font-serif font-bold mb-2">Step 2: Record Your Story</h2>
                <p className="text-amber-700 font-semibold">Tell us about your craft in your own words</p>
              </div>
              <AudioRecorder
                isRecording={isRecording}
                duration={recordingDuration}
                onStartRecording={handleStartRecording}
                onStopRecording={() => setIsRecording(false)}
                onAudioSave={(file) => setAudioFile(file)}
              />
            </div>
          )}

          {step === 3 && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl text-amber-900 font-serif font-bold mb-2">Step 3: Craft Your Story</h2>
                <p className="text-amber-700 font-semibold">Let our AI weave the magic of your story</p>
              </div>
              {/* Added bg-amber-50/50 for a slight contrast */}
              <div className="card-warm p-8 text-center bg-amber-50/50 rounded-lg"> 
                {isGenerating ? (
                  <div className="space-y-4">
                    <div className="w-16 h-16 mx-auto rounded-full bg-amber-500/20 flex items-center justify-center">
                      <Sparkles className="h-8 w-8 text-amber-500 animate-pulse" />
                    </div>
                    <h3 className="text-xl font-serif font-bold text-amber-900">Our AI is weaving the magic of your story... ✨</h3>
                    <p className="text-amber-700 font-semibold">This will take just a moment</p>
                    <div className="w-48 h-2 bg-amber-200 rounded-full mx-auto overflow-hidden">
                      <div className="h-full bg-amber-500 rounded-full animate-loading-bar"></div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <Sparkles className="h-16 w-16 mx-auto text-amber-500" />
                    <h3 className="text-xl font-serif font-bold text-amber-900">Ready to create magic?</h3>
                    <p className="text-amber-700 font-semibold">Our AI will analyze your image and audio to create a compelling story</p>
                    <PrimaryButton onClick={handleGenerateStory} size="lg" icon={<Sparkles className="h-5 w-5" />}>✨ Craft My Story</PrimaryButton>
                  </div>
                )}
              </div>
            </div>
          )}

          {step === 4 && (
            <div className="space-y-6">
              <div className="text-center mb-6">
                <h2 className="text-2xl text-amber-900 font-serif font-bold mb-2">Step 4: Review & Publish</h2>
                <p className="text-amber-700 font-semibold">Fine-tune your story and publish</p>
              </div>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm text-amber-900 font-medium mb-2">Title</label>
                  <input type="text" value={generatedContent.title} onChange={(e) => setGeneratedContent((prev) => ({ ...prev, title: e.target.value }))} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300" />
                </div>
                <div>
                  <label className="block text-sm text-amber-900 font-medium mb-2">Tagline</label>
                  <input type="text" value={generatedContent.tagline} onChange={(e) => setGeneratedContent((prev) => ({ ...prev, tagline: e.target.value }))} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300" />
                </div>
                <div>
                  <label className="block text-sm text-amber-900 font-medium mb-2">Story</label>
                  <textarea value={generatedContent.story} onChange={(e) => setGeneratedContent((prev) => ({ ...prev, story: e.target.value }))} rows={6} className="w-full px-4 py-3 rounded-lg border border-amber-300 bg-white/50 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all duration-300 resize-none" />
                </div>
                <div className="flex items-center justify-between p-4 border border-amber-300 rounded-lg bg-white/50">
                  <div className="flex items-center space-x-3">
                    <Instagram className="h-6 w-6 text-amber-600" /> 
                    <div>
                      <p className="font-medium text-amber-900">Auto-post to Instagram</p>
                      <p className="text-sm text-amber-700">Share with your followers</p>
                    </div>
                  </div>
                  <button onClick={() => setPostToInstagram(!postToInstagram)} className={`relative w-12 h-6 rounded-full transition-colors duration-300 ${postToInstagram ? 'bg-amber-500' : 'bg-amber-200'}`}>
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform duration-300 ${postToInstagram ? 'translate-x-7' : 'translate-x-1'}`} />
                  </button>
                </div>
                <PrimaryButton
                  onClick={async () => {
                    // Prepare form data
                    const formData = new FormData();
                    formData.append('title', generatedContent.title);
                    formData.append('tagline', generatedContent.tagline);
                    formData.append('story', generatedContent.story);
                    imageFiles.forEach((file, idx) => {
                      formData.append('images', file);
                    });
                    formData.append('audio', audioFile);
                    formData.append('postToInstagram', postToInstagram);
                    // TODO: Add userId/role if needed
                    // Send POST request
                    await fetch('/api/products', {
                      method: 'POST',
                      body: formData,
                    });
                    toast.success("Product published successfully!");
                    setTimeout(() => {
                      navigate("/manage-products")
                    }, 2000);
                  }}
                  size="lg"
                  className="w-full"
                >
                  Publish Product
                </PrimaryButton>
              </div>
            </div>
          )}
        </div>
      </div>
      <Navigation userRole="artisan" />
    </div>
  );
};

export default UploadProductPage;