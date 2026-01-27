# InvestingIQ Deployment Guide

This guide covers the complete CI/CD setup for deploying InvestingIQ to production.

## Architecture Overview

| Component | Platform | Trigger | Cost |
|-----------|----------|---------|------|
| Frontend (Next.js) | Vercel | Auto on push to main | Free |
| Backend (FastAPI) | Render | Deploy hook or auto | Free |
| Functions | Azure Functions | GitHub Actions | Pay-per-use |

## Prerequisites

- GitHub repository with this codebase
- Azure subscription with Contributor access
- Azure Service Principal with PFX certificate
- Vercel account (free)
- Render account (free)

---

## 1. Azure Service Principal Setup

### Create Service Principal with Certificate

```bash
# Generate a self-signed certificate (if you don't have one)
openssl req -x509 -newkey rsa:4096 -keyout sp-key.pem -out sp-cert.pem -days 365 -nodes \
  -subj "/CN=InvestingIQ-SP"

# Combine into PFX (PKCS#12) format
openssl pkcs12 -export -out sp-cert.pfx -inkey sp-key.pem -in sp-cert.pem -passout pass:

# Create Service Principal with certificate
az ad sp create-for-rbac \
  --name "InvestingIQ-Deployment" \
  --role Contributor \
  --scopes /subscriptions/<YOUR_SUBSCRIPTION_ID> \
  --cert @sp-cert.pem
```

Save the output - you'll need:
- `appId` → `AZURE_CLIENT_ID`
- `tenant` → `AZURE_TENANT_ID`

### Base64 Encode the PFX Certificate

```bash
# Encode the PFX file for GitHub secrets
base64 -i sp-cert.pfx -o sp-cert-base64.txt

# Copy the contents of sp-cert-base64.txt to AZURE_SP_CERTIFICATE_BASE64 secret
cat sp-cert-base64.txt
```

---

## 2. GitHub Secrets Configuration

Go to: **Repository → Settings → Secrets and variables → Actions**

### Azure Secrets (Required for Functions deployment)

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `AZURE_CLIENT_ID` | Service Principal App ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` |
| `AZURE_SP_CERTIFICATE_BASE64` | Base64-encoded PFX certificate | (long base64 string) |
| `AZURE_SP_CERTIFICATE_PASSWORD` | PFX password (empty if none) | `` |
| `AZURE_RESOURCE_GROUP` | Resource Group name | `investingiq-rg` |
| `AZURE_FUNCTION_APP_NAME` | Function App name | `investingiq-functions` |

### Azure Functions App Settings

| Secret Name | Description |
|-------------|-------------|
| `FUNC_DATABASE_URL` | PostgreSQL connection string |
| `FUNC_OPENAI_API_KEY` | OpenAI/LLM API key |
| `FUNC_OPENAI_BASE_URL` | LLM API base URL |
| `FUNC_LLM_MODEL` | Model name (e.g., `deepseek-ai/deepseek-v3.1`) |
| `FUNC_BACKEND_CALLBACK_URL` | Render backend URL |
| `FUNC_SERVICEBUS_CONNECTION_STRING` | Azure Service Bus connection |
| `FUNC_STORAGE_CONNECTION_STRING` | Azure Storage connection |
| `FUNC_ALPHA_VANTAGE_API_KEYS` | Alpha Vantage API keys (comma-separated) |

### Render Secret (Optional)

| Secret Name | Description |
|-------------|-------------|
| `RENDER_DEPLOY_HOOK_URL` | Render deploy hook URL (if not using auto-deploy) |

---

## 3. Vercel Setup (Frontend)

### Connect Repository

1. Go to [vercel.com](https://vercel.com) and sign in
2. Click "Add New Project"
3. Import your GitHub repository
4. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Next.js
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### Environment Variables

Add in Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://investingiq-backend.onrender.com` |

Vercel will automatically deploy on every push to `main`.

