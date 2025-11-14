/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{ts,tsx,js,jsx,mdx}', './public/index.html'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        foreground: 'var(--foreground)',

        card: 'var(--card)',
        'card-foreground': 'var(--card-foreground)',

        popover: 'var(--popover)',
        'popover-foreground': 'var(--popover-foreground)',

        primary: 'var(--primary)',
        'primary-foreground': 'var(--primary-foreground)',
        'primary-border': 'var(--primary-border)',
        'primary-hover': 'var(--primary-hover)',
        'primary-active': 'var(--primary-active)',

        secondary: 'var(--secondary)',
        'secondary-foreground': 'var(--secondary-foreground)',
        'secondary-border': 'var(--secondary-border)',
        'secondary-hover': 'var(--secondary-hover)',
        'secondary-active': 'var(--secondary-active)',

        accent: 'var(--accent)',
        'accent-foreground': 'var(--accent-foreground)',
        'accent-border': 'var(--accent-border)',
        'accent-hover': 'var(--accent-hover)',
        'accent-active': 'var(--accent-active)',

        muted: 'var(--muted)',
        'muted-foreground': 'var(--muted-foreground)',
        'muted-border': 'var(--muted-border)',

        destructive: 'var(--destructive)',
        'destructive-foreground': 'var(--destructive-foreground)',
        'destructive-border': 'var(--destructive-border)',
        'destructive-hover': 'var(--destructive-hover)',
        'destructive-active': 'var(--destructive-active)',

        success: 'var(--success)',
        'success-foreground': 'var(--success-foreground)',
        'success-border': 'var(--success-border)',
        'success-hover': 'var(--success-hover)',
        'success-active': 'var(--success-active)',

        warning: 'var(--warning)',
        'warning-foreground': 'var(--warning-foreground)',
        'warning-border': 'var(--warning-border)',
        'warning-hover': 'var(--warning-hover)',
        'warning-active': 'var(--warning-active)',

        info: 'var(--info)',
        'info-foreground': 'var(--info-foreground)',
        'info-border': 'var(--info-border)',
        'info-hover': 'var(--info-hover)',
        'info-active': 'var(--info-active)',

        neutral: 'var(--neutral)',
        'neutral-foreground': 'var(--neutral-foreground)',
        'neutral-border': 'var(--neutral-border)',

        border: 'var(--border)',
        input: 'var(--input)',
        ring: 'var(--ring)',

        violet: {
          DEFAULT: '#7c3aed',
          foreground: '#ffffff',
        },
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
      },
      borderColor: {
        border: 'var(--border)',
      },
      ringColor: {
        ring: 'var(--ring)',
      },
    },
  },
  plugins: [],
}
