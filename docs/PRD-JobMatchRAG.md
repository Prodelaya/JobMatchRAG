# PRD — JobMatchRAG
**Versión:** 1.0  
**Estado:** Definición base cerrada  
**Fecha:** Abril 2026  
**Owner:** Pablo Laya  
**Nombre público:** Pendiente de decidir  
**Naturaleza del producto:** Herramienta real de uso personal + escaparate público de automatización e IA aplicada

---

## 1. Resumen ejecutivo

JobMatchRAG es un sistema personal de inteligencia de empleo diseñado para detectar, consolidar, rankear y mostrar públicamente ofertas de trabajo alineadas con el perfil profesional y los criterios reales de Pablo Laya.

El producto tiene dos objetivos simultáneos:

1. **Utilidad real de búsqueda de empleo:** reducir ruido, detectar nuevas oportunidades relevantes y avisar solo cuando una nueva aparición supere un umbral de interés.
2. **Escaparate técnico y profesional:** demostrar públicamente cómo Pablo piensa, diseña y construye sistemas de automatización e IA aplicada.

El producto combinará:
- ingesta automatizada de múltiples portales de empleo,
- normalización y deduplicado,
- scoring híbrido basado en reglas + ajuste LLM,
- dashboard público con todas las ofertas capturadas,
- chatbot recruiter-facing basado en RAG,
- alertas por Telegram para oportunidades nuevas de score alto.

---

## 2. Problema

Los portales de empleo generalistas no resuelven bien búsquedas muy específicas como la de Pablo, donde importan más el **tipo real de problema que resuelve el rol** y el **contexto de uso interno** que el título o el lenguaje exacto.

Los problemas concretos a resolver son:

- demasiado ruido en los portales generalistas;
- mala detección de ofertas que encajan por naturaleza del rol, aunque no usen las palabras exactas;
- dificultad para distinguir entre:
  - herramientas internas vs producto externo,
  - automatización aplicada vs desarrollo genérico,
  - IA útil vs humo,
  - rol interno real vs consultoría/bodyshopping;
- dificultad para contar bien el perfil profesional solo con CV/LinkedIn;
- ausencia de una pieza viva de portfolio que demuestre criterio técnico, arquitectura, automatización e IA aplicada.

---

## 3. Objetivo del producto

### 3.1 Objetivo principal
**Demostrar públicamente cómo Pablo piensa y construye**, mediante un sistema real que además le sirve para buscar empleo mejor.

### 3.2 Objetivos funcionales
- Consolidar ofertas de empleo desde múltiples fuentes.
- Rankear ofertas según criterios reales de encaje.
- Notificar nuevas apariciones que superen un umbral configurable.
- Exponer públicamente el listado completo de ofertas capturadas.
- Ofrecer un chatbot que responda preguntas sobre la experiencia, proyectos y encaje profesional de Pablo.
- Permitir a un recruiter pegar una oferta y preguntar por qué Pablo encaja o no.

### 3.3 Objetivos de posicionamiento
- Presentar el sistema como:
  - herramienta personal de job hunting,
  - motor de matching experimental,
  - y sobre todo **escaparate de automatización + IA aplicada**.

---

## 4. Perfil de usuario y contexto

### 4.1 Usuario principal
**Pablo Laya**

Perfil resumido:
- Junior con experiencia real.
- Foco en automatización, productividad interna, bots, integraciones e IA aplicada.
- Stack principal real: Python.
- Abierto a otros lenguajes si el rol encaja en lo importante.
- Busca aumentar productividad de empleados internos mediante software, automatización e IA.

### 4.2 Usuarios secundarios
1. **Recruiters / hiring managers**
   - Quieren entender experiencia real, proyectos y encaje.
2. **Visitantes públicos**
   - Quieren ver el sistema, su lógica y el tipo de oportunidades detectadas.

### 4.3 Perfil no contemplado como usuario independiente
No se define un cuarto usuario específico “empresa interesada”, porque ese caso queda cubierto mediante:
- CV,
- dashboard público,
- chatbot recruiter.

---

## 5. Propuesta de valor

### 5.1 Valor para Pablo
- reduce ruido;
- reduce tiempo de revisión;
- aumenta probabilidad de encontrar ofertas realmente alineadas;
- convierte la búsqueda de empleo en un sistema de automatización útil.

