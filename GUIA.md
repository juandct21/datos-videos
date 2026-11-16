# Guía del video diario — "¿Sabías que…?"

Esta guía la sigue la tarea programada de cada día. El canal publica en español un dato curioso del mundo por día, en un video vertical de ~60 s con voz y animaciones sincronizadas.

## Cuentas y datos fijos
- **Instagram:** frutiverso.oficial2. Se publica con Windsor.ai (conector `instagram`, cuenta `17841417122034870`, acción `create_video_post`).
- **TikTok:** el dueño lo sube a mano. Solo se le entrega el video y el texto.
- **Hosting del video:** este repositorio (público). Archivo en `videos/AAAA-MM-DD-tema.mp4`, enlace público:
  `https://raw.githubusercontent.com/juandct21/datos-videos/main/videos/AAAA-MM-DD-tema.mp4`
- **Voz:** Speko `audio.synthesize`, voz Cartesia "Dario" `35b2cfc1-e6fb-4d69-a598-c1780612be4a`, con
  `constraints.allowedProviders.tts = ["cartesia:sonic-3.5"]` e `intent = {language: "es", optimizeFor: "accuracy"}`.
- **Hora:** el video debe quedar publicado hacia las 7:00 PM (America/Chicago).

## Paso a paso
1. **Tema del día:** búscalo en `temas.md` por la fecha de hoy (America/Chicago). Si no hay, elige uno nuevo que no esté en `publicados.md`: curioso, no genérico, con un "porqué" claro.
2. **Verifica los datos** con WebSearch antes de escribir nada. Ajusta cualquier dato dudoso; no inventes cifras. Si un detalle es discutido, dilo en el guion ("según la versión más conocida…").
3. **Guion:** 6 partes, unas 150 palabras en total (~60 s):
   gancho "¿Sabías que…?" → contexto → dato fuerte con números → el porqué → detalle sorprendente → cierre con un dato extra y "Síguenos para otro dato mañana."
   En el texto para la voz, escribe los números con palabras ("novecientos setenta y nueve").
4. **Voz:** genera cada parte por separado con Speko. El WAV llega guardado en disco (la ruta aparece en el resultado de la herramienta). Después pasa cada parte por `audio.transcribe` (language `es`, `word_timestamps: true`, con el enlace firmado que devuelve la síntesis). Así obtienes el momento exacto de cada palabra y compruebas que la pronunciación esté bien.
5. **Video:** toma `plantilla/make_salto_angel.py` como base de estilo y escribe un script nuevo para el tema:
   - 1080×1920, 30 fps; mismo fondo, colores (amarillo `#FFD23F`, navy), tipografía Inter Display, pastilla "DATO DEL DÍA" y barra de progreso arriba.
   - Duración de cada escena = duración de su audio + 0.5 s. El audio empieza 0.15 s después del inicio de la escena.
   - Cada animación aparece en el momento de su palabra (inicio de la palabra + 0.15 s).
   - Ilustraciones dibujadas con código (mapas simples, íconos, gráficas, contadores). No uses fotos de internet, personajes ni logos de marcas.
   - Mantén el texto importante entre y = 200 y y = 1550 (abajo lo tapa la interfaz de Reels y TikTok).
   - Antes de renderizar, revisa algunos fotogramas como imagen.
   - Renderiza una escena por archivo, únelas con concat y agrega el audio igual que en `plantilla/mk_audio_ejemplo.sh` (adelay + amix + loudnorm a −14 LUFS, AAC 192k).
6. **Publica el video:** cópialo a `videos/`, haz commit y push a `main` en este repositorio (con `-c push.negotiate=true`).
7. **Instagram:** publica con Windsor `execute_action` → `create_video_post`, con `video_url` = enlace raw, `caption` = texto de Instagram y `share_to_feed: true`.
   Si falla, no reintentes en bucle: avisa al dueño y entrégale el video para que lo suba a mano.
8. **Registro:** agrega una línea en `publicados.md` (fecha, tema, archivo y si Instagram salió bien) y haz commit y push.
9. **Entrega al dueño:** envíale el video con SendUserFile y, en un solo mensaje:
   - si Instagram quedó publicado o no;
   - el texto para TikTok, listo para copiar;
   - el título y la descripción para YouTube Shorts.

## Textos de publicación
- **Instagram:** gancho en la primera línea + 1 o 2 líneas con el dato + una pregunta para comentar + "🎙️ Voz generada con IA" + 4 a 6 hashtags (generales como #DatosCuriosos #SabíasQue, más los del tema).
- **TikTok:** más corto, con palabras clave del tema en la frase (en TikTok se busca como en Google), una pregunta y 3 a 5 hashtags.
- **YouTube Shorts:** título de menos de 60 caracteres con gancho + descripción de 2 líneas + 3 hashtags.

## Reglas
- Nada de temas políticos polémicos, tragedias recientes ni datos sin verificar.
- Si no se puede completar algún paso, explica cuál y entrega lo que haya quedado listo.
