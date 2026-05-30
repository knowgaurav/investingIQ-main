# Implementation Plan: Frontend Testing Setup

## Overview

This plan implements comprehensive frontend testing infrastructure for the InvestingIQ Next.js application using Vitest. Work should be done on a feature branch (`feature/frontend-testing-setup`).

## Tasks

- [x] 1. Install Vitest and configure test environment
  - [x] 1.1 Install Vitest and dependencies
    - Run: `npm install -D vitest @vitejs/plugin-react jsdom @testing-library/jest-dom`
    - Remove old Jest dependencies: `npm uninstall jest @testing-library/jest-dom`
    - Note: Keep @testing-library/react as it works with Vitest
    - _Requirements: 1.1, 1.2_
  - [x] 1.2 Create vitest.config.ts
    - Configure jsdom environment
    - Set up path aliases (@/ -> src/)
    - Configure coverage with v8 provider
    - Exclude node_modules and .next
    - _Requirements: 1.2, 1.3, 1.4, 1.6_
  - [x] 1.3 Create vitest.setup.ts
    - Import @testing-library/jest-dom/vitest
    - Mock next/navigation (useRouter, usePathname, useSearchParams)
    - Mock localStorage
    - Mock window.matchMedia for theme detection
    - _Requirements: 1.5, 2.1, 2.4_
  - [x] 1.4 Update package.json test scripts
    - Update "test": "vitest run"
    - Add "test:watch": "vitest"
    - Add "test:coverage": "vitest run --coverage"
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 2. Create test utilities and mock infrastructure
  - [x] 2.1 Create src/__tests__/utils/test-utils.tsx
    - Custom render function that wraps with ThemeProvider
    - Re-export all from @testing-library/react
    - _Requirements: 2.2, 2.3_
  - [x] 2.2 Create src/__tests__/utils/mock-data.ts
    - createMockStock factory function
    - createMockPriceData factory function
    - _Requirements: 3.4_

- [x] 3. Write API client tests
  - [x] 3.1 Create src/__tests__/lib/api.test.ts
    - Test ApiError class construction
    - Test fetchApi success and error handling
    - Test searchStocks URL parameter formatting
    - _Requirements: 6.1, 6.2, 6.3_
  - [x] 3.2 Write property test for ApiError construction
    - **Property 3: API Error Construction Preserves Values**
    - **Validates: Requirements 6.3**
  - [x] 3.3 Write property test for searchStocks URL formatting
    - **Property 4: Search Query URL Formatting**
    - **Validates: Requirements 6.2**

- [x] 4. Write hook tests
  - [x] 4.1 Create src/__tests__/hooks/useLLMConfig.test.ts
    - Test initial state (null config, isLoaded false)
    - Test loading config from localStorage
    - Test saveConfig persists to localStorage
    - Test clearConfig removes from localStorage
    - Test hasConfig computed property
    - _Requirements: 5.1, 5.2_
  - [x] 4.2 Write property test for LLM config round trip
    - **Property 2: LLM Config Persistence Round Trip**
    - **Validates: Requirements 5.1**

- [x] 5. Checkpoint - Verify core tests pass
  - Run `npm test` and ensure all tests pass
  - Ask user if questions arise

- [x] 6. Write component tests
  - [x] 6.1 Create src/__tests__/components/ThemeProvider.test.tsx
    - Test initial theme state
    - Test toggleTheme changes theme
    - Test theme persists to localStorage
    - _Requirements: 4.2_
  - [x] 6.2 Write property test for theme toggle round trip
    - **Property 1: Theme Toggle Round Trip**
    - **Validates: Requirements 2.3**
  - [x] 6.3 Create src/__tests__/components/DarkModeToggle.test.tsx
    - Test renders toggle button
    - Test click calls toggleTheme
    - Test aria-label updates based on theme
    - _Requirements: 4.3_
  - [x] 6.4 Create src/__tests__/components/PriceChart.test.tsx
    - Test renders chart with data
    - Test shows empty state message when no data
    - Test color changes based on price direction
    - _Requirements: 4.4_
  - [x] 6.5 Create src/__tests__/components/StockSearch.test.tsx
    - Test renders search input
    - Test typing triggers search (with debounce)
    - Test suggestions appear on results
    - Test keyboard navigation (ArrowDown, ArrowUp, Enter, Escape)
    - Test selecting suggestion navigates to analyze page
    - _Requirements: 4.1_

- [x] 7. Checkpoint - Verify all component tests pass
  - Run `npm test` and ensure all tests pass
  - Ask user if questions arise

- [x] 8. Set up GitHub Actions CI
  - [x] 8.1 Create .github/workflows/frontend-tests.yml
    - Trigger on PR to main/master for frontend/** paths
    - Use Node.js 20 with npm cache
    - Run npm ci and npm test with coverage
    - Upload coverage artifact
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  - [x] 8.2 Create BRANCH_PROTECTION.md documentation
    - Instructions for configuring branch protection in GitHub
    - Require "Frontend Tests" check to pass
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 9. Final checkpoint - Run full test suite
  - Run `npm test -- --coverage` and verify all tests pass
  - Commit all changes and push to feature branch
  - Ask user if questions arise

## Notes

- All property-based tests are required for comprehensive coverage
- All work should be done on `feature/frontend-testing-setup` branch
- fast-check library needed for property tests (add to devDependencies)
- Branch protection must be configured manually in GitHub after workflow is merged
- Vitest uses `vi` instead of `jest` for mocking functions
