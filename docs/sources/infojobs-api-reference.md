# InfoJobs API Reference for JobMatchRAG

## 1. Purpose

Este documento resume la documentación pública de InfoJobs que SÍ sirve para JobMatchRAG.

No redefine la arquitectura interna del proyecto. Su objetivo es dejar una referencia operativa para el futuro adapter de InfoJobs, con foco en:

- autenticación;
- endpoints útiles para capturar ofertas;
- diccionarios necesarios para filtros y normalización;
- errores y trazabilidad;
- límites y rarezas relevantes de la API.

Fuente principal revisada: <https://developer.infojobs.net/documentation/operation-list/index.xhtml>

Documentación complementaria revisada:

- quick start;
- app authentication;
- user OAuth2;
- `GET /offer`;
- `GET /offer/{offerId}`;
- `GET /dictionary/{dictionaryId}`;
- `GET /dictionary/type/{typeId}`;
- lista general de errores.

---

## 2. Qué partes de la API son relevantes para este proyecto

### 2.1 Relevantes para JobMatchRAG

Para el vertical de ingesta de ofertas, la parte útil hoy es la API pública de búsqueda de empleo:

- `GET /offer` — listado de ofertas por criterios de búsqueda; IMPLEMENTADO en V1.
- `GET /offer/{offerId}` — detalle completo de una oferta; IMPLEMENTADO en V1 solo para ofertas nuevas.
- `GET /dictionary/{dictionaryId}` — referencia útil para filtros y valores normalizados futuros; NO implementado en el adapter V1.
- `GET /dictionary/type/{typeId}` — referencia útil para diccionarios especiales como skills; NO implementado en el adapter V1.

### 2.2 No prioritarias para este proyecto hoy

La misma documentación también cubre endpoints de:

- candidate profile;
- CVs;
- applications;
- cover letters;
- questions / application tracking.

Eso NO es necesario para el ingestion framework ni para el primer adapter de ofertas.

### 2.3 OAuth2: documentado pero fuera del flujo principal de ingesta V1

InfoJobs documenta OAuth2 para endpoints privados de candidato.

Para JobMatchRAG, la ingesta de ofertas parte de endpoints **públicos** (`User Role: public`, `Scope: none`), así que el flujo OAuth2 no es requisito para capturar ofertas. Igual conviene tenerlo referenciado por si en el futuro se exploran features de candidate-side data, cosa que hoy está fuera de scope.

---

## 3. Base URL, formatos y autenticación

## 3.1 Base URLs

La documentación indica:

- España: `https://api.infojobs.net`
- Italia: `https://api.infojobs.it`

Para JobMatchRAG la referencia actual es **España**.

## 3.2 Formatos soportados

La documentación general indica que la API REST permite usar:

- JSON
- XML

Para este proyecto conviene tratar **JSON** como formato canónico de integración.

## 3.3 Autenticación de aplicación

Todas las llamadas requieren autenticación de aplicación con **HTTP Basic Auth** usando:

- `Client ID`
- `Client secret`

Header esperado:

```http
Authorization: Basic <base64(client_id:client_secret)>
```

Si falta o es inválido, la API puede devolver `401` o errores de seguridad como `102`.

## 3.4 OAuth2 de usuario

Solo aplica a endpoints privados. La documentación indica:

- authorize URL: `https://www.infojobs.net/api/oauth/user-authorize/index.xhtml`
- token URL: `https://www.infojobs.net/oauth/authorize`

No es parte del flujo de ingestión de ofertas públicas.

---

## 4. Endpoints útiles para JobMatchRAG

## 4.1 `GET /offer`

### URL documentada

`https://api.infojobs.net/api/9/offer`

### Uso en el proyecto

Es el endpoint principal para:

- descubrimiento de ofertas;
- capturas paginadas;
- filtros temporales provider-side explícitos como `sinceDate` cuando operación los pide en `provider_filters`;
- uso de filtros source-side como optimización.

En la implementación vigente de `first-source-infojobs`:

- cada `fetch()` del adapter procesa **una página de `GET /offer`**;
- `maxResults` se fija en **50** como ceiling operativo inicial;
- el request efectivo (`page`, `maxResults`, filtros soportados y `sinceDate` si existe) se preserva en la traza raw del run;
- la continuidad real del run sigue un checkpoint interno del framework/adapter y **NO** convierte `sinceDate` en checkpoint canónico;
- ese checkpoint es **best-effort**: usa página + posición + `next_offer_id` como ancla para reanudar dentro del listado actual, pero InfoJobs no ofrece garantía fuerte contra reordenamientos/mutaciones entre llamadas.

### Seguridad

- User Role: `public`
- Scope: `none`

### Parámetros relevantes

#### Texto y clasificación

- `q` — keyword search;
- `category` — categoría;
- `subcategory` — subcategoría.