---

## 4. Render Setup (Backend)

### Option A: Blueprint (Recommended)

1. Go to [render.com](https://render.com) and sign in
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will detect `render.yaml` and create the service

### Option B: Manual Setup

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `investingiq-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Docker
   - **Dockerfile Path**: `Dockerfile`

### Environment Variables

Add in Render Dashboard → Service → Environment:

| Variable | Value |
|----------|-------|
| `DATABASE_URL` | Your PostgreSQL connection string |
| `AZURE_SERVICEBUS_CONNECTION_STRING` | Azure Service Bus connection |
| `OPENAI_API_KEY` | Your LLM API key |
| `OPENAI_BASE_URL` | `https://ai.megallm.io/v1` |
| `LLM_MODEL` | `deepseek-ai/deepseek-v3.1` |
| `NEWS_API_KEY` | Your News API key |
| `ALPHA_VANTAGE_API_KEY` | Your Alpha Vantage key |

### Deploy Hook (Optional)

To trigger deploys from GitHub Actions:
1. Go to Service → Settings → Deploy Hook
2. Copy the URL
3. Add as `RENDER_DEPLOY_HOOK_URL` GitHub secret

---

## 5. GitHub Branch Protection

Go to: **Repository → Settings → Branches → Add rule**

Configure for `main` branch:
- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
  - Add: `test` (from frontend-tests, backend-tests, functions-tests)
- ✅ Require branches to be up to date before merging

---

## 6. Workflow Summary

### On Pull Request to main:

```
PR Created/Updated
       │
       ├── frontend/** changes → Frontend Tests
       ├── backend/** changes  → Backend Tests
       └── functions/** changes → Functions Tests
       │
       ▼
All tests must pass to merge
```

### On Merge to main:

```
Merge to main
       │
       ├── frontend/** changes → Vercel auto-deploys
       ├── backend/** changes  → Render deploy hook
       └── functions/** changes → Azure Functions deploy
```

---

## Troubleshooting

### Azure Login Fails

```
Error: AADSTS700027: Client assertion contains an invalid signature
```

**Solution**: Regenerate the certificate and update `AZURE_SP_CERTIFICATE_BASE64` secret.

### Azure Functions Deployment Fails

```
Error: The Resource 'Microsoft.Web/sites/xxx' was not found
```

**Solution**: Verify `AZURE_FUNCTION_APP_NAME` and `AZURE_RESOURCE_GROUP` secrets match your Azure resources.

### Render Deploy Hook Not Working

**Solution**: 
1. Verify the hook URL is correct
2. Check Render dashboard for deploy logs
3. Ensure the service is not suspended (free tier limitation)

### Vercel Build Fails

**Solution**:
1. Check build logs in Vercel dashboard
2. Ensure `NEXT_PUBLIC_API_URL` is set
3. Verify `frontend/package.json` has correct build script

---

## Cost Breakdown

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Vercel | Hobby | Free |
| Render | Free | Free (750 hours/month) |
| Azure Functions | Consumption | ~$0-5 (pay per execution) |
| Azure Storage | Standard | ~$1-2 |
| Azure Service Bus | Basic | ~$0.05 per million operations |

**Total estimated cost**: $1-10/month depending on usage

---

## Quick Reference

### Find Azure IDs

```bash
# Subscription ID
az account show --query id -o tsv

# Tenant ID
az account show --query tenantId -o tsv

# Service Principal Client ID (after creation)
az ad sp list --display-name "InvestingIQ-Deployment" --query "[0].appId" -o tsv
```

### Test Azure Login Locally

```bash
az login --service-principal \
  --username <CLIENT_ID> \
  --tenant <TENANT_ID> \
  --password sp-cert.pfx
```

### Verify Function App Exists

```bash
az functionapp show \
  --resource-group <RESOURCE_GROUP> \
  --name <FUNCTION_APP_NAME>
```