### 5.2 Valor para recruiters
- permite entender experiencia real más allá del CV;
- ofrece una forma rápida de preguntar por proyectos, stack y encaje;
- demuestra capacidad real de diseño, integración y ejecución.

### 5.3 Valor como portfolio
- demuestra scraping, integración, scoring, RAG, botificación, backend, despliegue y criterio de producto;
- enseña un sistema vivo y no un portfolio estático.

---

## 6. Alcance del producto

## 6.1 Dentro de alcance
- agregación de ofertas de múltiples portales;
- normalización y oferta canónica;
- deduplicado;
- detección de republicaciones;
- scoring híbrido;
- dashboard público;
- chatbot público recruiter-facing;
- persistencia de conversaciones del chatbot;
- panel de administración mínimo;
- alertas por Telegram;
- métricas públicas del sistema.

## 6.2 Fuera de alcance
- seguimiento de candidaturas dentro del sistema;
- guardar ofertas favoritas, notas o estados manuales por oferta;
- aprendizaje automático a partir del feedback del usuario;
- overrides manuales complejos;
- API pública del sistema;
- filtros avanzados complejos en la UI pública;
- páginas públicas de detalle permanentes por oferta.

---

## 7. Principios de producto

1. **Herramienta real antes que demo vacía**
2. **Simple en superficie, seria por debajo**
3. **Explicable sin sobrecargar la UI**
4. **Coste controlado**
5. **Público como escaparate, privado solo para operar**
6. **El contexto del rol importa más que la keyword**
7. **Python suma, pero no manda**

---

## 8. Criterios de encaje del producto

### 8.1 Preferencias profesionales del candidato
Prioridad de mayor a menor:

1. **Uso interno**
2. **IA aplicada**
3. **Automatización**
4. **Stack/lenguaje**
5. **Aceptan juniors / poca experiencia**
6. **Python** como bonus adicional

### 8.2 Regla de lenguaje
- Python puntúa positivamente por ser el stack real más fuerte del candidato.
- No se descarta ningún lenguaje por principio.
- El sistema debe considerar también lo que probablemente quiere la empresa, no solo las preferencias del candidato.
- Un rol puede puntuar muy bien aunque no sea Python-first, si cumple el resto de criterios clave.

---

## 9. Fuentes de ofertas

### 9.1 Fuentes incluidas en V1
- InfoJobs
- Tecnoempleo
- GetOnBoard
- Jooble
- Glassdoor
- Manfred
- Job Today

### 9.2 Frecuencia de refresco
- Cada **6 horas** para todas las fuentes.

### 9.3 Política de histórico
- Se guardará **histórico completo de ofertas canónicas/normalizadas**.
- Las ofertas expiradas o inactivas no se borrarán del histórico.
- Los snapshots/raw podrán tener retención técnica distinta para controlar crecimiento.

---

## 10. Reglas de compatibilidad geográfica y modalidad

### 10.1 Reglas definidas
- **Madrid:** presencial o híbrido, aceptable.
- **Fuera de Madrid:** híbrido solo si exige **máximo 2 días presenciales al mes** y la ciudad tiene **AVE**.
- **Remoto 100%:** aceptable desde cualquier parte del mundo **si el idioma de trabajo es español**.

### 10.2 Implicaciones
El sistema debe evaluar:
- ciudad,
- país,
- modalidad,
- frecuencia presencial,
- idioma de trabajo.

No debe tratar ubicación como un filtro plano.

---

## 11. Modelo funcional de oferta

### 11.1 Oferta canónica
Cuando la misma oferta aparezca en varias fuentes:
- se creará una **única oferta canónica**;
- se mostrarán también las **fuentes detectadas** asociadas.

### 11.2 URL principal
La URL principal mostrada será la del **portal de empleo más fiable/limpio**.

### 11.3 Republicaciones
Si una empresa republica la misma oferta dos semanas después:
- se tratará como **una nueva oportunidad distinta**.

### 11.4 Empresa canónica
El sistema intentará unificar automáticamente empresas con nombres ligeramente distintos cuando el contexto lo sostenga:
- nombre similar,
- descripción,
- ubicación,
- condiciones,
- dominio,
- similitud general.

