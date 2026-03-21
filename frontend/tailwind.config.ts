import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        latte: "#1A130D",
        parchment: "#E8D39B",
        tea: {
          900: "#090806",
          700: "#4E6B28",
          500: "#9BC53D",
          200: "#DCC483",
          100: "#EEDAA5",
        },
        bark: {
          700: "#8F6422",
          500: "#D9A640",
          100: "#F0CF82",
        },
        fog: "#65584A",
      },
      fontFamily: {
        sans: ["Manrope", "sans-serif"],
        display: ["Cormorant Garamond", "serif"],
      },
      boxShadow: {
        card: "0 20px 56px rgba(0, 0, 0, 0.28)",
        soft: "0 14px 32px rgba(9, 8, 6, 0.16)",
      },
      borderRadius: {
        "4xl": "2rem",
      },
      backgroundImage: {
        "paper-glow":
          "radial-gradient(circle at top left, rgba(212, 166, 64, 0.28), rgba(212, 166, 64, 0) 34%), radial-gradient(circle at top right, rgba(155, 197, 61, 0.12), rgba(155, 197, 61, 0) 24%), radial-gradient(circle at bottom center, rgba(240, 207, 130, 0.14), rgba(240, 207, 130, 0) 34%), linear-gradient(180deg, #110c08 0%, #1a120b 42%, #24180e 100%)",
      },
      keyframes: {
        floatIn: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "0.75" },
          "50%": { opacity: "1" },
        },
      },
      animation: {
        "float-in": "floatIn 0.45s ease-out",
        "pulse-soft": "pulseSoft 1.5s ease-in-out infinite",
      },
    },
  },
  plugins: [],
} satisfies Config;
