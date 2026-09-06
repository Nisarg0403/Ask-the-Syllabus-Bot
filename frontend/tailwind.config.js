/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: "var(--color-primary)",
        "primary-hover": "var(--color-primary-hover)",
        background: "var(--color-background)",
        surface: "var(--color-background)",
        "surface-container": "var(--color-surface-container)",
        "surface-variant": "var(--color-surface-variant)",
        "outline-variant": "var(--color-outline-variant)",
        "on-surface": "var(--color-on-surface)",
        "on-surface-variant": "var(--color-on-surface-variant)",
        border: "var(--color-border)",
        card: "var(--color-card)",
        "card-border": "var(--color-card-border)",
      },
      borderRadius: {
        "DEFAULT": "0.25rem",
        "lg": "12px",
        "xl": "16px",
        "full": "9999px"
      },
      spacing: {
        "container-padding": "40px",
        "sidebar-width": "280px",
        "stack-lg": "40px",
        "stack-md": "16px",
        "gutter": "24px",
        "stack-sm": "8px"
      },
      fontFamily: {
        "serif": ["Source Serif 4", "Lora", "Georgia", "serif"],
        "sans": ["Inter", "system-ui", "sans-serif"],
      }
    },
  },
  plugins: [],
}
