/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        body: ["Manrope", "Segoe UI", "sans-serif"],
      },
      colors: {
        olive: {
          50: "#f4f6ee",
          100: "#e5ead6",
          200: "#cdd6b4",
          400: "#8a9a5b",
          500: "#6d7f3d",
          700: "#3d4c2f",
          800: "#2b3a26",
          900: "#1f2e1f",
        },
        gold: {
          DEFAULT: "#b89445",
          light: "#d4b56a",
        },
        clay: "#a45f3b",
        cream: "#f7f4ec",
      },
      boxShadow: {
        card: "0 1px 3px rgba(31, 46, 31, 0.08), 0 1px 2px rgba(31, 46, 31, 0.04)",
        sheet: "0 -12px 40px rgba(31, 46, 31, 0.18)",
        bar: "0 -4px 24px rgba(31, 46, 31, 0.14)",
      },
      keyframes: {
        "slide-up": {
          from: { transform: "translateY(100%)" },
          to: { transform: "translateY(0)" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      animation: {
        "slide-up": "slide-up 0.28s cubic-bezier(0.32, 0.72, 0, 1)",
        "fade-in": "fade-in 0.2s ease-out",
      },
    },
  },
  plugins: [],
};
