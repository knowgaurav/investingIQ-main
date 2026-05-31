import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
        './src/components/**/*.{js,ts,jsx,tsx,mdx}',
        './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: 'rgb(var(--color-primary) / <alpha-value>)',
                accent: 'rgb(var(--color-accent) / <alpha-value>)',
                gain: 'rgb(var(--color-gain) / <alpha-value>)',
                loss: 'rgb(var(--color-loss) / <alpha-value>)',
                secondary: '#e0ebfd',
            },
            fontFamily: {
                display: ['var(--font-archivo)', 'system-ui', 'sans-serif'],
                sans: ['var(--font-plex-sans)', 'system-ui', 'sans-serif'],
                mono: ['var(--font-plex-mono)', 'ui-monospace', 'monospace'],
            },
            backgroundColor: {
                theme: 'rgb(var(--color-bg) / <alpha-value>)',
                'theme-secondary': 'rgb(var(--color-bg-secondary) / <alpha-value>)',
                'theme-card': 'rgb(var(--color-card) / <alpha-value>)',
            },
            textColor: {
                theme: 'rgb(var(--color-text) / <alpha-value>)',
                'theme-secondary': 'rgb(var(--color-text-secondary) / <alpha-value>)',
                'theme-muted': 'rgb(var(--color-text-muted) / <alpha-value>)',
            },
            borderColor: {
                theme: 'rgb(var(--color-border) / <alpha-value>)',
            },
            ringColor: {
                primary: 'rgb(var(--color-primary) / <alpha-value>)',
            },
        },
    },
    plugins: [],
}
export default config
