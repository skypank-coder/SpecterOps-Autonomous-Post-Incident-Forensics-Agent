/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "Inter", "sans-serif"],
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        ink: {
          950: "#050609",
          900: "#0a0c12",
          850: "#0e111a",
          800: "#141826",
          700: "#1b2030",
        },
        line: "#1d2234",
        brand: {
          DEFAULT: "#7c5cff",
          soft: "#9b82ff",
        },
        cyan: { DEFAULT: "#22d3ee" },
        mint: { DEFAULT: "#00f5a0" },
        rose: { DEFAULT: "#ff4d6d" },
        amber: { DEFAULT: "#f5a623" },
      },
      boxShadow: {
        glow: "0 0 40px -10px rgba(124,92,255,0.5)",
        "glow-mint": "0 0 40px -10px rgba(0,245,160,0.45)",
        card: "0 20px 60px -20px rgba(0,0,0,0.7)",
      },
      backgroundImage: {
        "grid-faint":
          "linear-gradient(to right, rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.04) 1px, transparent 1px)",
      },
      keyframes: {
        float: {
          "0%,100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-12px)" },
        },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        "pulse-ring": {
          "0%": { transform: "scale(0.8)", opacity: "0.7" },
          "100%": { transform: "scale(2.2)", opacity: "0" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        float: "float 6s ease-in-out infinite",
        shimmer: "shimmer 2s infinite",
        "pulse-ring": "pulse-ring 2.4s ease-out infinite",
        marquee: "marquee 28s linear infinite",
      },
    },
  },
  plugins: [],
};
