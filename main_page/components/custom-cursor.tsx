'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';

interface Particle {
  id: number;
  x: number;
  y: number;
}

export function SmokeCursor() {
  const [cursorX, setCursorX] = useState(0);
  const [cursorY, setCursorY] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const [particles, setParticles] = useState<Particle[]>([]);
  const particleIdRef = useRef(0);

  const cursorXSpring = useSpring(cursorX, { damping: 30, mass: 1, stiffness: 100 });
  const cursorYSpring = useSpring(cursorY, { damping: 30, mass: 1, stiffness: 100 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      const x = e.clientX;
      const y = e.clientY;

      setCursorX(x);
      setCursorY(y);

      // Создавать частицы дыма при движении
      if (Math.random() > 0.7) {
        const newParticle: Particle = {
          id: particleIdRef.current++,
          x: x,
          y: y,
        };

        setParticles((prev) => [...prev, newParticle]);

        // Удалять частицу после анимации
        setTimeout(() => {
          setParticles((prev) => prev.filter((p) => p.id !== newParticle.id));
        }, 1000);
      }
    };

    const handleMouseLeave = () => {
      setIsVisible(false);
    };

    const handleMouseEnter = () => {
      setIsVisible(true);
    };

    window.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
    };
  }, []);

  // Скрыть стандартный курсор
  useEffect(() => {
    document.body.style.cursor = 'none';
    return () => {
      document.body.style.cursor = 'auto';
    };
  }, []);

  if (typeof window !== 'undefined' && ('ontouchstart' in window || navigator.maxTouchPoints > 0)) {
    return null;
  }

  return (
    <>
      {/* Частицы дыма */}
      {particles.map((particle) => (
        <motion.div
          key={particle.id}
          className="fixed top-0 left-0 pointer-events-none z-[9998]"
          initial={{ x: particle.x, y: particle.y, opacity: 0.7, scale: 1 }}
          animate={{
            x: particle.x + (Math.random() - 0.5) * 80,
            y: particle.y + (Math.random() - 0.5) * 80,
            opacity: 0,
            scale: 3,
          }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ translateX: '-50%', translateY: '-50%' }}
        >
          <div
            className="w-8 h-8 rounded-full"
            style={{
              background: 'radial-gradient(circle, rgba(160, 160, 160, 0.5) 0%, rgba(100, 100, 100, 0.2) 60%, transparent 100%)',
              filter: 'blur(12px)',
            }}
          />
        </motion.div>
      ))}

      {/* Внешнее кольцо с серым свечением */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[9999] mix-blend-screen"
        style={{
          x: cursorXSpring,
          y: cursorYSpring,
          translateX: '-50%',
          translateY: '-50%',
        }}
        animate={{
          opacity: isVisible ? 1 : 0,
        }}
        transition={{ duration: 0.2 }}
      >
        <div
          className="w-10 h-10 rounded-full"
          style={{
            border: '2px solid rgba(180, 180, 180, 0.5)',
            boxShadow: '0 0 20px rgba(180, 180, 180, 0.3), 0 0 40px rgba(150, 150, 150, 0.15), inset 0 0 20px rgba(200, 200, 200, 0.1)',
          }}
        />
      </motion.div>

      {/* Внутренняя белая точка */}
      <motion.div
        className="fixed top-0 left-0 pointer-events-none z-[9999]"
        style={{
          x: cursorX,
          y: cursorY,
          translateX: '-50%',
          translateY: '-50%',
        }}
        animate={{
          opacity: isVisible ? 1 : 0,
        }}
        transition={{ duration: 0.15 }}
      >
        <div
          className="w-2.5 h-2.5 rounded-full bg-white"
          style={{
            boxShadow: '0 0 10px rgba(255, 255, 255, 0.9)',
          }}
        />
      </motion.div>
    </>
  );
}