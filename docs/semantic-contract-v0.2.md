# Contrato semántico SIF v0.2 — borrador normativo

Este contrato define cuándo un verificador puede declarar coherente una
transición representada por:

```
SIF = (S, I, T, C)
```

donde `S` es el estado de entrada, `I` la intención, `T` la transformación
y `C` las consecuencias declaradas.

Los términos **DEBE**, **NO DEBE** y **PUEDE** expresan requisitos
normativos. El contrato cubre coherencia e integridad estructural; **no
determina autorización ni demuestra que el sistema externo haya ejecutado
la transformación**.

## 1. Resultado del verificador

```
V(S, I, T, C) ∈ {PASS, FAIL, UNKNOWN}
```

- **PASS:** todas las obligaciones de este contrato se comprobaron y se
  cumplen.
- **FAIL:** se comprobó una contradicción, una obligación incumplida o una
  estructura inválida.
- **UNKNOWN:** no hay información suficiente para decidir alguna obligación.

`UNKNOWN` **NO DEBE** convertirse en `PASS`. Una estructura inválida —por
ejemplo, campos requeridos ausentes o tipos incorrectos— produce `FAIL`;
una referencia cuyo significado no puede resolverse produce `UNKNOWN`.

> NOTA (decisión 0001): el criterio de cierre de v0.3 revisa esta sección:
> una estructura inválida produce `UNKNOWN` con el error estructural
> registrado como hallazgo, y el estado final es el peor hallazgo
> (FAIL > UNKNOWN > PASS). Ver
> `docs/decisions/0001-result-status-and-findings.md`. Esta sección del
> contrato debe corregirse para reflejar esa decisión antes de cerrar v0.3.

## 2. Modelo de rutas

Cada ruta se interpreta desde la raíz del bloque que la contiene. Se
reconocen dos espacios de nombres:

- `state:/...`: campos de nivel superior de `STATE`, junto con
  `STATE.facts`.
- `result:/...`: campos del estado candidato derivado por
  `TRANSFORMATION.rule`.

Reglas de resolución:

1. Los campos reservados de nivel superior, incluidos `subject`, `revision`
   y `source`, se resuelven directamente en `STATE`.
2. Las demás rutas de estado se resuelven dentro de `STATE.facts`.
3. Una ruta inexistente es un error de resolución; no se interpreta como
   `null`.
4. La sintaxis distingue una ruta de una clave literal. No se permite
   reinterpretar silenciosamente una ruta no cualificada como perteneciente
   a otro espacio de nombres.
5. Las rutas se comparan después de normalizar sus segmentos según la
   canonicalización SIF aplicable.

Si una ruta puede resolverse de más de una manera, el resultado es
`UNKNOWN`; la implementación NO DEBE elegir una interpretación por
conveniencia.

## 3. Compatibilidad entre intención y transformación

Sea `W(T, S, I)` el conjunto de rutas que la regla de transformación puede
modificar al aplicarse a `S` con `I`. El verificador DEBE obtenerlo de la
regla validada, no inferirlo de las consecuencias declaradas.

La transformación es compatible con la intención solo si:

1. Cada ruta de `INTENT.target` está cubierta por el objetivo declarado en
   `TRANSFORMATION.arguments`.
2. El objetivo de los argumentos coincide con el objetivo efectivo de la
   regla.
3. El conjunto de rutas objetivo de la intención coincide con el conjunto
   de rutas que la regla puede modificar, salvo que el operador tenga una
   regla de expansión explícita y versionada que lo permita.
4. Cada parámetro usado por la regla existe en `INTENT.parameters` con el
   tipo requerido.
5. Ningún parámetro relevante ni argumento es ignorado implícitamente por
   la regla.

Si alguna condición falla y se demuestra la contradicción, el resultado es
`FAIL`. Si no se puede determinar el conjunto de rutas afectadas, el
resultado es `UNKNOWN`.

## 4. Identidad operativa

Sea `M(action, operator)` la correspondencia entre la acción de la
intención y el operador de la transformación, definida por `rule.kind`
(por ejemplo, `añadir-etiqueta` con `append-unique`).

1. `M` es una tabla de correspondencia explícita y versionada, parte del
   contrato del verificador.
2. La tripleta recibida `(action, operator, rule.kind)` DEBE coincidir
   exactamente con una entrada válida de `M`.
3. NO DEBE establecerse equivalencia por similitud de nombres.
4. Una tripleta incompatible produce `FAIL`; una combinación no definida
   en `M` produce `UNKNOWN`.
5. Cada operador DEBE tener una especificación: tipos de entrada y salida,
   precondiciones que evalúa, rutas que puede modificar, efectos
   secundarios declarados y comportamiento ante valores ausentes o nulos.
6. Un operador desconocido nunca produce `PASS`.

## 5. Derivación

La regla de transformación es declarativa, determinista y evaluable con
los datos disponibles. No ejecuta acciones externas ni consulta estado
durante la evaluación. Produce un único estado candidato `S'` y un
conjunto de cambios `Δ`.

Comprobaciones:

1. Las precondiciones son verdaderas en `S`.
2. Las postcondiciones son verdaderas en `S'`.
3. Cada ruta de `Δ` es un cambio real.
4. No hay cambios omitidos.
5. Misma entrada y misma versión de regla producen el mismo `S'` y el
   mismo `Δ`.

Una precondición o postcondición falsa produce `FAIL`. Una regla no
evaluable produce `UNKNOWN`.

## 6. Alcance, marco y efectos

1. Las rutas modificadas deben estar dentro de `Scope(C)`.
2. `Frame(T)` preserva el valor exacto de sus rutas.
3. Una ruta en `Scope` y en `Frame` a la vez es una contradicción
   contractual y produce `FAIL`.
4. Los efectos esperados no amplían el alcance.
5. Deben detectarse cambios múltiples y secundarios.
6. Si las rutas modificables no pueden enumerarse por completo, no hay
   `PASS`.
7. Los efectos esperados deben coincidir con los cambios derivados.
8. Un efecto derivado prohibido produce `FAIL`.
9. La lista de efectos declarados no sustituye la comparación con `Δ`.

## 7. Integridad del digest

La validación sintáctica es independiente de la verificación
criptográfica: recalcular a partir de la instantánea canónica identificada
por `STATE.source` y comparar con `snapshot_digest`.

1. Un formato válido no prueba correspondencia.
2. Sin acceso a la instantánea o a su representación canónica, la
   integridad criptográfica es `UNKNOWN`, no `PASS`.
3. El contrato debe declarar explícitamente si la integridad criptográfica
   es requisito para `PASS`; si lo es, un digest no verificable bloquea
   `PASS`.

## 8. Separación

`PASS` significa únicamente que se verificaron las obligaciones semánticas.
No significa que:

- la acción esté autorizada;
- el estado de entrada sea verdadero o actual;
- el sistema externo ejecutará exactamente lo previsto;
- la consecuencia declarada haya ocurrido;
- el comportamiento de un operador fuera del modelo esté cubierto.

La autorización y la verificación del efecto ejecutado son decisiones
separadas, con sus propios mecanismos y evidencia.

## 9. Aprobación

`PASS` solo si todas las obligaciones aplicables de las secciones 2–7
están demostradas, sin ningún `FAIL` ni `UNKNOWN`:

```
V = PASS ⟺ ∧ proved(j)
```

Criterio para las pruebas adversariales: cada obligación necesita casos de
cumplimiento, de contradicción y de información faltante. A1–A3 se
conservan como regresiones.