---

## 12. Scoring

## 12.1 Enfoque general
El scoring será **híbrido**:

- **capa 1:** fórmula fija con pesos manuales;
- **capa 2:** ajuste LLM.

### 12.2 Justificación
La fórmula fija aportará:
- estabilidad,
- coste bajo,
- control,
- consistencia.

El LLM aportará:
- inferencia semántica,
- detección de encaje implícito,
- matices sobre naturaleza del rol.

### 12.3 Reglas clave
- El sistema debe puntuar mejor las señales **explícitas** que las **inferidas**.
- El encaje implícito detectado por LLM **sí debe sumar**, pero con **prudencia**.
- La oferta puede puntuar por encaje implícito aunque no diga literalmente “automatización interna” o “IA aplicada”.

### 12.4 Estados de decisión
Además del score numérico, cada oferta tendrá uno de estos estados:
- `prioritaria`
- `revisar`
- `descartar`

### 12.5 Presentación del scoring
- El motor interno será más rico que una simple nota.
- La presentación pública estándar mostrará:
  - **score final**
  - **estado**
  - datos básicos de la oferta
- No se mostrará públicamente el desglose interno completo por componentes.

---

## 13. Requisitos funcionales — Ingesta

### 13.1 Captura
El sistema debe:
- consultar cada fuente cada 6 horas;
- obtener nuevas apariciones;
- persistir raw y versión normalizada;
- evitar reingestas innecesarias si no hay cambios relevantes.

### 13.2 Normalización mínima
Cada oferta debe poder mapearse como mínimo a:
- título
- empresa
- ubicación
- modalidad
- salario anual, si existe
- descripción
- URL
- fecha
- portal fuente
- idioma, si se puede inferir
- metadatos de captura

### 13.3 Histórico
Las ofertas pasadas deben conservarse para:
- análisis de tendencias,
- comparación de salarios,
- deduplicado,
- visibilidad histórica,
- valor de portfolio.

---

## 14. Requisitos funcionales — Dashboard público

### 14.1 Naturaleza
El dashboard principal será **público**.

### 14.2 Contenido mínimo visible por oferta
Cada oferta mostrará al menos:
- resumen corto
- scoring
- nombre de la compañía
- salario anual, si aparece
- modalidad: híbrido / presencial / remoto
- ubicación
- URL de la oferta

### 14.3 Alcance público
- Se mostrarán **todas las ofertas capturadas públicamente**.
- No habrá ranking público por categorías.
- No habrá páginas públicas de detalle permanentes por oferta.
- La navegación pública será de **lectura simple** con **ordenación por columnas**.

### 14.4 Qué no se mostrará públicamente
- red flags detallados;
- motivos negativos;
- trazabilidad interna;
- componentes internos del scoring.

### 14.5 Métricas públicas
Sí se mostrarán métricas públicas del sistema, por ejemplo:
- ofertas procesadas,
- fuentes activas,
- número total capturado,
- actividad reciente,
- otras métricas simples del funcionamiento general.

---

## 15. Requisitos funcionales — Chatbot recruiter

### 15.1 Objetivos
El chatbot debe:
1. responder preguntas sobre experiencia y proyectos;
2. vender a Pablo como candidato;
3. demostrar la calidad técnica del sistema.

### 15.2 Tono
- formal,
- recruiter-friendly,
- amistoso,
- no robótico.

### 15.3 Preguntas permitidas
- experiencia laboral;
- proyectos;
- stack;
- experiencia técnica;
- por qué encaja Pablo en determinados roles;
- análisis de una oferta pegada por un recruiter para responder por qué encaja o no.

### 15.4 Preguntas bloqueadas
- preguntas no relacionadas con Pablo o con su encaje profesional;
- preguntas abusivas o absurdamente largas;
- intentos de prompt injection;
- intentos de sacar al bot de su función;
- peticiones de escribir código o resolver tareas no relacionadas con Pablo;
- preguntas personales no laborales.

### 15.5 Fuentes del chatbot
El chatbot podrá usar:
- CV
- portfolio / web
- README
- documentación técnica
- experiencia laboral
- LinkedIn o equivalente manual
- código y tests seleccionados

