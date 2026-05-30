# Requirements Document

## Introduction

This document defines the requirements for setting up comprehensive frontend testing infrastructure for the InvestingIQ Next.js application. The goal is to establish a robust testing framework with Vitest and React Testing Library, configure GitHub Actions for CI/CD, and enforce test passing as a requirement for PR merges.

## Glossary

- **Test_Runner**: Vitest test framework configured for Next.js with jsdom environment
- **Testing_Library**: React Testing Library for component testing with user-centric queries
- **CI_Pipeline**: GitHub Actions workflow that runs tests on pull requests
- **Branch_Protection**: GitHub settings that require tests to pass before merging
- **Mock_Service**: Test utilities for mocking API calls and external dependencies
- **Coverage_Reporter**: Tool that generates and reports test coverage metrics

## Requirements

### Requirement 1: Vitest Configuration

**User Story:** As a developer, I want Vitest properly configured for Next.js, so that I can run tests for React components and TypeScript code.

#### Acceptance Criteria

1. THE Test_Runner SHALL support TypeScript files with .ts and .tsx extensions
2. THE Test_Runner SHALL use jsdom as the test environment for DOM testing
3. THE Test_Runner SHALL resolve path aliases (@/) to the src directory
4. THE Test_Runner SHALL exclude node_modules and .next directories from testing
5. WHEN running tests, THE Test_Runner SHALL load vitest.setup.ts for global test configuration
6. THE Test_Runner SHALL collect coverage from src directory excluding type definitions and layout files

### Requirement 2: Testing Library Setup

**User Story:** As a developer, I want React Testing Library configured with custom matchers, so that I can write expressive component tests.

#### Acceptance Criteria

1. THE Testing_Library SHALL extend Jest with jest-dom custom matchers
2. THE Testing_Library SHALL provide utilities for rendering components with providers (theme, router)
3. WHEN rendering components, THE Testing_Library SHALL wrap them with necessary context providers
4. THE Testing_Library SHALL support mocking Next.js router for navigation testing

### Requirement 3: API Mocking Infrastructure

**User Story:** As a developer, I want a consistent way to mock API calls, so that I can test components in isolation without network dependencies.

#### Acceptance Criteria

1. THE Mock_Service SHALL provide mock implementations for all API functions in lib/api.ts
2. WHEN a test needs API data, THE Mock_Service SHALL return predictable mock responses
3. THE Mock_Service SHALL support mocking fetch globally for integration tests
4. THE Mock_Service SHALL provide factory functions for generating test data

### Requirement 4: Component Test Coverage

**User Story:** As a developer, I want tests for critical UI components, so that I can catch regressions early.

#### Acceptance Criteria

1. THE Test_Runner SHALL have tests for StockSearch component covering search input, suggestions, and keyboard navigation
2. THE Test_Runner SHALL have tests for ThemeProvider component covering theme toggle and persistence
3. THE Test_Runner SHALL have tests for DarkModeToggle component covering click behavior
4. THE Test_Runner SHALL have tests for PriceChart component covering data rendering and empty states

### Requirement 5: Hook Test Coverage

**User Story:** As a developer, I want tests for custom hooks, so that I can verify their behavior in isolation.

#### Acceptance Criteria

1. THE Test_Runner SHALL have tests for useLLMConfig hook covering config loading, saving, and clearing
2. WHEN testing hooks, THE Test_Runner SHALL use renderHook from Testing Library

### Requirement 6: API Client Test Coverage

**User Story:** As a developer, I want tests for the API client, so that I can verify request formatting and error handling.

#### Acceptance Criteria

1. THE Test_Runner SHALL have tests for fetchApi wrapper covering success and error responses
2. THE Test_Runner SHALL have tests for searchStocks function covering query parameter formatting
3. THE Test_Runner SHALL have tests for ApiError class covering error construction

### Requirement 7: GitHub Actions CI Pipeline

**User Story:** As a developer, I want tests to run automatically on PRs, so that I can catch issues before merging.

#### Acceptance Criteria

1. WHEN a pull request is created or updated targeting main branch, THE CI_Pipeline SHALL run the test suite
2. THE CI_Pipeline SHALL use Node.js 20 for test execution
3. THE CI_Pipeline SHALL cache npm dependencies for faster builds
4. THE CI_Pipeline SHALL report test results as PR check status
5. IF tests fail, THEN THE CI_Pipeline SHALL mark the PR check as failed

### Requirement 8: Branch Protection Rules

**User Story:** As a team lead, I want PRs blocked from merging if tests fail, so that we maintain code quality.

#### Acceptance Criteria

1. THE Branch_Protection SHALL require the CI test check to pass before merge
2. THE Branch_Protection SHALL apply to the main branch
3. THE documentation SHALL include instructions for configuring branch protection in GitHub settings

### Requirement 9: Test Scripts and Developer Experience

**User Story:** As a developer, I want convenient npm scripts for running tests, so that I can easily run tests locally.

#### Acceptance Criteria

1. THE package.json SHALL have a "test" script that runs Vitest in run mode
2. THE package.json SHALL have a "test:watch" script for development (default Vitest behavior)
3. THE package.json SHALL have a "test:coverage" script for coverage reports
4. WHEN running tests, THE Test_Runner SHALL provide clear output with test names and results
