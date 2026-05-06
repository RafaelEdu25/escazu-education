#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-340ba04}"
SITE="education.escazu.edupan.dev"
NAMESPACE="frappe"
RELEASE="frappe-education"
VALUES="infraestructure/values/frappe.staging.values.yaml"

echo "==> Deploying image tag: $IMAGE_TAG"

helm upgrade "$RELEASE" frappe/erpnext \
  -n "$NAMESPACE" \
  -f "$VALUES" \
  --set image.tag="$IMAGE_TAG" \
  --wait

echo "==> Disabling maintenance mode..."
GUNICORN=$(kubectl get pods -n "$NAMESPACE" --no-headers | grep erpnext-gunicorn | awk '{print $1}' | head -1)
kubectl exec -n "$NAMESPACE" "$GUNICORN" -- bash -c \
  "cd /home/frappe/frappe-bench && bench --site $SITE set-maintenance-mode off"

echo "==> Clearing cache..."
kubectl exec -n "$NAMESPACE" "$GUNICORN" -- bash -c \
  "cd /home/frappe/frappe-bench && bench --site $SITE clear-cache && bench --site $SITE clear-website-cache"

echo "==> Done. Site: https://$SITE"
