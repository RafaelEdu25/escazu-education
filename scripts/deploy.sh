#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-340ba04}"
SITE="education.escazu.edupan.dev"
NAMESPACE="frappe"
RELEASE="frappe-education"
VALUES="infrastructure/values/frappe.staging.values.yaml"

echo "==> Deploying image tag: $IMAGE_TAG"

helm upgrade "$RELEASE" frappe/erpnext \
  -n "$NAMESPACE" \
  -f "$VALUES" \
  --set image.tag="$IMAGE_TAG" \
  --wait

echo "==> Running bench migrate..."
GUNICORN=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep erpnext-gunicorn | awk '{print $1}' | head -1)
kubectl exec -n "$NAMESPACE" "$GUNICORN" -- bash -c \
  "cd /home/frappe/frappe-bench && bench --site $SITE migrate"

echo "==> Disabling maintenance mode..."
kubectl exec -n "$NAMESPACE" "$GUNICORN" -- bash -c \
  "cd /home/frappe/frappe-bench && bench --site $SITE set-maintenance-mode off"

echo "==> Flushing Redis cache (assets_json + all keys)..."
VALKEY=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep valkey-cache | awk '{print $1}' | head -1)
kubectl exec -n "$NAMESPACE" "$VALKEY" -c frappe-education-valkey-cache -- redis-cli FLUSHALL

echo "==> Clearing Frappe cache..."
kubectl exec -n "$NAMESPACE" "$GUNICORN" -- bash -c \
  "cd /home/frappe/frappe-bench && bench --site $SITE clear-cache && bench --site $SITE clear-website-cache"

echo "==> Done. Site: https://$SITE"
