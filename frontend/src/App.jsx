import Navbar from "./components/Navbar.jsx";
import Hero from "./components/Hero.jsx";
import LogoCloud from "./components/LogoCloud.jsx";
import Problem from "./components/Problem.jsx";
import HowItWorks from "./components/HowItWorks.jsx";
import LiveDemo from "./components/demo/LiveDemo.jsx";
import Features from "./components/Features.jsx";
import Metrics from "./components/Metrics.jsx";
import TechStack from "./components/TechStack.jsx";
import CTA from "./components/CTA.jsx";
import Footer from "./components/Footer.jsx";

export default function App() {
  return (
    <div className="relative min-h-screen bg-ink-950 text-zinc-200">
      <Navbar />
      <main>
        <Hero />
        <LogoCloud />
        <Problem />
        <HowItWorks />
        <LiveDemo />
        <Features />
        <Metrics />
        <TechStack />
        <CTA />
      </main>
      <Footer />
    </div>
  );
}
