/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          blue:      "#1B3A6B",
          blueDark:  "#112544",
          blueLight: "#2A5298",
          gold:      "#C9A84C",
          goldLight: "#E8C96A",
          goldDark:  "#A8873C",
        },
        surface: {
          dark:   "#0F1923",
          card:   "#162030",
          border: "#1E2D42",
          hover:  "#1A2A3E",
        },
        status: {
          green:  "#22C55E",
          yellow: "#F59E0B",
          red:    "#EF4444",
          blue:   "#3B82F6",
        },
      },
      fontFamily: {
        arabic: ["Tajawal", "sans-serif"],
        latin:  ["Inter", "sans-serif"],
      },
      borderRadius: {
        xl2: "1rem",
        xl3: "1.5rem",
      },
    },
  },
  plugins: [],
};
