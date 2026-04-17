# Foundation de scoring — JobMatchRAG

## 1. Propósito

Este documento define la base de matching/scoring de V1. La idea es SIMPLE: primero excluir lo claramente incompatible, después puntuar con reglas auditables y recién al final permitir un ajuste LLM acotado.

Todavía no cierra una fórmula numérica detallada ni datasets de calibración fina. Sí cierra el ORDEN, los límites y el contrato de explicabilidad.

## 2. Orden de decisión

El flujo base de scoring es:

`eligibility -> rule score -> bounded LLM adjustment -> final classification`

Esto implica cuatro reglas no negociables:

1. una oferta incompatible NO llega al scoring;
2. la primera autoridad de score es una capa de reglas;
3. el LLM nunca reemplaza el score base;
4. la salida final debe seguir siendo explicable.

## 3. Gates de elegibilidad (filtros duros)

Antes de puntuar, el sistema debe descartar incompatibilidades claras.

### 3.1 Base mínima de filtros duros

Las causas mínimas de exclusión cerradas para esta foundation son:

- geografía o modalidad incompatibles;
- seniority por encima de 3 años;
- roles incompatibles con el foco real del producto;
- consultoras/body-shopping con evidencia explícita o reliable; una lista curada de compañías conocidas solo agrega ambigüedad, no blacklist automática.

La política activa de fuente-search queda así:

- onsite solo Madrid;
- remote en cualquier punto de España;
- hybrid en Madrid o fuera de Madrid solo si la asistencia explícita es `< 3 días/mes` y la ciudad aparece en el dataset curado de ciudades con acceso AVE sembrado en repo;
- frescura >15 días excluye solo cuando la fecha es confiable;
- los casos ambiguos sobreviven para scoring/explicación, pero las exclusiones explícitas NO llegan a LLM.

Los hints del proveedor (`q`, `experienceMin`, `teleworking`, `sinceDate`, `category`/`subcategory`) pueden ayudar al discovery, pero NO reemplazan estos gates: la autoridad de elegibilidad sigue en los filtros canónicos internos.

### 3.2 Significado de los filtros duros

Los filtros duros existen para evitar dos errores clásicos:

- gastar coste analítico en ofertas que ya sabemos que no encajan;
- dejar que un score “bonito” tape una incompatibilidad estructural.

Si falla elegibilidad, la oferta queda fuera del scoring pero mantiene trazabilidad histórica interna con sus razones.

## 4. Base mínima de score por reglas

La primera capa positiva de matching es un `ScoreBreakdown` por reglas.

### 4.1 Qué debe capturar el score por reglas

La capa de reglas debe poder representar, como mínimo:

- señales favorables del rol y del tipo de trabajo;
- compatibilidad de seniority, modalidad y geografía;
- evidencia de automatización útil o IA aplicada con valor concreto;
- señales complementarias de stack/lenguaje sin volverlas dominantes;
- razones positivas y negativas auditables.

### 4.2 Jerarquía de evidencia

La foundation fija una prioridad clave:

**la evidencia explícita vale más que la inferida**.

Eso significa que:

- una mención directa pesa más que una deducción débil;
- la inferencia puede ayudar, pero no sobreescribir hechos claros;
- el sistema debe resistir el entusiasmo artificial frente a texto ambiguo.

## 5. Ajuste LLM acotado

El LLM entra, si entra, como segunda capa controlada.

### 5.1 Rol permitido

El ajuste LLM sirve para:

- refinar ambigüedades semánticas;
- sumar o restar un delta limitado sobre el score base;
- mejorar el matching sin convertir el sistema en una caja negra.

### 5.2 Rol prohibido

El LLM NO debe:

- rescatar ofertas rechazadas por filtros duros;
- reinterpretar como compatibles ofertas excluidas por filtros canónicos explícitos de geografía, consultoría/body-shopping, seniority o frescura confiable;
- reemplazar la fórmula de reglas;
- inventar evidencia inexistente;
- producir un score final imposible de auditar.

En otras palabras: el LLM puede corregir un borde, no mover los cimientos del edificio.

## 6. Umbrales y etiquetas finales

La foundation deja cerrados estos umbrales operativos:

| Rango / evento | Significado |
|---|---|
| `< 70` | no califica para alerta de Telegram |
| `70-84` | categoría `buena` |
| `85-100` | categoría `prioritaria` |
| `>= 70` y nueva oportunidad | habilita alerta de Telegram |

### Reglas de umbral

- Telegram solo se dispara para **nuevas** oportunidades;
- el score no implica publicación pública automática si la oferta no pasó el flujo previo;
- `prioritaria` expresa mayor urgencia/encaje, no certeza absoluta.

## 7. Contrato de explicabilidad

Toda salida de scoring debe poder explicarse con un contrato mínimo.

### Payload mínimo de explicabilidad

Sin fijar todavía el schema físico, el sistema debe poder responder:

- qué filtros duros corrieron y cuáles aplicaron;
- qué razones positivas impulsaron el score;
- qué razones negativas lo limitaron;
- qué señales fueron explícitas frente a inferidas;
- si hubo `LLMAdjustment`, qué delta aplicó y sobre qué base;
- por qué la oferta terminó como no alertable, `buena` o `prioritaria`.

### Boundary de explicabilidad

La explicabilidad cerrada acá es principalmente interna/operativa. La superficie pública puede exponer solo un resumen suficiente, sin abrir internals sensibles ni red flags completas.

## 8. Relación con la publicación

Scoring y publicación están conectados, pero no son lo mismo.

- scoring determina elegibilidad de valor y prioridad;
- publicación usa ese resultado para proyectar al dashboard;
- Telegram depende de novedad + umbral;
- el dashboard público consume proyecciones ya calculadas, no lógica viva de scoring.

## 9. Boundaries para cambios verticales futuros

Todo vertical posterior debe respetar estas decisiones:

- filtros duros antes de todo score;
- score por reglas antes de LLM;
- evidencia explícita por encima de la inferida;
- `buena` = 70-84;
- `prioritaria` = 85-100;
- Telegram desde 70 solo para nuevas oportunidades;
- explicabilidad mínima obligatoria.

La calibración fina, la fórmula exacta y el delta concreto del LLM se resolverán después, pero SIN reabrir esta foundation.
