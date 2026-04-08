import { HeroSection } from "@/components/hero-section";
import { TransitionSection } from "@/components/transition-section";
import { MotivationSection } from "@/components/motivation-section";

export default function Home() {
  return (
    <main className="relative">
      {/* Экран 1: Hero с подростком */}
      <HeroSection />
      
      {/* Экран 2: Переходный экран */}
      <TransitionSection />
      
      {/* Экран 3: Мотивация */}
      <MotivationSection />
    </main>
  );
}
