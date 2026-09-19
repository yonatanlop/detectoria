# Set de validación

Un set chico de textos de autoría **conocida** para medir la exactitud real
del ensemble, en vez de calibrar contra herramientas de terceros (como
ZeroGPT) que son igual de cajas negras que la nuestra y con falsos positivos
documentados.

## Cómo está armado (y su limitación honesta)

- **`textos/ia/`** (10 archivos): textos genuinamente generados por IA (los
  escribió Claude para este set), variados en tema, longitud y registro —
  desde texto "genérico de IA" clásico (marketing, explicación educativa)
  hasta intentos deliberados de sonar más natural/casual (un correo laboral,
  una anécdota personal simulada), para ver si el ensemble los sigue
  detectando o si el estilo casual lo engaña.
- **`textos/humano/`** (9 archivos): textos de dominio público de autoría
  humana verificada, con registros variados a propósito:
  - Formal/político-histórico: Simón Bolívar (*Carta de Jamaica*, 1815),
    José Martí (*Nuestra América*, 1891), preámbulo de la Constitución de
    Colombia (1991).
  - Narrativo/literario: Cervantes (*Quijote*, 1605), Ricardo Palma
    (*Tradiciones peruanas*, 1877), Iriarte (fábula *El burro flautista*, 1782).
  - Ensayo/opinión conversacional: Larra (*El castellano viejo*, 1832) —
    el más cercano en tono a un artículo de opinión moderno del set.
  - Divulgación científica: Ramón y Cajal (*Reglas y consejos sobre
    investigación científica*, 1897) — contraste directo con la muestra de
    IA `06_explicacion_educativa.txt`.
  - Sarmiento (*Facundo*, 1845), invocación retórica.

  Todos con texto verificado contra fuentes confiables antes de incluirlos.

**Limitación que sigue vigente**: aun con más variedad de registro, todos
son textos de los siglos XVI-XX — no hay ningún ejemplo de escritura humana
**contemporánea** (un chat, un correo actual, un comentario de foro de 2020
en adelante), que es el registro que más importa para el caso de uso real
(ensayos, tareas, documentos actuales). No lo inventé yo mismo para no
mezclar texto generado por IA disfrazado de "humano casual" dentro del set
de referencia — eso invalidaría la medición. Si querés un set realmente
representativo, sumá 3-5 textos tuyos (algo que hayas escrito vos: un
correo, un mensaje largo, una opinión) como archivos `.txt` nuevos en
`textos/humano/`.

## Cómo correrlo

```bash
pip install requests
python validation/run_validation.py --url https://detectoria.duckdns.org
```

Imprime el score por archivo y fuente, la exactitud global con un umbral de
decisión de 50, y el score medio por fuente y categoría — esto último es lo
más útil para ver qué fuente discrimina mejor y cuál solo agrega ruido.

## Cómo usar los resultados para calibrar

- Si el score medio de `perplexity` en textos humanos es alto, subí
  `_PPL_REFERENCE` en `backend/app/detectors/perplexity.py` (el LM encuentra
  ese texto "predecible" con el umbral actual).
- Si una fuente sistemáticamente no separa humano de IA (medias parecidas en
  ambas categorías), bajá su peso en `backend/app/config.py`
  (`source_weights`) o considerá sacarla del ensemble.
- No ajustes nada con menos de ~20-30 ejemplos por categoría; con el set
  actual (5 y 10) alcanza para detectar errores groseros, no para afinar con
  precisión.
