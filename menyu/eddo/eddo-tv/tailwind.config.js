/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Fredoka', 'Nunito', 'system-ui', 'sans-serif'],
        body: ['Nunito', 'system-ui', 'sans-serif'],
      },
      colors: {
        // Eddo vivid royal purple (from the real menus)
        eddo: {
          950: '#2c0556',
          900: '#3a0a72',
          800: '#4b139b',  // base background
          700: '#5d1fbc',
          600: '#7a32d6',
          500: '#9a52e6',
        },
        ink: '#2c0a52',      // headings on white cards
        inksoft: '#7a5aa6',  // muted subtitles (russian, sizes)
        gold: {
          400: '#ffd60a',
          500: '#ffc400',
          600: '#f5a300',
        },
      },
    },
  },
  plugins: [],
}
