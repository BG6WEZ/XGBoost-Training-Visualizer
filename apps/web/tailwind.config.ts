/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 背景色
        background: {
          DEFAULT: '#0F1419',
          secondary: '#1A1F2E',
          tertiary: '#242B3A',
          elevated: '#2D3548',
        },
        // 文字色
        foreground: {
          DEFAULT: '#E5E7EB',
          secondary: '#9CA3AF',
          muted: '#6B7280',
          disabled: '#4B5563',
        },
        // 主色
        primary: {
          DEFAULT: '#6366F1',
          hover: '#5558E3',
          foreground: '#FFFFFF',
        },
        // 功能色
        success: '#10B981',
        warning: '#F59E0B',
        error: '#EF4444',
        info: '#3B82F6',
        // 边框色
        border: {
          DEFAULT: '#374151',
          muted: '#1F2937',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
      },
    },
  },
  plugins: [],
}