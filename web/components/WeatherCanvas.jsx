'use client';

import React, { useEffect, useRef } from 'react';

export default function WeatherCanvas({ weatherTheme = 'clear', isDay = 1 }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Particle sets
    const raindrops = Array.from({ length: 90 }, () => ({
      x: Math.random() * (width + 100),
      y: Math.random() * height,
      len: Math.random() * 16 + 12,
      speed: Math.random() * 10 + 14,
      slant: Math.random() * 2 + 2,
      color: 'rgba(125, 211, 252, 0.65)'
    }));

    const splashes = [];

    const snowflakes = Array.from({ length: 70 }, () => ({
      x: Math.random() * width,
      baseX: Math.random() * width,
      y: Math.random() * height,
      r: Math.random() * 3 + 1.5,
      speed: Math.random() * 1.5 + 0.8,
      driftAngle: Math.random() * Math.PI * 2,
      driftSpeed: Math.random() * 0.02 + 0.01,
      amp: Math.random() * 25 + 10
    }));

    const stars = Array.from({ length: 65 }, () => ({
      x: Math.random() * width,
      y: Math.random() * (height * 0.55),
      r: Math.random() * 1.8 + 0.8,
      alpha: Math.random() * 0.7 + 0.3,
      pulseSpeed: Math.random() * 0.03 + 0.015,
      pulseAngle: Math.random() * Math.PI * 2
    }));

    const fogBands = Array.from({ length: 5 }, (_, i) => ({
      x: Math.random() * width - width * 0.3,
      y: (height * 0.3) + i * (height * 0.12),
      w: width * 1.6,
      h: height * 0.18,
      speed: Math.random() * 0.3 + 0.15,
      alpha: Math.random() * 0.06 + 0.03
    }));

    let lightningFlash = 0;
    let lightningBolt = null;

    const createLightningBolt = () => {
      const startX = width * (0.2 + Math.random() * 0.6);
      let currX = startX;
      let currY = 0;
      const points = [[currX, currY]];
      const segments = Math.floor(Math.random() * 6) + 8;
      const stepY = (height * 0.7) / segments;

      for (let i = 0; i < segments; i++) {
        currX += (Math.random() - 0.5) * 60;
        currY += stepY;
        points.push([currX, currY]);
      }
      return points;
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // 1. Rain with ground splash ripples
      if (weatherTheme === 'rain' || weatherTheme === 'thunderstorm') {
        ctx.lineWidth = 1.5;
        for (let i = 0; i < raindrops.length; i++) {
          const p = raindrops[i];
          p.y += p.speed;
          p.x -= p.slant;

          if (p.y > height - 10) {
            if (splashes.length < 35 && Math.random() < 0.5) {
              splashes.push({
                x: p.x,
                y: height - Math.random() * 18,
                r: 1,
                maxR: Math.random() * 7 + 4,
                life: 1.0
              });
            }
            p.y = -20;
            p.x = Math.random() * (width + 100);
          }

          ctx.strokeStyle = p.color;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(p.x - p.slant, p.y + p.len);
          ctx.stroke();
        }

        // Render Splashes
        for (let i = splashes.length - 1; i >= 0; i--) {
          const s = splashes[i];
          s.r += (s.maxR - s.r) * 0.25;
          s.life -= 0.06;

          if (s.life <= 0) {
            splashes.splice(i, 1);
            continue;
          }

          ctx.strokeStyle = `rgba(186, 230, 253, ${s.life * 0.5})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.ellipse(s.x, s.y, s.r * 1.6, s.r * 0.5, 0, 0, Math.PI * 2);
          ctx.stroke();
        }
      }

      // 2. Thunderstorm Lightning
      if (weatherTheme === 'thunderstorm') {
        if (Math.random() < 0.012 && lightningFlash === 0) {
          lightningFlash = 4;
          lightningBolt = createLightningBolt();
        }

        if (lightningFlash > 0) {
          ctx.fillStyle = `rgba(255, 255, 255, ${lightningFlash >= 3 ? 0.25 : 0.12})`;
          ctx.fillRect(0, 0, width, height);
          lightningFlash--;

          if (lightningBolt && lightningBolt.length > 1) {
            ctx.shadowColor = '#38bdf8';
            ctx.shadowBlur = 15;
            ctx.strokeStyle = '#ffffff';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.moveTo(lightningBolt[0][0], lightningBolt[0][1]);
            for (let i = 1; i < lightningBolt.length; i++) {
              ctx.lineTo(lightningBolt[i][0], lightningBolt[i][1]);
            }
            ctx.stroke();
            ctx.shadowBlur = 0;
          }
        } else {
          lightningBolt = null;
        }
      }

      // 3. Snow Flurries
      if (weatherTheme === 'snow') {
        ctx.fillStyle = 'rgba(241, 245, 249, 0.85)';
        for (let i = 0; i < snowflakes.length; i++) {
          const s = snowflakes[i];
          s.y += s.speed;
          s.driftAngle += s.driftSpeed;
          s.x = s.baseX + Math.sin(s.driftAngle) * s.amp;

          if (s.y > height + 10) {
            s.y = -10;
            s.baseX = Math.random() * width;
          }

          ctx.beginPath();
          ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 4. Fog / Mist Bands
      if (weatherTheme === 'fog') {
        for (let i = 0; i < fogBands.length; i++) {
          const f = fogBands[i];
          f.x += f.speed;
          if (f.x > width) f.x = -f.w * 0.7;

          const grad = ctx.createLinearGradient(f.x, f.y, f.x + f.w, f.y + f.h);
          grad.addColorStop(0, 'rgba(226, 232, 240, 0)');
          grad.addColorStop(0.5, `rgba(241, 245, 249, ${f.alpha})`);
          grad.addColorStop(1, 'rgba(226, 232, 240, 0)');

          ctx.fillStyle = grad;
          ctx.fillRect(f.x, f.y, f.w, f.h);
        }
      }

      // 5. Starfield (for Night mode)
      if (!isDay && (weatherTheme === 'clear' || weatherTheme === 'cloudy')) {
        for (let i = 0; i < stars.length; i++) {
          const st = stars[i];
          st.pulseAngle += st.pulseSpeed;
          const alpha = 0.3 + 0.6 * Math.sin(st.pulseAngle);

          ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0.1, alpha)})`;
          ctx.beginPath();
          ctx.arc(st.x, st.y, st.r, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, [weatherTheme, isDay]);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 transition-opacity duration-1000"
      aria-hidden="true"
    />
  );
}
