/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        teal: { DEFAULT: "#20B2AA", bright: "#17c7ba", deep: "#1a9d96" },
        ink: { 900: "#0B1A1C", 800: "#0D1F21", 700: "#11282a", 600: "#132C30" },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "Roboto", "Inter", "sans-serif"],
      },
      keyframes: {
        fadeUp: { "0%": { opacity: 0, transform: "translateY(8px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        blink: { "0%,100%": { opacity: 1 }, "50%": { opacity: 0 } },
      },
      animation: { fadeUp: "fadeUp .35s ease both", blink: "blink 1s step-end infinite" },
    },
  },
  plugins: [],
};
