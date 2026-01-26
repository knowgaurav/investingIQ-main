import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent } from '@testing-library/react'
import { render } from '../utils/test-utils'
import DarkModeToggle from '@/components/DarkModeToggle'

describe('DarkModeToggle', () => {
    let mockStorage: Record<string, string> = {}

    beforeEach(() => {
        mockStorage = {}
        vi.spyOn(window.localStorage, 'getItem').mockImplementation((key) => mockStorage[key] || null)
        vi.spyOn(window.localStorage, 'setItem').mockImplementation((key, value) => {
            mockStorage[key] = value
        })
        document.documentElement.classList.remove('dark')
    })

    it('renders toggle button', async () => {
        render(<DarkModeToggle />)

        await vi.waitFor(() => {
            expect(screen.getByRole('button')).toBeInTheDocument()
        })
    })

    it('has correct aria-label for light mode', async () => {
        render(<DarkModeToggle />)

        await vi.waitFor(() => {
            const button = screen.getByRole('button')
            expect(button).toHaveAttribute('aria-label', 'Switch to dark mode')
        })
    })

    it('has correct aria-label for dark mode', async () => {
        mockStorage['theme'] = 'dark'
        render(<DarkModeToggle />)

        await vi.waitFor(() => {
            const button = screen.getByRole('button')
            expect(button).toHaveAttribute('aria-label', 'Switch to light mode')
        })
    })

    it('toggles theme on click', async () => {
        render(<DarkModeToggle />)

        await vi.waitFor(() => {
            expect(screen.getByRole('button')).toBeInTheDocument()
        })

        const button = screen.getByRole('button')
        fireEvent.click(button)

        await vi.waitFor(() => {
            expect(mockStorage['theme']).toBe('dark')
        })
    })
})
