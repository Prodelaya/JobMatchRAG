# Recruiter Chat — Product Framing

## 1. Purpose

Recruiter chat existe para ayudar a recruiters o hiring managers a entender mejor la experiencia y el encaje profesional de Pablo Laya.

Es una capacidad **secundaria** de V1. Acompaña al producto principal; no lo reemplaza.

## 2. Product Positioning

JobMatchRAG sigue siendo, primero, un sistema de inteligencia de empleo personal con pipeline de ofertas, scoring y publicación pública.

Recruiter chat se apoya en esa foundation porque:

- vive dentro del mismo portfolio/producto;
- comparte criterios de coste y guardrails;
- no tiene autoridad para redefinir dominio, prioridades ni arquitectura core.

## 3. Allowed Scope

El chat está permitido para responder sobre:

- perfil profesional de Pablo;
- experiencia relevante;
- proyectos, capacidades y contexto profesional presentes en el corpus permitido;
- aclaraciones recruiter-facing que ayuden a evaluar encaje.

Su rol es explicar mejor el perfil, no operar el sistema ni inventar un asesor conversacional universal.

## 4. Out of Scope

Esta foundation deja explícitamente fuera de alcance:

- diseño detallado de RAG;
- chunking, embeddings e indexado concretos;
- prompts finales y contrato conversacional fino;
- UX visual definitiva del chat;
- automatizaciones complejas de lead capture o workflows de recruiting.

Si alguien quiere meter todo eso acá, está mezclando foundation de producto con detalle de implementación. NO corresponde todavía.

## 5. Corpus Boundary

Recruiter chat solo puede responder desde el **corpus permitido** y el contexto profesional de Pablo.

### Boundary rules

- no responde desde conocimiento general como si fuera fuente autorizada del perfil;
- no inventa experiencia, logros o disponibilidad;
- no extrapola más allá de la evidencia disponible;
- no usa el pipeline de ofertas como excusa para hablar sin soporte del perfil.

## 6. Refusal Policy

Cuando el contexto sea insuficiente, el chat debe decirlo de forma explícita.

### Refusal baseline

- si falta evidencia, rechaza especular;
- si la pregunta sale del corpus permitido, lo comunica;
- si la respuesta exigiría inventar detalles, prioriza honestidad sobre fluidez.

La calidad del chat no se mide por “responder siempre”, sino por responder con criterio.

## 7. Operational Guardrails

Recruiter chat depende de la misma disciplina operativa del resto del sistema.

- su uso y coste deben ser observables;
- su degradación ocurre antes que la ingesta, scoring, dashboard o Telegram;
- no abre una superficie administrativa nueva;
- no puede imponer requisitos arquitectónicos al core del producto.

## 8. Dependency on Foundation Docs

Este documento no vive aislado. Depende explícitamente de:

- `docs/PRD-JobMatchRAG.md` para su rol secundario dentro de V1;
- `docs/architecture/system-overview.md` para su posición como capacidad separada del core;
- `docs/architecture/scoring-foundation.md` para recordar que el valor principal sigue siendo el pipeline de matching;
- `docs/operations/policies-and-controls.md` para degradación, protección y límites operativos.

## 9. What Future Vertical Changes Must Respect

Todo trabajo posterior sobre recruiter chat debe respetar esta foundation:

- sigue siendo capacidad secundaria;
- responde solo desde corpus permitido;
- rechaza especulación cuando falta contexto;
- sufre degradación antes que el core del producto;
- no redefine arquitectura ni prioridades de V1.

El diseño detallado de corpus, retrieval y experiencia conversacional vendrá después, pero sobre ESTA base.
