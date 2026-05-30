# Branch Protection Setup

This document explains how to configure branch protection rules in GitHub to require tests to pass before merging PRs.

## Prerequisites

1. The GitHub Actions workflow (`.github/workflows/frontend-tests.yml`) must be merged to the main branch first
2. At least one PR must have run the workflow so GitHub recognizes the check

## Configuration Steps

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Branches**
3. Under "Branch protection rules", click **Add rule**
4. Configure the rule:

   - **Branch name pattern**: `main` (or `master` if that's your default branch)
   
   - Check **Require a pull request before merging**
   
   - Check **Require status checks to pass before merging**
     - Search for and select: `test` (this is the job name from the workflow)
   
   - Check **Require branches to be up to date before merging** (recommended)

5. Click **Create** or **Save changes**

## What This Does

- PRs targeting the main branch will show the "Frontend Tests" check
- The check must pass (green) before the PR can be merged
- If tests fail, the merge button will be disabled

## Troubleshooting

**Check not appearing?**
- Ensure the workflow file is on the main branch
- Create a test PR that modifies files in `frontend/` to trigger the workflow
- The check name is the `jobs.<job_id>` value, which is `test`

**Tests passing locally but failing in CI?**
- Check the Actions tab for detailed logs
- Ensure all dependencies are in `package.json` (not just installed locally)
- Verify Node.js version matches (workflow uses Node 20)
