/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f6ff',
          100: '#e0edff',
          500: '#2563eb',
          600: '#1d4ed8',
          700: '#1e40af',
          900: '#1e3a8a',
        },
        dark: {
          bg: '#0b0f17',
          card: '#131b2e',
          border: '#1e293b',
          sidebar: '#0f172a'
        }
      }
    },
  },
  plugins: [],
}
