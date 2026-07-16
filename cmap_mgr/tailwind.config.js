/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      // custom colors
      colors: {},
      boxShadow: {
        custom:
          "0 0px 15px -3px rgb(0 0 0 / 11%), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
      },
      backgroundImage: {},
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
