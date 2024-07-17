/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./apps/**/index.html",
    "./apps/**/*.{js,ts,jsx,tsx}",
    "./common/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    colors: {
      transparent: 'transparent',
      "whitesmoke": "#F5F5F5",
      "red": "#B22222",
      //hsl(120, 61%, 26%)
      "green": "#1a6a1a",
      "gray-dark": "hsl(120, 51%, 10%)",
      "gray-med": "hsl(120, 11%, 50%)",
      "gray-panel-bg": "hsl(120, 5%, 83%)",
      "blue": "#4682B4",
      "gold": "#FFD700"

    },
    extend: {},
  },
  plugins: [],
}

