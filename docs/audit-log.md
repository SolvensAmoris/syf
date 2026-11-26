# Audit log — SIF v0.2

Registro de verificaciones ejecutadas contra el prototipo. Cada entrada
indica qué se comprobó, contra qué y con qué resultado. Las entradas
marcadas como brechas están registradas como regresiones en `tests/`.

## 2026-11-26 — Primera ejecución del prototipo

- Verificador v0.2 y 9 pruebas unitarias: **9/9 PASS** (0.002 s).
- Alcance: el prototipo verifica precondiciones, postcondiciones,
  invariantes, alcance, marco y efectos esperados/prohibidos para el
  operador `append-unique` sobre un documento con revisión, propietario
  y etiquetas.
- Límite: el DSL tiene un solo operador y una sola ruta, así que el cambio
  fuera de alcance solo puede probarse reduciendo `scope`, no derivando
  un cambio ajeno. La prueba correspondiente lo admite en su comentario.
- El verificador **nunca comprueba `snapshot_digest`** (0 referencias en
  el código): lo toma en confianza.

## 2026-11-26 — Demostraciones adversariales A1–A6

Ejecutadas contra el prototipo. Todas confirmaron brechas reales.

- **A1** — `arguments./path = /owner` + `INTENT.target = ["/owner"]` con
  `rule.path = /labels` → PASS. Brecha: `verify()` nunca lee
  `TRANSFORMATION.arguments`, `INTENT.target` ni `TRANSFORMATION.operator`
  (verificado por grep).
- **A2** — `operator = "delete-everything"` → PASS. Misma brecha.
- **A3** — `INTENT.action = "borrar-todo"` → PASS. Misma brecha.
- **A4** — `facts` reordenados → mismo PASS (sin efecto; el orden no
  afecta al veredicto).
- **A5** — `frame = ["/owner", "/labels"]` (solape con `scope`) → FAIL
  (condición de marco violada). El código resuelve la precedencia a
  favor del marco; el esquema no lo declara. Pendiente: declarar la
  precedencia marco-sobre-alcance en el esquema.
- **A6** — `STATE.revision` eliminada → UNKNOWN. `get_path` trata
  `/revision` y `/subject` como campos de nivel superior y el resto
  desde `facts`. La regla vive solo en el código; el esquema debe
  declararla.

## 2026-11-26 — Brechas B1–B8 (contrato vs. código)

- **B1** — falta `TRANSFORMATION.rule` → UNKNOWN (el contrato exige
  FAIL para estructura inválida).
- **B2** — `schema_version` incorrecta → UNKNOWN (el contrato exige
  FAIL).
- **B3** — `INTENT.target` con tipo incorrecto → PASS silencioso.
- **B4** — `preconditions` como string → `AttributeError` no capturado
  (`'str' object has no attribute 'get'`, `predicate()` línea 29).
  El verificador desaparece dentro de una excepción. Variante mínima:
  `preconditions = ["x"]`. Ver `tests/test_totality.py` y la fixture
  en `tests/fixtures/adversarial/`.
- **B5** — contradicción + incertidumbre: el verificador devuelve FAIL
  con una sola razón y pierde el hallazgo UNKNOWN. El veredicto necesita
  una lista de hallazgos.
- **B6** — `postconditions` con tipo incorrecto → UNKNOWN (vía
  `TypeError` capturado; el contrato exige FAIL).
- **B7** — falta `TRANSFORMATION` → UNKNOWN (el contrato exige FAIL).
- **B8** — `scope` como string → FAIL por la razón equivocada (el
  string se lee como conjunto de caracteres).
- **NFC** — el contrato §2 regla 5 exige normalización NFC; el código
  compara strings sin normalizar.

## 2026-11-26 — Segundo vector de caída

- Valor profundamente anidado en `facts` (3,000 niveles) →
  `RecursionError` no capturado desde el `deepcopy` de `derive`.
  El verificador necesita un límite de profundidad documentado con
  rechazo controlado.

## 2026-11-26 — Precisiones al ejemplo válido

- La precondición 1 referencia `state /revision`, que no está en
  `facts` (solo es campo de nivel superior de `STATE`). El código lo
  resuelve por la vía especial de A6; el esquema debe declarar la
  regla de resolución.
- El esquema define `Path` como lista de segmentos, pero el ejemplo
  usa strings con barras (`"/labels"`). Decisión de canonicalización
  pendiente; relevante para el digest. El JSON Schema
  (`schemas/sif-0.2.schema.json`) sigue la implementación (strings
  con barras) y lo deja anotado.

## 2026-11-26 — Protocolo STALE_STATE (validación optimista)

SIF se calcula sobre una revisión concreta y solo aplica si esa revisión
sigue vigente al confirmar:

1. Capturar el estado; registrar `subject`, `revision`,
   `snapshot_digest`.
2. Verificar el digest contra esa instantánea y derivar el candidato `S'`.
3. Confirmar con comparación atómica: aplicar solo si la revisión
   actual sigue siendo la capturada; en caso contrario, no escribir y
   devolver `STALE_STATE`.
4. Si se aplica, incrementar la revisión en la misma operación atómica
   y registrar qué revisión produjo el cambio.

SQL de referencia:

```sql
UPDATE documents SET data = :new_data, revision = revision + 1
WHERE id = :id AND revision = :expected_revision;
```

1 fila = aplicado; 0 filas = otra escritura ganó la carrera: descartar
el resultado derivado, releer el estado, recalcular SIF, no reaplicar
el candidato viejo.

Precisiones: tras `STALE_STATE`, re-verificar el digest sobre la
**nueva** instantánea (la verificación vieja no se transfiere); el
digest es el ancla de integridad de la instantánea capturada, la
revisión es el ancla de frescura al confirmar — ninguno basta solo; el
protocolo exige cooperación del destino (CAS atómico sobre la
revisión), el mismo límite que el fencing token.

Prueba adversarial: A y B leen r3; A aplica y avanza a r4; B intenta
confirmar con `expected_revision = r3` → B no escribe, recibe
`STALE_STATE`. Para cambios multi-fila o invariantes globales, la
comparación de una sola revisión puede no bastar; la validación debe
cubrir todo el conjunto relevante en una transacción con el aislamiento
adecuado.

## 2026-11-26 — Brecha lease / fencing (decisión abierta)

Un lease detecta una reserva expirada pero no prueba que la
re-ejecución sea segura (el proceso original puede seguir activo; el
efecto remoto puede haber ocurrido sin confirmación registrada).
Protocolo de cuatro estados: `processing` con lease válido → esperar
solo hasta un límite definido; lease expirado + efecto
demostrablemente no realizado → permitir reclaim; efecto remoto
idempotente/deduplicado → reintentar con la misma clave según el
contrato del destino; resultado incierto → responder "unknown" y
reconciliar, nunca re-ejecutar a ciegas. El reclaim usa un
generation/fencing token creciente para detener a un worker viejo
después del reclaim, solo si el destino también valida el token; sin
esa cooperación, el token solo no protege el efecto remoto. Pendientes:
política de lease y reclaim; timeout de espera acotado; estado incierto
sin re-ejecución automática. Precisión: "efecto demostrablemente no
realizado" exige estado consultable en el destino o esa rama colapsa
en "unknown"; el reclaim es una decisión de política (quién puede
reclamar, con qué evidencia), no un default del mecanismo.