#### Ubicación

- `province` / `provinceIds`;
- `city` / `cityIds`;
- `country` / `countryIds`.

#### Condiciones laborales

- `salaryMin`;
- `salaryMax`;
- `salaryPeriod`;
- `contractType`;
- `workday`;
- `teleworking`;
- `experienceMin`;
- `study`.

#### Operativos

- `page` — paginación;
- `maxResults` — tamaño de página; la propia doc recomienda **50 o menos** por performance;
- `order` — orden del resultado;
- `sinceDate` — antigüedad relativa (`_24_HOURS`, `_7_DAYS`, `_15_DAYS`, `ANY`);
- `facets` — devuelve navegación facetada y conteos;
- `employerId` — filtra por publisher.

### Observaciones útiles para el adapter

- Hay filtros multi-valor que aceptan repetición del parámetro (`province`, `category`, `subcategory`, etc.).
- `experienceMin` tiene semántica rara: con un valor funciona como filtro, con varios puede comportarse como rango.
- `subcategory` pisa a `category` si ambos aparecen.
- `province` pisa a `country`.
- `facets=true` puede ser útil para exploración y debugging, pero probablemente no para la captura estándar.
- `sinceDate` es relativo al “hoy” de InfoJobs; sirve como optimización temporal provider-side, no como checkpoint canónico del sistema ni como traducción automática de `window_start/window_end`.

### Campos relevantes de respuesta

Por cada offer, el listado trae suficiente metadata para decidir si conviene pedir detalle:

- `id`
- `title`
- `link`
- `city`
- `province`
- `category`
- `subcategory`
- `author`
- `published`
- `updated`
- `applications`
- `salaryMin`, `salaryMax`, `salaryPeriod`, `salaryDescription`
- `contractType`
- `workDay`
- `study`
- `experienceMin`
- `requirementMin`
- `teleworking`
- `executive`
- `priority`
- `multiProvince`

Además devuelve metadata de paginación:

- `totalResults`
- `currentResults`
- `totalPages`
- `currentPage`
- `pageSize`
- `availableSortingMethods`
- `sortBy`
- `queryParameters`

### Facets disponibles

La doc menciona facets como:

- `province`
- `category`
- `subcategory`
- `study`
- `contractType`
- `workDay`
- `salary`
- `experienceMin`
- `country`
- `city`

### Errores específicos documentados

Entre otros:

- `301` province inválida
- `302` country inválido
- `303` category inválida
- `304` subcategory inválida
- `305` order inválido
- `306` page inválida
- `307` contract type inválido
- `308` experience inválida
- `309` workday inválido
- `311` city inválida
- `318` salaryMin inválido
- `319` salaryMax inválido
- `820` employerId inválido

---

## 4.2 `GET /offer/{offerId}`

### URL documentada

`https://api.infojobs.net/api/7/offer/{offerId}`

### Uso en el proyecto

Es el endpoint para enriquecer la oferta capturada en listado con detalle completo. En `first-source-infojobs` se usa **solo para ofertas nuevas** detectadas por JobMatchRAG; si una oferta ya era conocida y reaparece en listados posteriores, no se hace re-enrichment regular en este vertical.

### Seguridad

- User Role: `public`
- Scope: `none`

### Parámetro

- `offerId` — identificador de la oferta.

### Campos especialmente útiles para JobMatchRAG

#### Identidad y estado

- `id`
- `state`
- `active`
- `archived`
- `deleted`
- `availableForVisualization`
- `disponibleForFullVisualization`

#### Contenido de la oferta

- `title`
- `description`
- `minRequirements`
- `desiredRequirements`
- `referenceId`
- `vacancies`
- `schedule`
- `contractDuration`
- `commissions`

#### Ubicación y geografía

- `city`
- `cityPD`
- `province`
- `country`
- `zipCode`
- `latitude`
- `longitude`
- `exactLocation`

#### Clasificación laboral

- `category`
- `subcategories`
- `contractType`
- `journey`
- `studiesMin`
- `experienceMin`
- `jobLevel`
- `staffInCharge`
- `residence`
- `teleworking` aparece en listado pero NO figura explícitamente en el detalle documentado; hay que asumir posible desalineación entre shapes.

#### Compensación

- `showPay`
- `minPay`
- `maxPay`

#### Publicación y engagement

- `creationDate`
- `updateDate`
- `applications`
- `upsellings`

#### Empresa

- `profile.id`
- `profile.name`
- `profile.description`
- `profile.province`
- `profile.country`
- `profile.numberWorkers`
- `profile.typeIndustry`
- `profile.logoUrl`
- `profile.corporateWebsiteUrl`
- `profile.websiteUrl`
- `profile.hidden`
- `profile.reviewSummary` (opcional)

#### Skills

- `skillsList`

### Errores específicos documentados

