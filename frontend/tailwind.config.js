/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          navy: '#0f2240',
          dark: '#1e293b',
          surface: '#f8fafc',
          card: '#ffffff',
          border: '#e2e8f0',
          teal: '#007299',
          tealHover: '#005a7a',
          pass: '#16a34a',
          passLight: '#f0fdf4',
          warn: '#d97706',
          warnLight: '#fffbeb',
          fail: '#dc2626',
          failLight: '#fef2f2',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      }
    },
  },
  plugins: [],
}
