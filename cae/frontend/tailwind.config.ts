import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0D1117',
          800: '#161B22',
          700: '#1C2128',
          600: '#21262D',
          border: '#30363D',
        },
        gold: {
          DEFAULT: '#C8A951',
          light: '#E3C97A',
          dark: '#A08838',
        },
        risk: {
          critical: '#DC2626',
          high: '#EA580C',
          moderate: '#D97706',
          low: '#16A34A',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};

export default config;
