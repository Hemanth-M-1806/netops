/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['IBM Plex Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        // Network status semantic colors
        network: {
          healthy:   '#22c55e',
          warning:   '#f59e0b',
          critical:  '#ef4444',
          info:      '#3b82f6',
          down:      '#6b7280',
        },
        // Base dark technical palette
        surface: {
          950: '#050709',
          900: '#090c10',
          850: '#0d1117',
          800: '#111827',
          750: '#161d2b',
          700: '#1c2433',
          600: '#232d3f',
          500: '#2a3649',
          400: '#374458',
        },
        // Accent — cool electric blue
        accent: {
          50:  '#eff8ff',
          100: '#dff0ff',
          200: '#b8e2ff',
          300: '#7aceff',
          400: '#38b6ff',
          500: '#0e9de8',
          600: '#027cc5',
          700: '#0362a0',
          800: '#075384',
          900: '#0c466e',
          950: '#072c49',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'ping-slow': 'ping 2s cubic-bezier(0, 0, 0.2, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'slide-in-left': 'slideInLeft 0.25s ease-out',
        'slide-in-right': 'slideInRight 0.25s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
        'flow': 'flow 2s linear infinite',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px #0e9de830' },
          '100%': { boxShadow: '0 0 20px #0e9de860, 0 0 40px #0e9de820' },
        },
        slideInLeft: {
          '0%': { transform: 'translateX(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        flow: {
          '0%': { strokeDashoffset: '100' },
          '100%': { strokeDashoffset: '0' },
        },
      },
      boxShadow: {
        'glow-sm': '0 0 8px rgba(14, 157, 232, 0.3)',
        'glow-md': '0 0 16px rgba(14, 157, 232, 0.4)',
        'glow-lg': '0 0 32px rgba(14, 157, 232, 0.3)',
        'critical': '0 0 16px rgba(239, 68, 68, 0.4)',
        'warning': '0 0 16px rgba(245, 158, 11, 0.4)',
        'healthy': '0 0 16px rgba(34, 197, 94, 0.4)',
        'panel': '0 4px 24px rgba(0,0,0,0.5), 0 1px 4px rgba(0,0,0,0.4)',
      },
      borderColor: {
        DEFAULT: 'rgba(255,255,255,0.07)',
      },
      backgroundImage: {
        'grid-pattern': `
          linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
          linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
        `,
      },
      backgroundSize: {
        'grid': '32px 32px',
      },
    },
  },
  plugins: [],
}
