# Recruiter chat — Framing de producto

## 1. Propósito

Recruiter chat existe para ayudar a recruiters o hiring managers a entender mejor la experiencia y el encaje profesional de Pablo Laya.

Es una capacidad **secundaria** de V1. Acompaña al producto principal; no lo reemplaza.

## 2. Posicionamiento de producto

JobMatchRAG sigue siendo, primero, un sistema de inteligencia de empleo personal con pipeline de ofertas, scoring y publicación pública.

Recruiter chat se apoya en esa foundation porque:

- vive dentro del mismo portfolio/producto;
- comparte criterios de coste y guardrails;
- no tiene autoridad para redefinir dominio, prioridades ni arquitectura core.

## 3. Alcance permitido

El chat está permitido para responder sobre:

- perfil profesional de Pablo;
- experiencia relevante;
- proyectos, capacidades y contexto profesional presentes en el corpus permitido;
- aclaraciones recruiter-facing que ayuden a evaluar encaje.

Su rol es explicar mejor el perfil, no operar el sistema ni inventar un asesor conversacional universal.

## 4. Fuera de alcance

Esta foundation deja explícitamente fuera de alcance:

- diseño detallado de RAG;
- chunking, embeddings e indexado concretos;
- prompts finales y contrato conversacional fino;
- UX visual definitiva del chat;
- automatizaciones complejas de lead capture o workflows de recruiting.

Si alguien quiere meter todo eso acá, está mezclando foundation de producto con detalle de implementación. NO corresponde todavía.

## 5. Boundary del corpus

Recruiter chat solo puede responder desde el **corpus permitido** y el contexto profesional de Pablo.

### Reglas del boundary

- no responde desde conocimiento general como si fuera fuente autorizada del perfil;
- no inventa experiencia, logros o disponibilidad;
- no extrapola más allá de la evidencia disponible;
- no usa el pipeline de ofertas como excusa para hablar del perfil sin soporte.

## 6. Política de rechazo

Cuando el contexto sea insuficiente, el chat debe decirlo de forma explícita.

### Base mínima de rechazo

- si falta evidencia, rechaza especular;
- si la pregunta sale del corpus permitido, lo comunica;
- si la respuesta exigiría inventar detalles, prioriza honestidad sobre fluidez.

La calidad del chat no se mide por “responder siempre”, sino por responder con criterio.

## 7. Guardrails operativos

Recruiter chat depende de la misma disciplina operativa del resto del sistema.

- su uso y coste deben ser observables;
- su degradación ocurre antes que la ingesta, el scoring, el dashboard o Telegram;
- no abre una superficie administrativa nueva;
- no puede imponer requisitos arquitectónicos al core del producto.

## 8. Dependencia de documentos foundation

Este documento no vive aislado. Depende explícitamente de:

- `docs/PRD-JobMatchRAG.md` para su rol secundario dentro de V1;
- `docs/architecture/system-overview.md` para su posición como capacidad separada del core;
- `docs/architecture/scoring-foundation.md` para recordar que el valor principal sigue siendo el pipeline de matching;
- `docs/operations/policies-and-controls.md` para degradación, protección y límites operativos.

## 9. Qué deben respetar los cambios verticales futuros

Todo trabajo posterior sobre recruiter chat debe respetar esta foundation:

- sigue siendo una capacidad secundaria;
- responde solo desde el corpus permitido;
- rechaza especulación cuando falta contexto;
- se degrada antes que el core del producto;
- no redefine la arquitectura ni las prioridades de V1.

El diseño detallado de corpus, retrieval y experiencia conversacional vendrá después, pero sobre ESTA base.
