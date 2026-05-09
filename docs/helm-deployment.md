# Despliegue ERPNext 16 + Education en Kubernetes con Helm

Guía para desplegar ERPNext v16 junto con la app `education` (Edupan) en un clúster Kubernetes usando el chart oficial `frappe/helm`.

---

## Prerrequisitos

| Requisito | Detalle |
|---|---|
| Kubernetes | 1.25+ |
| Helm | 3.10+ |
| Storage Class | Con acceso **ReadWriteMany (RWX)** — EFS, GlusterFS, Rook-CephFS, NFS |
| Container Registry | Docker Hub, GHCR, ECR, etc. para la imagen personalizada |
| MariaDB | 10.6 — externo (RDS) o via subchart del Helm chart |
| Redis/Valkey | Externo o via subchart (Valkey viene por defecto) |

> **Nodo único / dev:** RWO es suficiente si todos los pods corren en el mismo nodo. En producción se requiere RWX.

---

## Paso 1 — Construir imagen Docker personalizada

El chart de Helm usa una sola imagen de contenedor que debe incluir **todos** los apps (frappe, erpnext, payments, education). Se construye con `frappe/frappe_docker`.

### 1.1 Clonar frappe_docker

```bash
git clone https://github.com/frappe/frappe_docker
cd frappe_docker
```

### 1.2 Crear `apps.json`

```json
[
  {
    "url": "https://github.com/frappe/erpnext",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/frappe/payments",
    "branch": "version-16"
  },
  {
    "url": "https://github.com/DevOpsEdupan/escazu-education.git",
    "branch": "develop"
  }
]
```

> Para repositorios privados usa un token en la URL:
> `https://<TOKEN>@github.com/DevOpsEdupan/escazu-education.git`
> El token **nunca** queda en la imagen gracias al mecanismo `--secret`.

### 1.3 Construir imagen

```bash
export IMAGE_TAG="ghcr.io/devopsedupan/erpnext-education:v16-$(git -C ../education rev-parse --short HEAD)"

docker build \
  --no-cache \
  --build-arg=FRAPPE_PATH=https://github.com/frappe/frappe \
  --build-arg=FRAPPE_BRANCH=version-16 \
  --secret=id=apps_json,src=apps.json \
  --tag=${IMAGE_TAG} \
  --file=images/layered/Containerfile .
```

### 1.4 Push al registry

```bash
docker push ${IMAGE_TAG}
```

---

## Paso 2 — Preparar namespace y secretos en Kubernetes

```bash
kubectl create namespace erpnext

# Credenciales de base de datos
kubectl create secret generic db-credentials \
  --namespace erpnext \
  --from-literal=dbRootPassword='<ROOT_PASS>' \
  --from-literal=dbRootUser='root'

# (Opcional) imagePullSecret si el registry es privado
kubectl create secret docker-registry ghcr-secret \
  --namespace erpnext \
  --docker-server=ghcr.io \
  --docker-username=<GH_USER> \
  --docker-password=<GH_TOKEN>
```

---

## Paso 3 — Agregar repo Helm y descargar chart

```bash
helm repo add frappe https://helm.erpnext.com
helm repo update
helm search repo frappe/erpnext --versions | head -5
```

---

## Paso 4 — Configurar `values.yaml`

Crear archivo `infraestructure/helm/values.yaml`:

