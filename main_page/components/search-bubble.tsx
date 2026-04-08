"use client";

import { motion } from "framer-motion";
import { useState, useRef } from "react";
import { Search } from "lucide-react";

interface SearchBubbleProps {
  text: string;
  className?: string;
  style?: React.CSSProperties;
}

export function SearchBubble({ text, className = "", style }: SearchBubbleProps) {
  const [isHovered, setIsHovered] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  return (
    <motion.button
      ref={buttonRef}
      className={`group relative flex items-center gap-3 px-5 py-3.5 rounded-full cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-400 focus-visible:ring-offset-2 focus-visible:ring-offset-[#0a1628] ${className}`}
      style={{
        ...style,
        transformOrigin: "center bottom",
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onFocus={() => setIsHovered(true)}
      onBlur={() => setIsHovered(false)}
      aria-label={`Поиск: ${text}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ 
        opacity: 1, 
        y: isHovered ? -10 : 0,
        scaleY: isHovered ? 1.08 : 1,
      }}
      transition={{
        opacity: { duration: 0.5, delay: 0.2 },
        y: {
          type: "spring",
          stiffness: 120,
          damping: 15,
          mass: 0.8,
        },
        scaleY: {
          type: "spring",
          stiffness: 120,
          damping: 15,
          mass: 0.8,
        },
      }}
      whileTap={{ scale: 0.98 }}
    >
      {/* White pill background - matching Figma exactly */}
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          background: "#ffffff",
        }}
        animate={{
          boxShadow: isHovered
            ? "0 8px 32px rgba(0, 0, 0, 0.25), 0 0 20px 2px rgba(0, 240, 255, 0.3)"
            : "0 4px 20px rgba(0, 0, 0, 0.15)",
        }}
        transition={{
          duration: 0.45,
          ease: [0.23, 1, 0.32, 1],
        }}
      />

      {/* Border glow on hover */}
      <motion.div
        className="absolute inset-0 rounded-full pointer-events-none"
        animate={{
          boxShadow: isHovered
            ? "inset 0 0 0 2px rgba(0, 240, 255, 0.5)"
            : "inset 0 0 0 0px transparent",
        }}
        transition={{
          duration: 0.45,
          ease: [0.23, 1, 0.32, 1],
        }}
      />

      {/* Search icon - gray color matching Figma */}
      <motion.div
        className="relative z-10"
        animate={{
          color: isHovered ? "#00c8d4" : "#9ca3af",
        }}
        transition={{ duration: 0.3 }}
      >
        <Search className="w-5 h-5" strokeWidth={2} />
      </motion.div>

      {/* Text with shimmer effect */}
      <span className="relative z-10 text-base font-normal overflow-hidden whitespace-nowrap">
        <motion.span 
          className="relative inline-block"
          animate={{
            color: isHovered ? "#0a1628" : "#1f2937",
          }}
          transition={{ duration: 0.3 }}
        >
          {text}
          {/* Shimmer overlay */}
          <motion.span
            className="absolute inset-0 pointer-events-none"
            style={{
              background: "linear-gradient(90deg, transparent 0%, transparent 20%, #00f0ff 40%, white 50%, #00f0ff 60%, transparent 80%, transparent 100%)",
              backgroundSize: "200% 100%",
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
              color: "transparent",
              mixBlendMode: "overlay",
            }}
            initial={{ backgroundPosition: "200% 0" }}
            animate={{
              backgroundPosition: isHovered ? "-200% 0" : "200% 0",
            }}
            transition={{
              duration: 0.8,
              ease: "linear",
            }}
          >
            {text}
          </motion.span>
        </motion.span>
      </span>
    </motion.button>
  );
}
