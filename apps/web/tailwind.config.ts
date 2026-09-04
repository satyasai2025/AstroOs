import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // AstroOS Research Workstation Theme — deep navy + instrument teal + gold + violet
        cosmos: {
          50:  "#f0f4ff",
          100: "#dde6ff",
          200: "#c3d0ff",
          300: "#9db0ff",
          400: "#7585ff",
          500: "#4f5bfa",
          600: "#3a3def",
          700: "#2f2fd6",
          800: "#1e1e8a",
          900: "#0d0d3d",
          950: "#060620",
        },
        amber: {
          300: "#fcd34d",
          400: "#fbbf24",
          500: "#f59e0b",
          600: "#d97706",
        },
        saffron: "#ff9933",
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "monospace"],
        vedic: ["var(--font-noto-serif)", "Georgia", "serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in-out",
        "slide-up": "slideUp 0.4s ease-out",
        "spin-slow": "spin 8s linear infinite",
        "pulse-amber": "pulseAmber 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
        pulseAmber: {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(251,191,36,0.4)" },
          "50%": { boxShadow: "0 0 0 8px rgba(251,191,36,0)" },
        },
      },
      backgroundImage: {
        "cosmos-gradient":
          "radial-gradient(ellipse at top, #1e1e8a 0%, #060620 70%)",
        "card-glass":
          "linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