### 15.6 Corpus
Desde el inicio entrarán en el corpus:
- CV
- portfolio / web
- README y documentación
- experiencia laboral
- LinkedIn/equivalente
- código y tests seleccionados

### 15.7 Selección del corpus
- Ingesta automática de todo lo público.
- Se permitirá una **lista negra de exclusiones** para mejorar calidad.
- El corpus deberá incorporar **timestamps/metadatos temporales** para poder hablar de progreso y evolución.

### 15.8 Refresco del corpus
- Solo manual.
- Debe existir en admin un botón simple de **recargar / reindexar** el corpus.

### 15.9 Persistencia de conversaciones
- El sistema debe **guardar conversaciones del chatbot**.
- La persistencia deberá incluir al menos:
  - sesión,
  - mensajes,
  - fecha/hora,
  - identificador anónimo técnico,
  - métricas de uso básicas.

### 15.10 Límites de uso
- Límite por usuario anónimo: **10 preguntas al día**.
- Protección: **rate limit por IP/sesión**, sin captcha ni login obligatorio.
- No habrá API pública del chatbot; solo interfaz web.

### 15.11 Ubicación del chatbot en la web
Queda abierta una decisión de UX:
- vivir solo dentro de la página del producto;
- o también como elemento flotante en toda la web.

---

## 16. Requisitos funcionales — Alertas Telegram

### 16.1 Tipo de alerta
Solo habrá alertas de:
- **nuevas apariciones** con score superior al umbral configurado.

### 16.2 Umbral
- Será configurable manualmente.
- El valor exacto queda pendiente de definir.

### 16.3 Formato
- Alertas **siempre individuales**.
- No habrá agrupación.

### 16.4 Exclusiones manuales
- No se contemplan silencios manuales por empresa, keyword o rol.

---

## 17. Requisitos funcionales — Panel de administración

### 17.1 Naturaleza
El panel de administración será privado.

### 17.2 Acciones permitidas
Desde el panel se podrá:
- lanzar scrapers;
- recargar corpus/chat;
- cambiar umbral de alertas;
- cambiar pesos de scoring.

### 17.3 Acciones no contempladas
- overrides manuales de ofertas/empresas;
- blacklists/whitelists complejas;
- versionado de prompts;
- versionado de pesos.

---

## 18. Requisitos no funcionales

### 18.1 Coste
- objetivo ideal mensual: **5 €**
- máximo mensual: **10 €**

### 18.2 Política de degradación si se acerca al límite
Lo primero que debe degradarse es:
- **el chatbot público**

Antes de degradar:
- scoring de ofertas;
- frecuencia de scraping;
- ingestión.

### 18.3 Filosofía coste/calidad
- Se prioriza **equilibrio entre calidad y coste**.

### 18.4 Disponibilidad
- No se exige SLA formal.
- Se espera funcionamiento doméstico estable sobre infraestructura propia.

### 18.5 Seguridad
- Solo exposición web a través de la infraestructura existente.
- Sin API pública abierta.
- Con rate limiting para chatbot.

---

## 19. Arquitectura de alto nivel

## 19.1 Principio
Arquitectura de **producto single-candidate**, con ligera preparación para futura evolución a multi-candidate sin sobreingeniería.

### 19.2 Componentes lógicos
1. **Módulo de ingesta de fuentes**
2. **Módulo de normalización y canonicidad**
3. **Módulo de scoring**
4. **Módulo de dashboard público**
5. **Módulo de chatbot recruiter**
6. **Módulo de alertas Telegram**
7. **Panel de administración**

### 19.3 Separación pública/privada
**Público**
- listado de ofertas
- score final
- métricas públicas
- chatbot

**Privado**
- lanzar scrapers
- recargar corpus
- tocar pesos
- tocar umbral de alertas

### 19.4 Integración web
El producto vivirá integrado en `prodelaya.dev`, sin rehacer toda la web.

---

## 20. Modelo de datos de alto nivel

Entidades principales esperadas:

- `candidates`
- `sources`
- `source_runs`
- `raw_offers`
- `canonical_offers`
- `offer_sources`
- `companies`
- `offer_scores`
- `offer_status`
- `candidate_documents`
- `candidate_chunks`
- `chat_sessions`
- `chat_messages`
- `telegram_notifications`

