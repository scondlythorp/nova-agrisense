# Google Cloud Infrastructure Setup Guide

External infrastructure provisioning is required outside the AI Studio container before deploying Phase 1+:

1. **Cloud SQL (PostgreSQL 15+)**
   - Create instance in a nearby region (e.g., `europe-west1` or `europe-west2`).
   - Create database `nova_agrisense` and least-privilege application role `nova_user`.
   - Run `infrastructure/postgres-init.sql` to enable `pgcrypto` and `postgis`.
2. **Secret Manager**
   - Store `nova-database-url` (Cloud SQL Unix socket URI or private IP URI) and `nova-secret-key` (32+ random bytes).
3. **Cloud Storage**
   - Create a private bucket for staged CSV/Excel imports and generated PDF/CSV/XLSX reports with uniform bucket-level access.
4. **Cloud Run**
   - Build and deploy `apps/api/Dockerfile` using `infrastructure/cloudrun-api.yaml`.
   - Build and deploy `apps/web/Dockerfile` using `infrastructure/cloudrun-web.yaml`.
5. **GitHub Actions CI/CD**
   - Configure Workload Identity Federation and repository secrets for automated Cloud Run deployments on `main`.
