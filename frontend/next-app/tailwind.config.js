/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./pages/**/*.{js,jsx}', './components/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        surface: { DEFAULT: '#0f0f1e', 2: '#13132a', 3: '#1a1a30' },
        border: { DEFAULT: '#1e1e3a', active: '#7c3aed33' },
        accent: { DEFAULT: '#a78bfa', dark: '#7c3aed', light: '#c4b5fd' },
        success: '#22c55e',
        warning: '#f59e0b',
        danger: '#ef4444',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
}
