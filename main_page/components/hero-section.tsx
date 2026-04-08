"use client";

import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect, useRef } from "react";
import Image from "next/image";
import { SearchBubble } from "./search-bubble";
import { SmokeCursor } from "./custom-cursor";

export function HeroSection() {
  const containerRef = useRef<HTMLDivElement>(null);

  // Mouse position tracking
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Spring animation for smooth parallax
  const springConfig = { stiffness: 80, damping: 25 };
  const mouseXSpring = useSpring(mouseX, springConfig);
  const mouseYSpring = useSpring(mouseY, springConfig);

  // Transform mouse position to parallax offset (max 30px)
  const imageX = useTransform(mouseXSpring, [-1, 1], [-30, 30]);
  const imageY = useTransform(mouseYSpring, [-1, 1], [-25, 25]);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;

      const rect = containerRef.current.getBoundingClientRect();
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;

      // Normalize to -1 to 1 range
      const normalizedX = (e.clientX - centerX) / (rect.width / 2);
      const normalizedY = (e.clientY - centerY) / (rect.height / 2);

      mouseX.set(Math.max(-1, Math.min(1, normalizedX)));
      mouseY.set(Math.max(-1, Math.min(1, normalizedY)));
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, [mouseX, mouseY]);

  return (
    <div
      ref={containerRef}
      className="relative w-full h-screen overflow-hidden cursor-none"
      style={{
        backgroundColor: "#0a1628",
      }}
    >
      {/* Custom Cursor */}
      <SmokeCursor />

      {/* ═══════════════════════════════════════════════════════════
          СЛОЙ 1: СТАТИЧНЫЙ ФОН (z-index: 0)
          - НЕ двигается при перемещении курсора
          ═══════════════════════════════════════════════════════════ */}
      <div className="absolute inset-0 z-0">
        <Image
          src="/images/background-room.jpg"
          alt="Фон - темная комната с синим освещением"
          fill
          className="object-cover object-center"
          priority
          sizes="100vw"
        />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          СЛОЙ 2: ПОИСКОВЫЕ ПУЗЫРИ (z-index: 10)
          ═══════════════════════════════════════════════════════════ */}
      <div className="hidden md:block z-10">
        {/* "страхование дорого телефона копить" - Top left */}
        <div className="absolute top-[8%] left-[10%]">
          <SearchBubble text="страхование дорого телефона копить" />
        </div>

        {/* "как застраховать новый велосипед" - Right side, middle-upper */}
        <div className="absolute top-[24%] right-[8%]">
          <SearchBubble text="как застраховать новый велосипед" />
        </div>

        {/* "страховой случай это" - Left side, middle */}
        <div className="absolute top-[45%] left-[15%]">
          <SearchBubble text="страховой случай это" />
        </div>
      </div>

      {/* Search bubbles - Mobile layout */}
      <div className="md:hidden absolute bottom-8 left-0 right-0 flex flex-col items-center gap-3 px-4 z-10">
        <SearchBubble text="страхование дорого телефона копить" />
        <SearchBubble text="как застраховать новый велосипед" />
        <SearchBubble text="страховой случай это" />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          СЛОЙ 3: "ПОДРОСТОК ГЛАВНЫЙ" (z-index: 20)
          - ТОЛЬКО этот слой двигается с параллаксом
          - Перекрывает поисковые пузыри
          - Размер: max-w-7xl (1280px), высота 100%
          ═══════════════════════════════════════════════════════════ */}
      <motion.div
        className="absolute inset-0 z-20 pointer-events-none"
        style={{
          x: imageX,
          y: imageY,
        }}
      >
        <div className="relative w-full h-full flex items-end justify-center">
          {/* Изменить размер: max-w-5xl=1024px, max-w-6xl=1152px, max-w-7xl=1280px, max-w-full=100% */}
          <div className="relative w-full max-w-7xl h-full">
            <Image
              src="/images/teenager-main.png"
              alt="Подросток главный - смотрит в телефон"
              fill
              className="object-contain object-bottom"
              priority
              sizes="(max-width: 768px) 100vw, 1280px"
            />
          </div>
        </div>
      </motion.div>
    </div>
  );
}
