/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Prompt", "sans-serif"]
      },
      colors: {
        ink: "#111111",
        paper: "#f5f5f2",
        line: "#d7d7d1"
      },
      boxShadow: {
        frame: "0 12px 40px rgba(0, 0, 0, 0.16)"
      }
    }
  },
  plugins: []
};
