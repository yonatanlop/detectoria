# Despliegue en Oracle Cloud (Always Free)

> **Nota**: esta guía asume una VM nueva y dedicada, construyendo la imagen
> del backend directamente ahí (`docker compose up -d --build`). El despliegue
> real actual de DetectorIA usa una VM que **ya tenía otro proyecto corriendo**
> (con su propio Caddy ocupando los puertos 80/443), con las imágenes
> pre-construidas por GitHub Actions en vez de compilarse en el servidor. Para
> ese escenario, ver [`../shared-caddy.md`](../shared-caddy.md) y usar
> `docker-compose.deploy.yml` en lugar de `docker-compose.yml`. Esta guía sigue
> siendo válida tal cual si en algún momento se despliega en una VM limpia sin
> nada más corriendo.

Estos pasos usan exclusivamente recursos **Always Free** de OCI. Verificá al
momento de desplegar que Oracle no haya vuelto a cambiar los límites (en 2026
redujeron el Ampere A1 de 4 OCPU/24GB a **2 OCPU / 12 GB** por tenancy).

## 1. Crear la VM

1. En la consola de OCI: **Compute → Instances → Create Instance**.
2. Shape: `VM.Standard.A1.Flex`, con **2 OCPU / 12 GB** (todo el Always Free
   disponible en una sola VM).
3. Imagen: **Canonical Ubuntu 22.04 (aarch64)**.
4. Boot volume: 50GB (dentro del límite gratuito de 200GB boot+block combinado).
5. Agregá tu clave SSH pública.

## 2. Abrir puertos (los dos niveles, no solo uno)

**Este es el error más común**: hay que abrir el puerto tanto a nivel de red de
OCI como en el firewall local de la VM. Si solo hacés uno de los dos pasos, la
página no va a cargar aunque "todo parezca bien configurado".

**a) A nivel de red (Security List o NSG):**
Abrí ingreso TCP en los puertos 22 (SSH), 80 (HTTP) y 443 (HTTPS) desde
`0.0.0.0/0` en la Security List de la subnet (o en un Network Security Group
asociado a la instancia).

**b) A nivel de sistema operativo (iptables en la VM):**
Las imágenes Ubuntu de Oracle traen reglas de `iptables` que bloquean todo
salvo el puerto 22 por defecto, además de la Security List de OCI. Conectate
por SSH y ejecutá:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # o: sudo apt install iptables-persistent
```

## 3. Instalar Docker + Compose

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
# cerrá sesión y volvé a entrar por SSH para que el grupo tome efecto
```

## 4. Copiar el proyecto y desplegar

```bash
git clone <tu-repo> DetectorIA
cd DetectorIA
cp .env.example .env   # ajustá ENABLE_TRANSLATION_CLASSIFIER si querés la fuente D

docker compose up -d --build
```

La primera build descarga los pesos de los modelos (~1-2GB) dentro de la
imagen del backend — puede tardar varios minutos en una VM ARM compartida.
Podés seguir el progreso con:

```bash
docker compose logs -f backend
```

## 5. Verificar

Abrí `http://<ip-publica-de-tu-vm>/` desde tu navegador. También podés
chequear el backend directamente:

```bash
curl http://<ip-publica>/api/health
```

## 6. HTTPS (opcional, fase 2)

Sin dominio, la v1 queda en HTTP plano — los documentos subidos viajan sin
cifrar. Si más adelante apuntás un dominio a la IP pública de la VM, se puede
agregar un contenedor `certbot` con el método webroot contra el Nginx
existente para obtener un certificado gratuito de Let's Encrypt y configurar
su renovación automática. Esto queda fuera del alcance de v1.
