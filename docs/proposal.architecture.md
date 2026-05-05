# Proposal: CI/CD Architecture for Education App Deployment

This document outlines the proposed architecture to automate the build, deployment, and update process for the `education` app within the Frappe/ERPNext Kubernetes environment.

## 1. Application Inclusion Strategy

Since the official Frappe Helm chart requires a single container image containing all installed apps, we will use a custom image build process.

### Custom Image Build
- **`apps.json`**: A configuration file specifying the source and branch of all required apps.
  ```json
  [
    { "url": "https://github.com/frappe/erpnext", "branch": "version-16" },
    { "url": "https://github.com/frappe/payments", "branch": "version-16" },
    { "url": "https://github.com/DevOpsEdupan/escazu-education.git", "branch": "develop" }
  ]
  ```
- **Build Process**: Utilize `frappe/frappe_docker` to build the layered image.
- **Tagging**: Use the Git commit SHA as the image tag (e.g., `v16-<short-sha>`) to ensure traceability and enable rollbacks.

## 2. Kubernetes Configuration (Helm)

The deployment is managed via the `frappe/erpnext` Helm chart with the following key configurations in `values.yaml`:

- **Image**: Point to the custom registry (GHCR) and the specific tag.
- **Site Creation**: Ensure `education` is included in the `installApps` list during the initial `createSite` job.
- **Persistence**: Use a StorageClass with `ReadWriteMany (RWX)` for shared assets and logs across pods.

## 3. CI/CD Pipeline Design

The pipeline will be implemented using GitHub Actions to automate the lifecycle from code change to production.

### Pipeline Workflow

1. **Trigger**
   - Trigger on `push` to the `develop` or `main` branches.

2. **Build and Push (CI)**
   - Checkout `frappe_docker` and the `education` repository.
   - Build the Docker image using the current commit SHA.
   - Push the resulting image to the GitHub Container Registry (GHCR).

3. **Deployment (CD)**
   - **Update Image**: Update the Helm release with the new image tag:
     ```bash
     helm upgrade frappe-bench --set image.tag=v16-<sha> --namespace erpnext frappe/erpnext
     ```
   - **Database Migration**:
     - Enable the migration job: `helm upgrade frappe-bench --set jobs.migrate.enabled=true ...`
     - Wait for the `frappe-bench-migrate` job to complete successfully.
     - Disable the migration job to prevent redundant executions.

### Proposed Tooling
- **CI/CD Engine**: GitHub Actions.
- **Container Registry**: GHCR.io.
- **Deployment Method**: Helm (via GitHub Action runner with `kubeconfig`).
- **Optional Enhancement**: Implement **ArgoCD** for a GitOps approach, where the state of the cluster is automatically synced with the `values.yaml` in the git repository.
