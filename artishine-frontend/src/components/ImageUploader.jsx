import React, { useRef, useState } from 'react';
import { Camera } from 'lucide-react';
import PrimaryButton from './PrimaryButton';

const ImageUploader = ({ onImageSelect, previews }) => {
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length && onImageSelect) onImageSelect(files);
  };

  const handleButtonClick = () => {
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length && onImageSelect) onImageSelect(files);
  };

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 ${
        dragActive ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'
      }`}
      onDragEnter={() => setDragActive(true)}
      onDragLeave={() => setDragActive(false)}
      onDragOver={(e) => e.preventDefault()}
      onDrop={handleDrop}
    >
      <input
        type="file"
        accept="image/*"
        multiple
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />
      {previews && previews.length > 0 ? (
        <div className="space-y-4">
          <div className="flex flex-wrap gap-4 justify-center">
            {previews.map((url, idx) => (
              <img key={idx} src={url} alt={`Preview ${idx + 1}`} className="max-h-48 rounded-lg shadow-warm" />
            ))}
          </div>
          <p className="text-muted-foreground">Images uploaded successfully!</p>
        </div>
      ) : (
        <div className="space-y-4">
          <Camera className="mx-auto h-12 w-12 text-muted-foreground" />
          <div>
            <p className="text-lg font-semibold font-medium">Upload your craft images</p>
            <p className="text-muted-foreground font-semibold">Drag and drop or click to select (multiple allowed)</p>
          </div>
          <PrimaryButton variant="outline" onClick={handleButtonClick}>
            <Camera className="mr-2 h-4 w-4" />
            Choose Images
          </PrimaryButton>
        </div>
      )}
    </div>
  );
};

export default ImageUploader;


