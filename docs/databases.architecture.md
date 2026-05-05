# MariaDB Architecture & Deployment Plan

This document outlines the production deployment strategy for MariaDB using the `mariadb-operator`.

## Overview
The `mariadb-operator` allows for declarative management of MariaDB clusters on Kubernetes, providing high availability, automated backups, and seamless updates.

## Deployment Strategy

### 1. Installation Flow
The deployment is split into three parts to ensure CRD stability:
1. **CRDs**: Install `mariadb-operator-crds` to define the MariaDB resources.
2. **Operator**: Install `mariadb-operator` to manage the lifecycle of the databases.
3. **Cluster**: Deploy the `MariaDB` custom resource (via `mariadb-cluster` chart or manifest).

### 2. Production Configuration

#### High Availability (HA)
To ensure zero downtime and resilience:
- **Replicas**: Minimum 3 replicas for the operator.
- **Anti-Affinity**: Pods must be distributed across different nodes to avoid single-point-of-failure.
- **Pod Disruption Budget (PDB)**: Ensure at least 2 replicas are always available during maintenance.

#### Database Topology
- **Galera Cluster**: Recommended for production to provide synchronous multi-master replication.
- **MaxScale**: Used as a database proxy for read/write splitting and automated failover.

#### Backup & Recovery
- **Physical Backups**: Scheduled full backups using `mariadb-backup`.
- **Storage**: Use S3-compatible storage (e.g., MinIO, AWS S3) for off-cluster backup persistence.
- **PITR**: Enable binary log archiving for Point-In-Time Recovery.

#### Security & Monitoring
- **TLS**: Integration with `cert-manager` for automatic certificate rotation.
- **Observability**: Enable `mysqld-exporter` for Prometheus metrics and Grafana dashboards.

### 3. Update Strategy
Use the `ReplicasFirstPrimaryLast` strategy to perform rolling updates:
1. Update replicas one by one.
2. Wait for replicas to be healthy.
3. Update the primary node last.

## Deployment Commands
```bash
helm repo add mariadb-operator https://helm.mariadb.com/mariadb-operator
helm install mariadb-operator-crds mariadb-operator/mariadb-operator-crds
helm install mariadb-operator mariadb-operator/mariadb-operator -f infraestructure/mariadb.values.yaml
```
