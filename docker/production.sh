#!/bin/bash
# =============================================================================
#  production.sh — Despliegue completo de ERPNext + Education
#
#  Uso:
#    ./production.sh install    → Primera instalación (infra + config + sitio)
#    ./production.sh upgrade    → Actualizar imagen y migrar BD
#    ./production.sh up         → Levantar stack (sitio ya existe)
#    ./production.sh down       → Bajar todos los servicios
#    ./production.sh logs       → Ver logs (Ctrl+C para salir)
#    ./production.sh logs <svc> → Logs de un servicio específico
# =============================================================================
set -euo pipefail

COMPOSE_FILE="$(dirname "$0")/compose.yml"
ENV_FILE="$(dirname "$0")/.env"

# ─────────────────────────────────────────────────────────────────────────────
#  CONFIGURACIÓN — edita estos valores antes del primer despliegue
# ─────────────────────────────────────────────────────────────────────────────

# Imagen
IMAGE_NAME="docker.io/frappe/erpnext"
VERSION="version-16"
PULL_POLICY="always"
APP_BRANCH="version-16"

# Sitio Frappe
SITE_NAME="mi-escuela.com"           # ← cambia esto
ADMIN_PASSWORD="cambia_esto_admin"   # ← cambia esto
INSTALL_APP_ARGS="--install-app erpnext --install-app education"

# App Education (repo custom)
INSTALL_EDUCATION="1"
EDUCATION_REPO="https://github.com/DevOpsEdupan/escazu-education"

# Base de datos
DB_HOST="db"
DB_PORT="3306"
DB_ROOT_PASSWORD="cambia_esto_db"    # ← cambia esto

# Redis
REDIS_CACHE="redis-cache:6379"
REDIS_QUEUE="redis-queue:6379"

# Nginx / acceso público
HTTP_PORT="8080"
FRAPPE_SITE_NAME_HEADER="\$host"
UPSTREAM_REAL_IP_ADDRESS="0.0.0.0/0"

# Gunicorn
GUNICORN_WORKERS="2"

# Volumen de sites (bind mount local por defecto)
SITE_VOLUME_TYPE="none"
SITE_VOLUME_OPTS="bind"
SITE_VOLUME_DEV="./sites"

# ─────────────────────────────────────────────────────────────────────────────
#  FIN DE CONFIGURACIÓN — no es necesario tocar nada más abajo
# ─────────────────────────────────────────────────────────────────────────────

# Genera el .env que consume compose.yml
generate_env() {
  cat > "$ENV_FILE" <<EOF
# Generado por production.sh — no editar manualmente
IMAGE_NAME=${IMAGE_NAME}
VERSION=${VERSION}
PULL_POLICY=${PULL_POLICY}
APP_BRANCH=${APP_BRANCH}

SITE_NAME=${SITE_NAME}
ADMIN_PASSWORD=${ADMIN_PASSWORD}
INSTALL_APP_ARGS=${INSTALL_APP_ARGS}

INSTALL_EDUCATION=${INSTALL_EDUCATION}
EDUCATION_REPO=${EDUCATION_REPO}

DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}
DB_ROOT_PASSWORD=${DB_ROOT_PASSWORD}

REDIS_CACHE=${REDIS_CACHE}
REDIS_QUEUE=${REDIS_QUEUE}

HTTP_PORT=${HTTP_PORT}
FRAPPE_SITE_NAME_HEADER=${FRAPPE_SITE_NAME_HEADER}
UPSTREAM_REAL_IP_ADDRESS=${UPSTREAM_REAL_IP_ADDRESS}

GUNICORN_WORKERS=${GUNICORN_WORKERS}

SITE_VOLUME_TYPE=${SITE_VOLUME_TYPE}
SITE_VOLUME_OPTS=${SITE_VOLUME_OPTS}
SITE_VOLUME_DEV=${SITE_VOLUME_DEV}

# Flags one-off (production.sh los controla, no cambiar aquí)
CONFIGURE=0
CREATE_SITE=0
MIGRATE=0
EOF
  echo "✔  .env generado en $ENV_FILE"
}

# Wrapper de docker compose con el env y compose file correctos
dc() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

