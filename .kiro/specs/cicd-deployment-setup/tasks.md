# Implementation Plan: CI/CD Deployment Setup

## Overview

This plan implements CI/CD pipelines for InvestingIQ using GitHub Actions. The implementation creates test workflows for PRs and deployment workflows for merges to main, targeting Vercel (frontend), Render (backend), and Azure Functions (serverless).

## Tasks

- [x] 1. Create backend test workflow
  - [x] 1.1 Create `.github/workflows/backend-tests.yml` with Python 3.11 setup
    - Trigger on PR to main with `backend/**` path changes
    - Setup Python with pip caching
    - Install dependencies from `backend/requirements.txt`
    - Run pytest with coverage reporting
    - Upload coverage artifact
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Create unified deployment workflow
  - [x] 2.1 Create `.github/workflows/deploy.yml` with change detection
    - Trigger on push to main branch
    - Use `dorny/paths-filter` to detect changed components
    - Output boolean flags for frontend, backend, functions changes
    - _Requirements: 2.1, 2.5_

  - [x] 2.2 Add Vercel deployment job
    - Conditional on frontend changes
    - Use Vercel CLI or GitHub integration trigger
    - _Requirements: 2.2, 5.1_

  - [x] 2.3 Add Render deployment job
    - Conditional on backend changes
    - Call Render deploy hook URL from secrets
    - _Requirements: 2.3, 4.1_

  - [x] 2.4 Add Azure Functions deployment job
    - Conditional on functions changes
    - Decode PFX certificate from base64 secret
    - Authenticate with `az login --service-principal` using certificate
    - Package and deploy functions using `az functionapp deployment`
    - Configure app settings from secrets
    - _Requirements: 2.4, 3.1, 3.2, 3.3, 3.4_

- [x] 3. Create Render configuration
  - [x] 3.1 Create `render.yaml` with backend service definition
    - Define Docker service pointing to `backend/Dockerfile`
    - Configure health check endpoint `/health`
    - Set environment group reference for secrets
    - _Requirements: 4.2, 4.3, 4.4_

- [x] 4. Create deployment documentation
  - [x] 4.1 Create `DEPLOYMENT.md` with complete setup guide
    - Document all GitHub secrets with descriptions
    - Provide Azure Service Principal setup with PFX certificate instructions
    - Explain Vercel GitHub integration setup
    - Explain Render deploy hook configuration
    - Include troubleshooting section for common failures
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 5. Checkpoint - Verify all files created
  - Ensure all workflow YAML files have valid syntax
  - Verify render.yaml structure is correct
  - Confirm documentation covers all required secrets
  - Ask the user if questions arise

## Notes

- Vercel deployment relies on Vercel's native GitHub integration (auto-deploys on push to main)
- Render deployment uses deploy hooks rather than render.yaml auto-deploy for more control
- Azure Functions uses Service Principal with PFX certificate (not federated credentials)
- Branch protection rules must be configured manually in GitHub repository settings
