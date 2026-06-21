import { Navbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { LogoCloud } from "@/components/landing/LogoCloud";
import { Workflow } from "@/components/landing/Workflow";
import { AnalysisShowcase } from "@/components/landing/AnalysisShowcase";
import { Features } from "@/components/landing/Features";
import { StatsBand } from "@/components/landing/StatsBand";
import { CTA } from "@/components/landing/CTA";
import { Footer } from "@/components/landing/Footer";

export function LandingPage() {
  return (
    <div className="relative min-h-screen bg-base text-ink">
      <Navbar />
      <main>
        <Hero />
        <LogoCloud />
        <Workflow />
        <AnalysisShowcase />
        <Features />
        <StatsBand />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
