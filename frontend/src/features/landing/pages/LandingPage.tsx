import { HeroSection } from "../components/HeroSection";
import { FeaturesSection } from "../components/FeaturesSection";
import { ArchitectureSection } from "../components/ArchitectureSection";
import { CtaSection } from "../components/CtaSection";
export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-24 pb-20">
      <HeroSection />
      <FeaturesSection />
      <ArchitectureSection />
      <CtaSection />
    </div>
  );
};

export default LandingPage;
