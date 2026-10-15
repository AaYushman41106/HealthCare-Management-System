/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          navy: "#102A43",
          darkNavy: "#0B1F33",
          teal: "#0F9D92",
          paleTeal: "#E7F7F5",
          bg: "#F8FAFC",
          card: "#FFFFFF",
          border: "#E2E8F0",
        }
      }
    },
  },
  plugins: [],
}