### 20.1 Multi-candidate light
Aunque el producto es de un solo candidato, el diseño debe permitir en futuro:
- introducir `candidate_id`,
- separar claramente perfil/corpus/ofertas.

Sin multiusuario real en esta fase.

---

## 21. Flujos principales

### 21.1 Flujo de oferta
1. Captura desde portal
2. Persistencia raw
3. Normalización
4. Dedupe
5. Creación o actualización de oferta canónica
6. Cálculo de score base
7. Ajuste LLM
8. Clasificación (`prioritaria`, `revisar`, `descartar`)
9. Publicación en dashboard
10. Alerta Telegram si nueva aparición + supera umbral

### 21.2 Flujo de chatbot
1. Usuario pregunta
2. Control de rate limit
3. Recuperación de contexto desde corpus
4. Respuesta del modelo
5. Persistencia de conversación
6. Devolución de respuesta

### 21.3 Flujo de recarga de corpus
1. Acción manual desde admin
2. Relectura de fuentes documentales
3. Rechunking/reindexado
4. Sustitución segura del índice activo

---

## 22. Orden de construcción

### 22.1 Primer bloque a construir
- **Ingestión de ofertas**

### 22.2 Bloques críticos
El producto no se considera realmente existente hasta tener:
- ingesta,
- scoring,
- dashboard,
- chatbot.

### 22.3 Restricción de roadmap
- No hay deadline.
- No se aceptan recortes por presión temporal.
- Sí habrá orden de implementación, pero no reducción del alcance completo deseado.

---

## 23. Métricas de éxito

El sistema se considerará exitoso si:
1. **ahorra tiempo** de revisión;
2. **reduce ruido** y trae ofertas realmente interesantes;
3. **mejora opciones reales de entrevista/contacto**.

### 23.1 Métrica práctica más importante
- Que la **mayoría de alertas altas merezcan revisión real**.

### 23.2 Métricas públicas
Sí habrá métricas visibles del sistema, pero sin convertir la UI pública en un panel complejo.

---

## 24. Riesgos y mitigaciones

### 24.1 Riesgo: ruido y calidad variable de fuentes
**Mitigación**
- normalización robusta,
- deduplicado,
- score híbrido,
- oferta canónica.

### 24.2 Riesgo: gasto del chatbot
**Mitigación**
- rate limit,
- contexto controlado,
- degradarlo primero si se acerca al límite.

### 24.3 Riesgo: crecimiento del almacenamiento
**Mitigación**
- histórico completo de canónicas,
- política distinta para snapshots/raw/logs.

### 24.4 Riesgo: UI pública demasiado cargada
**Mitigación**
- home simple,
- sin páginas de detalle,
- listado simple con ordenación,
- profundidad en páginas secundarias si hiciera falta.

### 24.5 Riesgo: corpus demasiado amplio y ruidoso
**Mitigación**
- lista negra de exclusiones,
- recarga manual,
- revisión periódica de calidad del corpus.

---

## 25. Decisiones ya cerradas

- nombre público: pendiente;
- umbral exacto de alertas: pendiente;
- ubicación exacta del chatbot en la web: pendiente;
- todo lo demás relevante de producto base: **cerrado**.

---

## 26. Anexo operativo (fuera del alcance funcional estricto del PRD)

> Este apartado no forma parte del comportamiento funcional del producto, pero se incluye como contexto operativo explícito.

### 26.1 Infraestructura disponible
El usuario ya dispone de:

- **Servidor:** MiniPC doméstico
- **CPU:** Intel i5-6500T
- **RAM:** 8 GB
- **Espacio libre:** ~75 GB
- **SO:** Ubuntu 24.04

### 26.2 Infraestructura ya existente
- PostgreSQL 16 corriendo
- Cloudflare Tunnel configurado
- Web actual en `prodelaya.dev`
- Servicios ya existentes que no deben romperse

### 26.3 Presupuesto
- **Presupuesto ideal mensual:** **5 €**
- **Presupuesto máximo mensual:** **10 €**

### 26.4 Implicaciones operativas
- El producto debe diseñarse para ser ligero y razonable en consumo.
- No debe depender de infraestructura cloud cara.
- Debe convivir con el resto de servicios ya desplegados por el usuario.

---
