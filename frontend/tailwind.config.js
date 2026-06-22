/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bgMain: "#07090F",
        bgSurface: "#0D1117",
        borderColor: "#1C2A3A",
        brandBlue: "#2563EB",
        brandPurple: "#8B5CF6",
        brandGreen: "#10B981",
        brandAmber: "#F59E0B",
        brandRed: "#EF4444",
        brandText: "#E2EBF9",
      },
      fontFamily: {
        heading: ["'Space Grotesk'", "sans-serif"],
        body: ["Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
}