- `313` — `offerId` inválido.

### Observaciones operativas para el adapter

- el raw de `GET /offer/{offerId}` se preserva como captura **hermana** de la captura de listado, no como reemplazo;
- si una oferta nueva queda sin detalle por rate limit o presupuesto de requests, igualmente se preserva el raw de listing y la traza marca el detalle como `deferred` en vez de descartar la oferta;
- si `GET /offer` o `GET /offer/{offerId}` devuelven `429`, el adapter registra una observación estructurada de rate limit (`Retry-After`, cuota restante si está disponible); el run solo cierra `partial` si ya había material usable en el handoff, y si no había nada todavía cierra `failed` con razón `rate limit constrained execution`;
- errores de autenticación (`401`) se traducen como terminales de credenciales, salvo códigos provider-specific como `102` que se clasifican como configuración inválida;
- payloads exitosos malformados o respuestas con schema imposible se tratan como `source_data` terminal, no como fallos transitorios de red.

---

## 4.3 `GET /dictionary/{dictionaryId}`

### URL documentada

`https://api.infojobs.net/api/1/dictionary/{dictionaryId}`

### Uso en el proyecto

Es referencia útil para futuro trabajo de filtros/normalización, pero NO forma parte de los endpoints mínimos ni del adapter V1 implementado hoy. Sirve para:

- traducir filtros humanos a keys/ids válidos de InfoJobs;
- cachear valores maestros de provincia, categoría, teletrabajo, etc.;
- reducir errores por parámetros inválidos;
- facilitar mapping de valores raw hacia shapes internos.

### Seguridad

- User Role: `public`
- Scope: `none`

### Parámetros

- `dictionaryId` — nombre del diccionario;
- `parent` — permite filtrar listas jerárquicas.

### Diccionarios más útiles para JobMatchRAG

- `category`
- `subcategory`
- `country`
- `province`
- `city`
- `contract-type`
- `experience-min`
- `workday`
- `study`
- `salary-period`
- `salary-quantity`
- `teleworking`
- `offer-state`
- `industry`
- `employer-type`

### Relación jerárquica útil

- `subcategory` depende de `category`
- `province` depende de `country`
- `city` depende de `province`

### Shape de respuesta

Cada item trae:

- `id`
- `key`
- `value`
- `order`
- `parent` (cuando aplica)

### Error específico documentado

- `201` — parámetro inválido.

---

## 4.4 `GET /dictionary/type/{typeId}`

### URL documentada

`https://api.infojobs.net/api/1/dictionary/type/{typeId}`

### Uso en el proyecto

Sirve sobre todo como referencia futura para `skills`, porque el detalle de oferta puede devolver `skillsList`. No está integrado todavía en el adapter V1.

### Valores documentados

- `skills`
- `certifications`
- `InformalTraining`

### Shape de respuesta

- `id`
- `name`

---

## 5. Errores generales y trazabilidad

La documentación general de errores trae varios códigos relevantes para el adapter:

### Errores genéricos

- `1` — operación inexistente
- `201` — parámetro inválido
- `202` — parámetro requerido faltante
- `211` — header inválido
- `221` — body JSON inválido
- `222` — body XML inválido
- `223` — body faltante
- `224` — body demasiado largo
- `225` — error de conversión
- `226` — formato de fecha inválido

### Errores de seguridad

- `101` — usuario no autenticado
- `102` — credenciales de cliente inválidas
- `invalid_grant` — problema en OAuth2 / refresh / autorización expirada
- `116` — operación temporalmente deshabilitada

### Trazabilidad crítica

La doc indica que ante errores internos puede venir un `requestId`.

Eso es MUY importante para JobMatchRAG:

- debe guardarse en `rate_limit_observations` o `error_summary` si aparece;
- debe preservarse en logs/run trace para soporte posterior;
- no hay que perderlo en excepciones agregadas del adapter.

---

## 6. Qué filtros de InfoJobs sí conviene usar como optimización

Dado el contrato del proyecto, los filtros de portal NO son autoridad canónica. Igual conviene aprovechar varios como reducción de ruido/coste:

- `sinceDate`
- `category` / `subcategory`
- `province` / `provinceIds`
- `city` / `cityIds`
- `contractType`
- `workday`
- `teleworking`
- `experienceMin`
- `study`
- `salaryMin` / `salaryMax`
- `q`

### Regla para JobMatchRAG

- **en origen:** se usan como optimización de captura;
- **internamente:** elegibilidad, scoring y publicación siguen mandando.

---

## 7. Rarezas y decisiones operativas a tener en cuenta

## 7.1 Inconsistencia de versiones en la propia doc

La documentación muestra distintas versiones por endpoint:

- `GET /offer` → `api/9`
- `GET /offer/{offerId}` → `api/7`
- diccionarios → `api/1`

