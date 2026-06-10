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
          50: "#f5f7ef",
          100: "#e7ecd6",
          500: "#6d7f3d",
          700: "#3d4c2f",
          900: "#243126",
        },
        gold: "#b89445",
        clay: "#a45f3b",
        cream: "#fbf7ed",
      },
      boxShadow: {
        panel: "0 18px 55px rgba(28, 38, 28, 0.12)",
      },
    },
  },
  plugins: [],
};
