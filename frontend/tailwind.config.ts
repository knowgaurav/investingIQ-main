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
                primary: '#3d85ed',
                secondary: '#e0ebfd',
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
        },
    },
    plugins: [],
}
export default config
