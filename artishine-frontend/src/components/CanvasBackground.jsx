// src/components/CanvasBackground.jsx

import React, { useRef, useEffect } from 'react';
import './CanvasBackground.css'; // We will create this next

const CanvasBackground = ({ backgroundColor, elementColors }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    const resize = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };
    window.addEventListener('resize', resize);
    resize();

    const elements = [];
    const presets = {};

    presets.o = function (x, y, s, dx, dy, color) {
      return {
        x: x, y: y, r: 12 * s, w: 5 * s, dx: dx, dy: dy, color: color,
        draw: function (ctx, t) {
          this.x += this.dx;
          this.y += this.dy;
          ctx.beginPath();
          ctx.arc(this.x + +Math.sin((50 + x + (t / 10)) / 100) * 3, this.y + +Math.sin((45 + x + (t / 10)) / 100) * 4, this.r, 0, 2 * Math.PI, false);
          ctx.lineWidth = this.w;
          ctx.strokeStyle = this.color;
          ctx.stroke();
        },
      };
    };

    presets.x = function (x, y, s, dx, dy, dr, r, color) {
      r = r || 0;
      return {
        x: x, y: y, s: 20 * s, w: 5 * s, r: r, dx: dx, dy: dy, dr: dr, color: color,
        draw: function (ctx, t) {
          this.x += this.dx;
          this.y += this.dy;
          this.r += this.dr;
          
          const _this = this;
          const line = (x, y, tx, ty, c, o) => {
            o = o || 0;
            ctx.beginPath();
            ctx.moveTo(-o + ((_this.s / 2) * x), o + ((_this.s / 2) * y));
            ctx.lineTo(-o + ((_this.s / 2) * tx), o + ((_this.s / 2) * ty));
            ctx.lineWidth = _this.w;
            ctx.strokeStyle = c;
            ctx.stroke();
          };

          ctx.save();
          ctx.translate(this.x + Math.sin((x + (t / 10)) / 100) * 5, this.y + Math.sin((10 + x + (t / 10)) / 100) * 2);
          ctx.rotate((this.r * Math.PI) / 180);
          line(-1, -1, 1, 1, this.color);
          line(1, -1, -1, 1, this.color);
          ctx.restore();
        },
      };
    };

    // Populate elements
    if (canvas.width > 0 && canvas.height > 0) {
      for (let x = 0; x < canvas.width; x++) {
        for (let y = 0; y < canvas.height; y++) {
          if (Math.round(Math.random() * 8000) === 1) {
            const s = (Math.random() * 5 + 1) / 10;
            const color = elementColors[Math.floor(Math.random() * elementColors.length)];
            if (Math.round(Math.random()) === 1)
              elements.push(presets.o(x, y, s, 0, 0, color));
            else
              elements.push(presets.x(x, y, s, 0, 0, (Math.random() * 3 - 1) / 10, Math.random() * 360, color));
          }
        }
      }
    }

    // Animation loop
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const time = new Date().getTime();
      for (let e in elements) {
        elements[e].draw(ctx, time);
      }
      animationFrameId = requestAnimationFrame(animate);
    };
    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [backgroundColor, elementColors]); // Re-run if colors change

  return <canvas ref={canvasRef} id="canvas-background" />;
};

export default CanvasBackground;