# Igual que dc() pero sobreescribe variables puntuales para jobs one-off
dc_with() {
  local overrides="$1"; shift
  env $(echo "$overrides" | tr '\n' ' ') \
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

wait_service() {
  local svc="$1"
  echo "  ⏳ Esperando que '$svc' termine..."
  dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" wait "$svc" 2>/dev/null || {
    # fallback: esperar hasta que el contenedor salga con código 0
    local cid
    cid=$(dc ps -q "$svc" 2>/dev/null | head -1)
    [[ -z "$cid" ]] && return 0
    docker wait "$cid" > /dev/null
  }
}

# ─────────────────────────────────────────────────────────────────────────────

case "${1:-help}" in

  # ── PRIMERA INSTALACIÓN ───────────────────────────────────────────────────
  install)
    echo ""
    echo "════════════════════════════════════════"
    echo "  ERPNext + Education  —  INSTALL"
    echo "════════════════════════════════════════"

    generate_env
    mkdir -p ./sites

    echo ""
    echo "▶  [1/4] Levantando infraestructura base (db + redis)..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" up -d db redis-cache redis-queue
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" wait db redis-cache redis-queue

    echo ""
    echo "▶  [2/4] Ejecutando configurator (escribe common_site_config.json)..."
    dc_with "CONFIGURE=1 CREATE_SITE=0 MIGRATE=0" up configurator
    wait_service configurator

    echo ""
    echo "▶  [3/4] Creando sitio e instalando apps..."
    dc_with "CONFIGURE=0 CREATE_SITE=1 MIGRATE=0" up create-site
    wait_service create-site

    echo ""
    echo "▶  [4/4] Levantando stack completo..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" up -d \
      backend websocket queue-default queue-long queue-short scheduler frontend

    echo ""
    echo "✅  Instalación completa."
    echo "    URL:      http://$(hostname -I | awk '{print $1}'):${HTTP_PORT}"
    echo "    Usuario:  Administrator"
    echo "    Password: ${ADMIN_PASSWORD}"
    echo ""
    ;;

  # ── ACTUALIZACIÓN ─────────────────────────────────────────────────────────
  upgrade)
    echo ""
    echo "════════════════════════════════════════"
    echo "  ERPNext + Education  —  UPGRADE"
    echo "════════════════════════════════════════"

    generate_env

    echo ""
    echo "▶  [1/3] Descargando imagen nueva..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" pull \
      backend websocket queue-default queue-long queue-short scheduler frontend

    echo ""
    echo "▶  [2/3] Ejecutando migración de base de datos..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=1" up migration
    wait_service migration

    echo ""
    echo "▶  [3/3] Reiniciando servicios..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" up -d --force-recreate \
      backend websocket queue-default queue-long queue-short scheduler frontend

    echo ""
    echo "✅  Upgrade completo."
    echo ""
    ;;

  # ── LEVANTAR (sitio ya existe) ────────────────────────────────────────────
  up)
    generate_env
    echo "▶  Levantando stack..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" up -d
    echo "✅  Stack activo en http://$(hostname -I | awk '{print $1}'):${HTTP_PORT}"
    ;;

  # ── BAJAR ─────────────────────────────────────────────────────────────────
  down)
    generate_env
    echo "▶  Bajando stack..."
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" down
    echo "✅  Stack detenido."
    ;;

  # ── LOGS ──────────────────────────────────────────────────────────────────
  logs)
    generate_env
    dc_with "CONFIGURE=0 CREATE_SITE=0 MIGRATE=0" logs -f "${2:-}"
    ;;

  # ── AYUDA ─────────────────────────────────────────────────────────────────
  *)
    echo ""
    echo "Uso: $0 {install|upgrade|up|down|logs [servicio]}"
    echo ""
    echo "  install  → Primera instalación completa"
    echo "  upgrade  → Actualizar imagen + migrar BD"
    echo "  up       → Levantar stack (sitio ya creado)"
    echo "  down     → Detener todos los servicios"
    echo "  logs     → Ver todos los logs en tiempo real"
    echo "  logs <s> → Ver logs de un servicio específico"
    echo ""
    exit 1
    ;;
esac