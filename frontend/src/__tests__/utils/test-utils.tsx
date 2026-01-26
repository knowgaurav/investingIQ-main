import { render, RenderOptions } from '@testing-library/react'
import { ThemeProvider } from '@/components/ThemeProvider'
import { ReactElement } from 'react'

function customRender(ui: ReactElement, options?: Omit<RenderOptions, 'wrapper'>) {
    return render(ui, {
        wrapper: ({ children }) => <ThemeProvider>{children}</ThemeProvider>,
        ...options,
    })
}

export * from '@testing-library/react'
export { customRender as render }
