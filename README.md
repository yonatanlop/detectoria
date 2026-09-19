# DetectorIA

Aplicación web para subir documentos (TXT, PDF, DOCX) y estimar, combinando
varias fuentes de análisis independientes, la probabilidad de que el texto
haya sido generado por IA. Pensada para texto en **español**, 100% con
software libre y modelos gratuitos, corriendo en contenedores sobre el
**Always Free tier de Oracle Cloud**.

## ⚠️ Importante

Esto da un **indicador probabilístico, no una prueba**. Los detectores de
texto generado por IA tienen falsos positivos reales, especialmente con
escritores no nativos o texto muy editado. No lo uses como única evidencia
para una decisión académica o disciplinaria.

## Fuentes de análisis

| Fuente | Método | Costo |
|---|---|---|
| A. Estilometría | Heurísticas (burstiness de oraciones, riqueza de vocabulario, puntuación, repetición) | Sin modelo, gratis |
| B. Perplejidad/burstiness | LM en español (`mrm8488/spanish-gpt2`) | Modelo abierto, gratis |
| C. Rank/entropía de tokens | Estilo GLTR, reutiliza el forward pass de la fuente B | Sin costo adicional |
| D. Traducción + clasificador EN | `Helsinki-NLP/opus-mt-es-en` + `roberta-base-openai-detector` | Modelos abiertos, gratis (activada en el despliegue; togglable con `ENABLE_TRANSLATION_CLASSIFIER`) |

Ver el detalle de diseño y las limitaciones de cada fuente en los docstrings
de `backend/app/detectors/`.

## Estructura

```
DetectorIA/
├── backend/     # FastAPI + modelos (Python)
├── frontend/    # React + Vite (SPA)
├── deploy/oci/  # Pasos de despliegue en Oracle Cloud Always Free
└── docker-compose.yml
```

## Desarrollo local

**Backend** (requiere Python 3.11+):

```bash
cd backend
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend**:

```bash
cd frontend
npm install
npm run dev
```

El dev server de Vite (puerto 5173) hace proxy de `/api` hacia el backend
(puerto 8000).

## Todo el stack con Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Abrí `http://localhost/`.

## CI/CD

`.github/workflows/build-images.yml` compila y publica las imágenes en GHCR
(`ghcr.io/yonatanlop/detectoria-backend` y `-frontend`) en cada push a `main`.
El backend se compila solo para `arm64` (única arquitectura de despliegue);
el frontend para `amd64`+`arm64`.

## Despliegue en Oracle Cloud

- VM nueva y dedicada: [`deploy/oci/README.md`](deploy/oci/README.md).
- VM que ya corre otro proyecto con su propio Caddy en 80/443 (caso actual):
  [`deploy/shared-caddy.md`](deploy/shared-caddy.md), usando
  `docker-compose.deploy.yml` (imágenes ya construidas, sin build en el
  servidor).

## Validación de exactitud

[`validation/`](validation/README.md) tiene un set de textos de autoría
conocida (humana verificada vs. IA) y un script para medir la exactitud real
del ensemble contra un despliegue en vivo, en vez de calibrar a ojo con un
solo documento o contra otra herramienta de terceros.