```yaml
# ──────────────────────────────────────────────
# Imagen personalizada con education incluido
# ──────────────────────────────────────────────
image:
  repository: ghcr.io/devopsedupan/erpnext-education
  tag: "v16-<GIT_SHORT_SHA>"   # reemplazar en CI/CD
  pullPolicy: IfNotPresent

imagePullSecrets:
  - name: ghcr-secret           # omitir si registry es público

# ──────────────────────────────────────────────
# Base de datos — opción A: subchart integrado
# ──────────────────────────────────────────────
mariadb-sts:
  enabled: true
  image:
    repository: mariadb
    tag: "10.6"
  auth:
    rootPassword: "<ROOT_PASS>"   # mismo valor que el secret de arriba
  persistence:
    size: 20Gi
    storageClass: ""              # dejar vacío para usar la default

# ──────────────────────────────────────────────
# Base de datos — opción B: RDS / MariaDB externo
# (comentar opción A y descomentar esto)
# ──────────────────────────────────────────────
# mariadb-sts:
#   enabled: false
# dbHost: "rds-endpoint.us-east-1.rds.amazonaws.com"
# dbPort: 3306
# dbExistingSecret: "db-credentials"   # key: dbRootPassword

# ──────────────────────────────────────────────
# Cache y colas — Valkey (default)
# ──────────────────────────────────────────────
valkey-cache:
  enabled: true
valkey-queue:
  enabled: true

# ──────────────────────────────────────────────
# Persistencia — requiere StorageClass RWX
# ──────────────────────────────────────────────
persistence:
  worker:
    storageClass: ""    # ej: "rook-cephfs", "efs-sc", "nfs-client"
    size: 8Gi
  logs:
    enabled: false      # activar en producción
    storageClass: ""
    size: 8Gi

# ──────────────────────────────────────────────
# Workers
# ──────────────────────────────────────────────
worker:
  gunicorn:
    replicaCount: 2
  default:
    replicaCount: 1
  short:
    replicaCount: 1
  long:
    replicaCount: 1
  scheduler:
    replicaCount: 1

# ──────────────────────────────────────────────
# Ingress
# ──────────────────────────────────────────────
ingress:
  enabled: true
  className: "nginx"        # o "traefik", "alb", etc.
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: erp.edupan.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: erp-edupan-tls
      hosts:
        - erp.edupan.com

# ──────────────────────────────────────────────
# Job: crear sitio (ejecutar solo la primera vez)
# ──────────────────────────────────────────────
jobs:
  createSite:
    enabled: false        # cambiar a true solo en primer despliegue
    siteName: "erp.edupan.com"
    adminPassword: "<ADMIN_PASS>"
    dbType: "mariadb"
    installApps:
      - "erpnext"
      - "payments"
      - "education"
    dropSiteOnFail: false
    forceCreate: false

  migrate:
    enabled: false        # activar en upgrades
    sites:
      - erp.edupan.com
```

---

## Paso 5 — Despliegue

### Primera vez (creación de sitio)

```bash
# 1. Habilitar createSite en values.yaml: enabled: true

helm install frappe-bench \
  --namespace erpnext \
  --values infraestructure/helm/values.yaml \
  frappe/erpnext

# 2. Esperar que el job termine
kubectl -n erpnext get jobs -w
kubectl -n erpnext logs job/frappe-bench-create-site -f

# 3. Una vez completado, deshabilitar createSite (enabled: false) y hacer upgrade
helm upgrade frappe-bench \
  --namespace erpnext \
  --values infraestructure/helm/values.yaml \
  frappe/erpnext
```

### Verificar pods

```bash
kubectl -n erpnext get pods
# Esperar: gunicorn, nginx, scheduler, socketio, workers — todos Running
```

---

## Paso 6 — Upgrades de la app education

Cada vez que se actualiza el código de `education`:

```bash
# 1. Reconstruir imagen con nuevo tag
export IMAGE_TAG="ghcr.io/devopsedupan/erpnext-education:v16-$(git rev-parse --short HEAD)"
docker build ... --tag=${IMAGE_TAG} ...
docker push ${IMAGE_TAG}

# 2. Actualizar tag en values.yaml
# image.tag: "v16-<nuevo-sha>"

# 3. Activar migrate en values.yaml: enabled: true
# jobs.migrate.sites: ["erp.edupan.com"]

# 4. Helm upgrade
helm upgrade frappe-bench \
  --namespace erpnext \
  --values infraestructure/helm/values.yaml \
  frappe/erpnext

# 5. Esperar migrate, luego desactivar migrate y hacer otro upgrade
kubectl -n erpnext logs job/frappe-bench-migrate -f
```

---

## Referencia rápida de comandos

```bash
# Ver estado del release
helm -n erpnext status frappe-bench

# Ver logs de gunicorn
kubectl -n erpnext logs deployment/frappe-bench-erpnext-gunicorn -f

# Acceso a bench CLI dentro del pod
kubectl -n erpnext exec -it deployment/frappe-bench-erpnext-gunicorn -- bash
bench --site erp.edupan.com list-apps

# Backup manual
kubectl -n erpnext create job --from=cronjob/frappe-bench-backup backup-manual-$(date +%s)

# Desinstalar (NO borra PVCs)
helm -n erpnext uninstall frappe-bench
```

---

## Notas importantes

- **Imagen única:** Todos los apps (frappe, erpnext, payments, education) deben estar en la misma imagen. No es posible instalar apps en tiempo de ejecución con este chart.
- **`createSite` es one-shot:** Después de crear el sitio, deshabilitar el job para evitar recreaciones accidentales.
- **Storage RWX:** En entornos locales/dev usar k3s con NFS provisioner o `local-path` con un solo nodo.
- **Versión del chart:** Este documento asume chart `8.x` (app version `v16.x`). Verificar con `helm search repo frappe/erpnext`.
- **Moodle Integration:** El módulo `moodle_integration` incluido en la app `education` se activa automáticamente al instalar la app. Configurar las credenciales Moodle en ERPNext > Moodle Settings después del despliegue.
