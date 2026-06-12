/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: { DEFAULT: "#0D1F21", 2: "#11282A", 3: "#162F32" },
        accent: { DEFAULT: "#20B2AA", 2: "#2DD4BF", dim: "rgba(32,178,170,0.15)" },
        fg: { DEFAULT: "#FFFFFF", 2: "#A0AEB0", 3: "#607274" },
        brd: "rgba(32,178,170,0.2)",
        ok: "#22C55E",
        warn: "#EAB308",
        err: "#EF4444",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
        mono: ["'SF Mono'", "Monaco", "Menlo", "monospace"],
      },
      boxShadow: {
        glass: "0 4px 24px 0 rgba(32,178,170,0.08), 0 1px 0 rgba(32,178,170,0.15) inset",
      },
      backdropBlur: { xs: "4px" },
    },
  },
  plugins: [],
};
