# Integración con el Caddy compartido de otro proyecto

Esta VM ya corre otro proyecto (`gamificacion-fundacion`) cuyo contenedor
`caddy` es el único proceso escuchando en los puertos 80/443 de la IP pública,
sirviendo `gamificaciones.duckdns.org` con HTTPS automático. Solo un proceso
puede escuchar en esos puertos, así que DetectorIA no puede traer su propio
Caddy en 80/443 — tiene que sumarse al que ya existe.

**Decisión explícita**: no se modifica el repositorio ni el `docker-compose`
de `gamificacion-fundacion`. En su lugar, `deploy/patch-shared-caddy.sh` hace
dos cosas en caliente sobre el contenedor `caddy` que ya está corriendo:

1. Lo conecta a una red Docker nueva y compartida (`edge`), sin desconectarlo
   de la suya propia — el sitio existente sigue funcionando exactamente igual.
2. Le agrega un segundo bloque de sitio al Caddyfile en ejecución (`docker exec`
   + `caddy reload`, sin reiniciar el contenedor, sin downtime) que enruta
   `detectoria.duckdns.org` hacia `detectoria-frontend:80` en esa red.

## Importante: esto no es persistente

El `docker-compose.prod.yml` de `gamificacion-fundacion` regenera el
Caddyfile desde cero (solo con su propio dominio) cada vez que ese contenedor
arranca. Como no tocamos ese archivo, **si el contenedor `caddy` de ese otro
proyecto se recrea** (un redeploy de `gamificacion-fundacion`, un reinicio de
la VM, etc.), el bloque de DetectorIA se pierde y hay que volver a correr:

```bash
./deploy/patch-shared-caddy.sh
```

Es idempotente — se puede correr las veces que haga falta sin duplicar nada
ni afectar el sitio del otro proyecto.

## Orden de despliegue en la VM

```bash
git clone https://github.com/yonatanlop/detectoria.git
cd detectoria
cp .env.example .env   # ajustar si hace falta

docker compose -f docker-compose.deploy.yml pull
docker compose -f docker-compose.deploy.yml up -d

./deploy/patch-shared-caddy.sh
```

Verificar: `https://detectoria.duckdns.org/` y que
`https://gamificaciones.duckdns.org/` siga funcionando igual que antes.
