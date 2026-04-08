"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";

interface MotivationSectionProps {
  onStartGuide?: () => void;
}

export function MotivationSection({ onStartGuide }: MotivationSectionProps) {
  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: "-10%" });

  // Lines that appear one by one
  const firstBlock = [
    "Это про ситуации, когда что-то пошло не так.",
    "Разбитый телефон. Потерянные деньги. Неожиданные расходы.",
    "Большинство подростков думают: «со мной такого не случится».",
  ];

  const pauseText = "Давай проверим.";

  const secondBlock = [
    "Мы создали интерактивный гайд, где ты проживёшь 1 год своей жизни.",
    "С твоими привычками.",
    "С твоими устройствами.",
    "С твоими решениями.",
  ];

  const keyMotivation =
    "Чтобы ты увидел, сколько это реально может стоить — до того, как это случится в жизни.";

  return (
    <section
      ref={sectionRef}
      className="relative min-h-screen flex items-center justify-center px-6 py-24"
      style={{ backgroundColor: "#050d1a" }}
    >
      <div className="max-w-3xl mx-auto">
        {/* Main heading */}
        <motion.h2
          className="text-3xl md:text-5xl lg:text-6xl font-bold text-white mb-12 text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 0.2 }}
        >
          Страхование — это не про бумажки
        </motion.h2>

        {/* First block of lines */}
        <div className="space-y-4 mb-10">
          {firstBlock.map((line, index) => (
            <motion.p
              key={index}
              className="text-lg md:text-xl text-white/70 text-center"
              initial={{ opacity: 0, x: -20 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.6, delay: 0.6 + index * 0.4 }}
            >
              {line}
            </motion.p>
          ))}
        </div>

        {/* Pause text - highlighted */}
        <motion.p
          className="text-2xl md:text-3xl font-semibold text-cyan-400 text-center my-12"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={isInView ? { opacity: 1, scale: 1 } : {}}
          transition={{ duration: 0.8, delay: 2.2 }}
        >
          {pauseText}
        </motion.p>

        {/* Second block of lines */}
        <div className="space-y-3 mb-10">
          {secondBlock.map((line, index) => (
            <motion.p
              key={index}
              className="text-lg md:text-xl text-white/60 text-center"
              initial={{ opacity: 0, x: 20 }}
              animate={isInView ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.6, delay: 3.0 + index * 0.35 }}
            >
              {line}
            </motion.p>
          ))}
        </div>

        {/* Key motivation - highlighted box */}
        <motion.div
          className="relative my-14 p-8 rounded-2xl"
          style={{
            background: "linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(59, 130, 246, 0.1) 100%)",
            border: "1px solid rgba(6, 182, 212, 0.3)",
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.8, delay: 4.5 }}
        >
          <p className="text-xl md:text-2xl text-white font-medium text-center leading-relaxed">
            {keyMotivation}
          </p>
        </motion.div>

        {/* CTA Button */}
        <motion.div
          className="flex justify-center"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6, delay: 5.2 }}
        >
          <motion.button
            onClick={onStartGuide}
            className="relative px-12 py-5 text-xl font-semibold text-white rounded-full overflow-hidden"
            style={{
              background: "linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)",
            }}
            whileHover={{ scale: 1.05, boxShadow: "0 0 40px rgba(6, 182, 212, 0.5)" }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Shimmer effect */}
            <motion.span
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
              initial={{ x: "-100%" }}
              animate={{ x: "200%" }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            />
            <span className="relative z-10">Пройти гайд</span>
          </motion.button>
        </motion.div>
      </div>

      {/* Background decorative elements */}
      <div className="absolute top-20 left-1/4 w-2 h-2 bg-cyan-400/50 rounded-full" />
      <div className="absolute top-40 right-1/3 w-1.5 h-1.5 bg-blue-400/50 rounded-full" />
      <div className="absolute bottom-32 left-1/3 w-2.5 h-2.5 bg-cyan-400/30 rounded-full" />
      <div className="absolute bottom-20 right-1/4 w-2 h-2 bg-blue-400/40 rounded-full" />
    </section>
  );
}
