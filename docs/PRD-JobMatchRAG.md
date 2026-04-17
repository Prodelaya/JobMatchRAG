# PRD — JobMatchRAG

**Versión:** 1.1  
**Estado:** foundation V1 alineada con specs aceptadas  
**Fecha:** Abril 2026  
**Owner:** Pablo Laya  
**Nombre público:** Pendiente de decidir

---

## 1. Resumen ejecutivo

JobMatchRAG es, ante todo, un sistema personal de inteligencia de empleo para Pablo Laya. Su trabajo principal en V1 es capturar ofertas, filtrar incompatibilidades duras, consolidar duplicados, calcular un score explicable y publicar el resultado como escaparate público del sistema.

El producto combina dos capas, en este orden:

1. **Utilidad real de job hunting:** detectar oportunidades nuevas y relevantes con menos ruido.
2. **Escaparate técnico público:** mostrar cómo se diseña y opera un sistema de automatización e IA aplicada con criterio, trazabilidad y coste controlado.

El recruiter chat existe en V1, pero queda explícitamente como **capacidad secundaria**. No redefine el producto ni desplaza el flujo principal de ofertas.

---

## 2. Problema

Los portales generalistas meten demasiado ruido para una búsqueda como la de Pablo, donde importa más la naturaleza real del rol que el título exacto. El sistema necesita distinguir si la oferta encaja con trabajo interno, automatización e IA aplicada, sin depender solo de keywords literales.

Además, Pablo necesita que esa búsqueda útil sirva también como prueba pública de criterio técnico, arquitectura y ejecución real.

---

## 3. Framing del producto V1

### 3.1 Objetivo principal

Operar como **personal job intelligence first**: las ofertas compatibles pasan filtros duros, reciben scoring y se publican en un dashboard público. Las alertas por Telegram se reservan para oportunidades nuevas con score suficiente.

### 3.2 Usuario principal

**Pablo Laya** es el usuario principal y el sujeto del matching. El sistema está optimizado para sus criterios reales, no para un marketplace multiusuario.

### 3.3 Usuarios secundarios

- **Recruiters / hiring managers:** consultan el dashboard público y, de forma secundaria, usan el recruiter chat para entender experiencia y encaje.
- **Visitantes públicos:** observan la actividad, frescura y lógica general del sistema como pieza viva de portfolio.

### 3.4 Promesa de producto

El sistema debe responder dos preguntas simples:

- **¿Qué ofertas valen la pena para Pablo ahora?**
- **¿Qué demuestra este sistema sobre cómo Pablo diseña automatización e IA aplicada?**

---

## 4. Alcance funcional V1

### 4.1 Dentro de alcance

- ingesta de ofertas bajo un contrato común de fuentes;
- `capture profile` canónica y bilingüe para búsqueda/captura, con pushdown al proveedor solo como optimización;
- pipeline canónico `source -> raw -> normalized -> canonical -> eligibility -> scored -> published/notified`;
- filtros de elegibilidad antes del scoring;
- consolidación de oferta canónica con evidencia por fuente;
- scoring híbrido: reglas primero y ajuste LLM acotado después;
- dashboard público de lectura con visibilidad de ofertas aptas para publicación;
- disclosure de frescura/actividad en la superficie pública;
- alertas por Telegram solo para **nuevas** oportunidades con **score >= 70**;
- superficie administrativa mínima, separada y protegida para operar runs y reprocesos;
- recruiter chat acotado al contexto profesional de Pablo.

### 4.2 Fuera de alcance en esta foundation

- diseño detallado de RAG, chunking, prompts o UX completa del chat;
- implementación multi-candidate real;
- API pública;
- microservicios;
- UI operativa pública para acciones internas;
- detalle público completo de razones internas de scoring, trazabilidad o red flags;
- automatizaciones de candidatura, favoritos, notas manuales u overrides complejos.

---

## 5. Visibilidad pública y reglas de publicación

### 5.1 Dashboard público

El dashboard es público y representa la salida visible del flujo principal. Debe mostrar ofertas ya evaluadas para lectura simple, con foco en utilidad y transparencia general del sistema.

### 5.2 Frescura y visibilidad

- la vista pública debe dejar clara la **frescura** de los datos;
- la experiencia por defecto debe priorizar actividad reciente;
- el histórico completo se conserva internamente aunque la navegación pública privilegie lo reciente.

### 5.3 Alertas por Telegram

- solo se envían para **apariciones nuevas**;
- el umbral base de disparo es **score >= 70**;
- un mismo evento publicable no debe duplicar alertas sin una nueva oportunidad real.

---

## 6. Recruiter chat como capacidad secundaria

El recruiter chat existe para ayudar a recruiters a entender experiencia, proyectos y encaje profesional de Pablo, pero no es el núcleo del producto.

Reglas base:

- responde solo desde contexto del perfil y corpus permitido de Pablo;
- no especula si falta evidencia;
- debe decir explícitamente cuando no tiene suficiente contexto;
- su coste y uso se degradan antes que la ingesta, el scoring, el dashboard o Telegram.

---

## 7. Criterios base de elegibilidad y scoring

### 7.1 Filosofía de matching

El sistema debe priorizar:

1. trabajo interno real;
2. automatización útil;
3. IA aplicada con valor concreto;
4. compatibilidad de seniority, modalidad y geografía;
5. stack/lenguaje como señal complementaria, no dominante.

### 7.2 Reglas base cerradas

- las incompatibilidades claras se rechazan **antes** del scoring;
- la fórmula por reglas corre primero;
- el ajuste LLM, si existe, es una segunda capa acotada;
- la evidencia explícita vale más que la inferida;
- `buena` cubre score **70-84**;
- `prioritaria` cubre score **85-100**.

---

## 8. Foundation técnica y operativa

- backend base: **Python + FastAPI**;
- procesamiento asíncrono/background: **Celery desde V1**;
- forma del sistema: **modular monolith**;
- admin y operaciones protegidas, separadas de rutas públicas;
- retención diferenciada por clase de dato, no un único TTL global;
- observabilidad mínima sobre runs, fallos, alertas y uso de LLM/chat.

---

## 9. Fuentes y política inicial

### 9.1 Fuente inicial de producción

La primera fuente de producción cerrada para V1 es **InfoJobs official API**. Otras fuentes quedan para verticales posteriores bajo el mismo contrato común de adapters.

### 9.2 Política de filtrado

Se permite filtrar del lado de la fuente para reducir ruido, pero eso no reemplaza la elegibilidad interna: el filtro duro propio sigue siendo la autoridad antes del scoring. En V1 la semántica de búsqueda/captura vive en una `capture profile` canónica; el proveedor recibe params derivados mediante un mapper auditable y los filtros no soportados (por ejemplo AVE-friendly hybrid o consultoría/body-shopping) se resuelven post-fetch dentro de JobMatchRAG. Los params del portal son artefactos de ejecución, no definición del producto.

---

## 10. Principios del producto

1. **Utilidad real antes que demo vacía**.
2. **Foundation transversal antes que verticales nuevas**.
3. **Trazabilidad por etapas antes que shortcuts mágicos**.
4. **Público como escaparate; privado solo para operar**.
5. **Coste controlado y degradación explícita**.
6. **Explicabilidad suficiente sin exponer internals sensibles**.

---

## 11. Decisiones todavía abiertas

- nombre público definitivo del producto;
- ubicación exacta del recruiter chat dentro de la experiencia pública;
- profundidad y cadencia de métricas públicas más allá de frescura/actividad básica;
- diseño detallado del stack RAG y su contrato conversacional fino.
