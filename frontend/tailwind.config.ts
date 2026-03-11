import type { Config } from "tailwindcss";
import tailwindcssAnimate from "tailwindcss-animate";

const config: Config = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        screen: "#070b14",
        surface: "#0d1726",
        "surface-raised": "#112035",
        border: "#1e2d45",
        "text-primary": "#e2e8f0",
        "text-muted": "#64748b",
        "text-dim": "#334155",
        "accent-cyan": "#00d4ff",
        "accent-amber": "#f59e0b",
        "accent-green": "#34d399",
        "accent-red": "#ef4444",
      },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Cascadia Code",
          "monospace",
        ],
      },
      borderRadius: {
        DEFAULT: "6px",
      },
    },
  },
  plugins: [tailwindcssAnimate],
};

export default config;
