import React from 'react';
import './AnimatedBackground.css'; // We will create this file next

const AnimatedBackground = () => {
  return (
    <>
      {/* This is the main background element */}
      <section className="bg-container">
        <div className="bg-wrap">
          <div className="bg-pattern"></div>
        </div>
      </section>

      {/* This is the credit link */}
      <div className="bg-credit">
        
        <a href="http://thepatternlibrary.com/#alchemy" target="_blank" rel="noopener noreferrer">
          
        </a>
      </div>
    </>
  );
};

export default AnimatedBackground;