Además, algunos ejemplos usan otras versiones (`api/6`, `api/7`).

Conclusión para el proyecto:

- NO confiar ciegamente en el número de versión que aparece en ejemplos viejos;
- fijar versión por endpoint en el adapter/config de integración;
- cubrirlo con tests de contrato o smoke checks.

## 7.2 Diferencias entre listado y detalle

El shape del listado y el del detalle no son idénticos.

Ejemplos:

- listado usa `published` / `updated`; detalle usa `creationDate` / `updateDate`;
- listado muestra `teleworking` explícitamente; el detalle documentado no lo destaca igual;
- listado usa `author`; detalle usa `profile`.

Eso implica que el adapter debe preservar ambos raws y no asumir que el detalle “reemplaza” 1:1 al listado.

## 7.3 `city` como campo abierto

La doc del detalle aclara que `city` es un campo abierto y puede contener cualquier valor, aunque también existe `cityPD`.

Para normalización posterior, `cityPD` y diccionarios son más confiables que el texto libre.

## 7.4 `maxResults`

La propia doc recomienda **50 o menos** por request. Conviene respetarlo como ceiling inicial del adapter salvo validación posterior.

## 7.5 `sinceDate` no reemplaza checkpoint canónico

Es útil para bajar volumen, pero es un filtro relativo. No debe reemplazar el checkpoint interno del framework (`checkpoint_in` / `checkpoint_out`).

Además, en InfoJobs actual el checkpoint del adapter solo puede prometer continuidad **best-effort** sobre el orden observado del listado. Si el proveedor inserta, borra o reordena resultados entre fetches, el adapter puede reanudar con replay defensivo de página para evitar skips silenciosos, pero NO puede prometer continuidad determinista exacta sin una garantía de orden estable que la API no documenta. Si recibe un checkpoint inválido o ajeno al adapter, la ejecución debe fallar explícitamente en vez de resetearse silenciosamente a página 1.

---

## 8. Recomendación de uso dentro de JobMatchRAG

### 8.1 Flujo sugerido para el adapter InfoJobs implementado

1. traducir filter intent interno a parámetros source-side permitidos;
2. consultar `GET /offer` paginado con límites acotados;
3. capturar raw de listado con query efectiva y metadata de paginación;
4. decidir enriquecimiento por `offerId` usando `GET /offer/{offerId}` solo para ofertas nuevas;
5. persistir snapshots raw separados o componibles;
6. entregar material a normalización sin perder:
   - request params efectivos,
   - versioned endpoint usado,
   - timestamps de captura por origen (`list` y, si existe, `detail`),
   - requestId si hubo error.

### 8.2 Endpoints mínimos para V1 del adapter

Implementado hoy en `first-source-infojobs`:

- `GET /offer`
- `GET /offer/{offerId}`

Referencia futura, fuera de V1:

- `GET /dictionary/{dictionaryId}`
- `GET /dictionary/type/skills`

---

## 9. Resumen ejecutivo

Con `first-source-infojobs` ya implementado y archivado, la parte de InfoJobs que realmente importa para JobMatchRAG es esta:

- **Auth:** Basic Auth de aplicación; OAuth2 no hace falta para ofertas públicas.
- **Discovery/listing:** `GET /offer` con paginación, `sinceDate`, ubicación, categoría, teleworking y filtros laborales.
- **Enrichment/detail:** `GET /offer/{offerId}` para descripción completa, empresa, salarios, ubicación, skills y estado.
- **Future normalization support:** diccionarios públicos para categorías, provincias, ciudades, contrato, teletrabajo, experiencia, estudios y salarios; referenciados pero NO implementados en V1.
- **Traceability:** preservar `requestId` en errores, query efectiva, versión del endpoint, timestamps de captura por origen y diferencias entre listado vs detalle.
- **Boundary rule:** InfoJobs ofrece filtros útiles, pero la autoridad canónica sigue siendo interna.

---

## 10. Referencias revisadas

- Operations list: <https://developer.infojobs.net/documentation/operation-list/index.xhtml>
- Quick start: <https://developer.infojobs.net/documentation/quick-start/index.xhtml>
- App auth: <https://developer.infojobs.net/documentation/app-auth/index.xhtml>
- User OAuth2: <https://developer.infojobs.net/documentation/user-oauth2/index.xhtml>
- Offer list: <https://developer.infojobs.net/documentation/operation/offer-list-9.xhtml>
- Offer detail: <https://developer.infojobs.net/documentation/operation/offer-get-7.xhtml>
- Dictionary: <https://developer.infojobs.net/documentation/operation/dictionary-get-1.xhtml>
- Dictionary types: <https://developer.infojobs.net/documentation/operation/dictionary-type-get-1.xhtml>
- API errors: <https://developer.infojobs.net/documentation/operation/errors.xhtml>
