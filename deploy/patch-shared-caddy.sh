#!/usr/bin/env bash
# Conecta el Caddy existente de otro proyecto (gamificacion-fundacion) a una
# red compartida y le agrega un segundo bloque de sitio para DetectorIA, SIN
# tocar el repositorio ni el docker-compose de ese otro proyecto.
#
# Es un cambio en caliente sobre el contenedor en ejecución: si ese contenedor
# se recrea alguna vez (redeploy del otro proyecto, reinicio de la VM), hay
# que volver a correr este script. Es idempotente: se puede ejecutar todas las
# veces que haga falta sin duplicar nada.
#
# Uso: ./patch-shared-caddy.sh

set -euo pipefail

CADDY_CONTAINER="gamificacion-fundacion-caddy-1"
NETWORK="edge"
DOMAIN="detectoria.duckdns.org"
UPSTREAM="detectoria-frontend:80"

echo "1) Red compartida '$NETWORK'..."
sudo docker network inspect "$NETWORK" >/dev/null 2>&1 || sudo docker network create "$NETWORK"

echo "2) Conectando $CADDY_CONTAINER a '$NETWORK' (si no lo está ya)..."
if ! sudo docker inspect "$CADDY_CONTAINER" --format '{{json .NetworkSettings.Networks}}' | grep -q "\"$NETWORK\""; then
  sudo docker network connect "$NETWORK" "$CADDY_CONTAINER"
  echo "   conectado."
else
  echo "   ya estaba conectado."
fi

echo "3) Verificando el bloque de sitio para $DOMAIN en el Caddyfile..."
if sudo docker exec "$CADDY_CONTAINER" grep -q "$DOMAIN" /etc/caddy/Caddyfile; then
  echo "   ya existe, no se toca."
else
  sudo docker exec "$CADDY_CONTAINER" sh -c "cat >> /etc/caddy/Caddyfile <<EOF

$DOMAIN {
	reverse_proxy $UPSTREAM
}
EOF"
  echo "   agregado. Recargando Caddy sin downtime..."
  sudo docker exec "$CADDY_CONTAINER" caddy reload --config /etc/caddy/Caddyfile --adapter caddyfile
fi

echo
echo "--- Caddyfile actual ---"
sudo docker exec "$CADDY_CONTAINER" cat /etc/caddy/Caddyfile
