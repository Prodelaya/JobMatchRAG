# Scoring Foundation — JobMatchRAG

## 1. Purpose

Este documento define la base de matching/scoring de V1. La idea es SIMPLE: primero excluir lo claramente incompatible, después puntuar con reglas auditables y recién al final permitir un ajuste LLM acotado.

No cierra todavía una fórmula numérica detallada ni datasets de calibración fina. Cierra el ORDEN, los límites y el contrato de explicabilidad.

## 2. Decision Order

El flujo base de scoring es:

`eligibility -> rule score -> bounded LLM adjustment -> final classification`

Esto implica cuatro reglas no negociables:

1. una oferta incompatible NO llega al scoring;
2. la primera autoridad de score es una capa de reglas;
3. el LLM nunca reemplaza el score base;
4. la salida final debe seguir siendo explicable.

## 3. Eligibility Gates (Hard Filters)

Antes de puntuar, el sistema debe descartar incompatibilidades claras.

### 3.1 Baseline hard filters

Las causas mínimas de exclusión cerradas para esta foundation son:

- geografía o modalidad incompatibles;
- seniority por encima de 3 años;
- roles incompatibles con el foco real del producto;
- consultoras, salvo que exista evidencia clara de trabajo interno real.

### 3.2 Meaning of hard filters

Los hard filters existen para evitar dos errores clásicos:

- gastar coste analítico en ofertas que ya sabemos que no encajan;
- dejar que un score “bonito” tape una incompatibilidad estructural.

Si falla elegibilidad, la oferta queda fuera del scoring pero mantiene trazabilidad histórica interna con sus razones.

## 4. Rule-Score Baseline

La primera capa positiva de matching es un `ScoreBreakdown` por reglas.

### 4.1 What the rule score must capture

La capa de reglas debe poder representar, como mínimo:

- señales favorables del rol y del tipo de trabajo;
- compatibilidad de seniority, modalidad y geografía;
- evidencia de automatización útil o IA aplicada con valor concreto;
- señales complementarias de stack/lenguaje sin volverlas dominantes;
- razones positivas y negativas auditables.

### 4.2 Evidence hierarchy

La foundation fija una prioridad clave:

**la evidencia explícita vale más que la inferida**.

Eso significa que:

- una mención directa pesa más que una deducción débil;
- la inferencia puede ayudar, pero no sobreescribir hechos claros;
- el sistema debe resistir el entusiasmo artificial por texto ambiguo.

## 5. Bounded LLM Adjustment

El LLM entra, si entra, como segunda capa controlada.

### 5.1 Allowed role

El ajuste LLM sirve para:

- refinar ambigüedades semánticas;
- sumar o restar un delta limitado sobre el score base;
- mejorar matching sin convertir el sistema en una caja negra.

### 5.2 Forbidden role

El LLM NO debe:

- rescatar ofertas rechazadas por hard filters;
- reemplazar la fórmula de reglas;
- inventar evidencia inexistente;
- producir un score final imposible de auditar.

En otras palabras: el LLM puede corregir un borde, no mover los cimientos del edificio.

## 6. Final Thresholds and Labels

La foundation deja cerrados estos umbrales operativos:

| Range / event | Meaning |
|---|---|
| `< 70` | no califica para alerta Telegram |
| `70-84` | categoría `buena` |
| `85-100` | categoría `prioritaria` |
| `>= 70` y nueva oportunidad | habilita alerta Telegram |

### Threshold rules

- Telegram solo se dispara para **nuevas** oportunidades;
- el score no implica publicación pública automática si la oferta no pasó el flujo previo;
- `prioritaria` expresa mayor urgencia/encaje, no certeza absoluta.

## 7. Explainability Contract

Toda salida de scoring debe poder explicarse con un contrato mínimo.

### Minimum explainability payload

Sin fijar todavía el schema físico, el sistema debe poder responder:

- qué hard filters corrieron y cuáles aplicaron;
- qué razones positivas impulsaron el score;
- qué razones negativas lo limitaron;
- qué señales fueron explícitas vs inferidas;
- si hubo `LLMAdjustment`, qué delta aplicó y sobre qué base;
- por qué la oferta terminó como no alertable, `buena` o `prioritaria`.

### Explainability boundary

La explicabilidad cerrada aquí es principalmente interna/operativa. La superficie pública puede exponer solo un resumen suficiente, sin abrir internals sensibles ni red flags completas.

## 8. Publication Relationship

Scoring y publicación están conectados, pero no son lo mismo.

- scoring determina elegibilidad de valor y prioridad;
- publication usa ese resultado para proyectar al dashboard;
- Telegram depende de novedad + threshold;
- el dashboard público consume proyecciones ya calculadas, no lógica viva de scoring.

## 9. Boundaries for Future Vertical Changes

Todo vertical posterior debe respetar estas decisiones:

- hard filters antes de todo score;
- score por reglas antes de LLM;
- evidencia explícita sobre inferida;
- `buena` = 70-84;
- `prioritaria` = 85-100;
- Telegram desde 70 solo para nuevas oportunidades;
- explicabilidad mínima obligatoria.

La calibración fina, la fórmula exacta y el delta concreto del LLM se resolverán después, pero SIN reabrir esta foundation.
