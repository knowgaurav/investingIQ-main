import { describe, it, expect, vi, beforeEach } from 'vitest'
import { screen, fireEvent, waitFor } from '@testing-library/react'
import { render } from '../utils/test-utils'
import LLMSettings from '@/components/LLMSettings'

// Mock useLLMConfig hook
vi.mock('@/hooks/useLLMConfig', () => ({
    useLLMConfig: vi.fn(() => ({
        config: null,
        saveConfig: vi.fn(),
        clearConfig: vi.fn(),
        hasConfig: false,
    })),
    PROVIDER_MODELS: {
        openai: { default: 'gpt-4o', options: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'] },
        anthropic: { default: 'claude-3-5-sonnet-20241022', options: ['claude-3-5-sonnet-20241022'] },
        google: { default: 'gemini-1.5-pro', options: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
    },
    PROVIDER_NAMES: {
        openai: 'OpenAI',
        anthropic: 'Anthropic',
        google: 'Google AI',
    },
}))

import { useLLMConfig } from '@/hooks/useLLMConfig'

describe('LLMSettings', () => {
    beforeEach(() => {
        vi.mocked(useLLMConfig).mockReturnValue({
            config: null,
            saveConfig: vi.fn(),
            clearConfig: vi.fn(),
            hasConfig: false,
            isLoaded: true,
        })
        global.fetch = vi.fn()
    })

    it('renders floating settings button', () => {
        render(<LLMSettings />)
        const button = screen.getByTitle('Configure LLM')
        expect(button).toBeInTheDocument()
    })

    it('opens modal on button click', () => {
        render(<LLMSettings />)
        const button = screen.getByTitle('Configure LLM')
        fireEvent.click(button)
        expect(screen.getByText('Configure LLM')).toBeInTheDocument()
        expect(screen.getByText('Provider')).toBeInTheDocument()
    })

    it('closes modal on cancel button click', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))
        expect(screen.getByText('Configure LLM')).toBeInTheDocument()

        // Click cancel to close
        fireEvent.click(screen.getByText('Cancel'))
        // Modal closes, button title should be back to Configure LLM
        expect(screen.getByTitle('Configure LLM')).toBeInTheDocument()
    })

    it('renders provider dropdown with options', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        // Get all comboboxes and check the first one (provider)
        const selects = screen.getAllByRole('combobox')
        expect(selects.length).toBeGreaterThan(0)
        expect(screen.getByText('OpenAI')).toBeInTheDocument()
    })

    it('renders API key input', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        expect(screen.getByPlaceholderText('Enter your API key')).toBeInTheDocument()
    })

    it('renders model dropdown', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        expect(screen.getByText(/Model/)).toBeInTheDocument()
    })

    it('shows verify button', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        expect(screen.getByText('Verify Key')).toBeInTheDocument()
    })

    it('disables verify button when API key is empty', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        const verifyButton = screen.getByText('Verify Key')
        expect(verifyButton).toBeDisabled()
    })

    it('enables verify button when API key is entered', () => {
        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        const apiKeyInput = screen.getByPlaceholderText('Enter your API key')
        fireEvent.change(apiKeyInput, { target: { value: 'sk-test-key' } })

        const verifyButton = screen.getByText('Verify Key')
        expect(verifyButton).not.toBeDisabled()
    })

    it('shows green button when config exists', () => {
        vi.mocked(useLLMConfig).mockReturnValue({
            config: { provider: 'openai', apiKey: 'sk-test', model: 'gpt-4o' },
            saveConfig: vi.fn(),
            clearConfig: vi.fn(),
            hasConfig: true,
            isLoaded: true,
        })

        render(<LLMSettings />)
        const button = screen.getByTitle('LLM: OpenAI')
        expect(button).toHaveClass('bg-green-500')
    })

    it('shows clear button when config exists', () => {
        vi.mocked(useLLMConfig).mockReturnValue({
            config: { provider: 'openai', apiKey: 'sk-test', model: 'gpt-4o' },
            saveConfig: vi.fn(),
            clearConfig: vi.fn(),
            hasConfig: true,
            isLoaded: true,
        })

        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('LLM: OpenAI'))

        expect(screen.getByText('Clear')).toBeInTheDocument()
    })

    it('calls verify API on verify button click', async () => {
        vi.mocked(global.fetch).mockResolvedValueOnce({
            json: () => Promise.resolve({ valid: true }),
        } as Response)

        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        const apiKeyInput = screen.getByPlaceholderText('Enter your API key')
        fireEvent.change(apiKeyInput, { target: { value: 'sk-test-key' } })

        fireEvent.click(screen.getByText('Verify Key'))

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                'http://localhost:8000/api/v1/llm/verify',
                expect.objectContaining({
                    method: 'POST',
                })
            )
        })
    })

    it('shows verified status after successful verification', async () => {
        vi.mocked(global.fetch).mockResolvedValueOnce({
            json: () => Promise.resolve({ valid: true }),
        } as Response)

        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        const apiKeyInput = screen.getByPlaceholderText('Enter your API key')
        fireEvent.change(apiKeyInput, { target: { value: 'sk-test-key' } })

        fireEvent.click(screen.getByText('Verify Key'))

        await waitFor(() => {
            expect(screen.getByText('Verified')).toBeInTheDocument()
        })
    })

    it('shows error on failed verification', async () => {
        vi.mocked(global.fetch).mockResolvedValueOnce({
            json: () => Promise.resolve({ valid: false, error: 'Invalid API key' }),
        } as Response)

        render(<LLMSettings />)
        fireEvent.click(screen.getByTitle('Configure LLM'))

        const apiKeyInput = screen.getByPlaceholderText('Enter your API key')
        fireEvent.change(apiKeyInput, { target: { value: 'invalid-key' } })

        fireEvent.click(screen.getByText('Verify Key'))

        await waitFor(() => {
            expect(screen.getByText('Invalid API key')).toBeInTheDocument()
        })
    })
})
