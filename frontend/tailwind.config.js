/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        severity: {
          critical: '#dc2626', // red-600
          high: '#f97316',     // orange-500
          medium: '#facc15',   // yellow-400
          low: '#3b82f6',      // blue-400
        },
        verdict: {
          allow: '#22c55e',     // green-500
          deny: '#dc2626',      // red-600
          quarantine: '#f97316', // orange-500
          escalate: '#a855f7',  // purple-500
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
