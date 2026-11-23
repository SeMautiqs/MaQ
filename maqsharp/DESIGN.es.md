# MaQ#: Q# en Maude (v0.6)

Semántica operacional ejecutable de un fragmento de Q#, construida sobre la
semántica simbólica de qubits de smc4qc (Canh Minh Do, JAIST).

## Uso rápido

```
maude -allow-files qsharp-io.maude
Q#> open examples/bell.qs
Q#> run Main
Q#> check Main ensures RES:Value == (true).QBool
```

Con amplitudes simbólicas:

```
maude -allow-files examples/symbolic.maude qsharp-io.maude
Q#> open examples/teleport.qs
Q#> module SYMBOLIC
Q#> check Teleport (qb(0), qb(1)) in (q[0]: a . |0> + b . |1>) (q[1]: |0>) ensures eqUpToPhase(qubitAt(QS:Qubit, 1), a . |0> + b . |1>)
```

Comandos (en todos, `Op` admite la forma `Op (args) in estado`):

| Comando | Qué hace |
|---|---|
| `open f.qs` / `show` | cargar un programa / ver su traducción |
| `run Op` | estados finales distintos, con la probabilidad de **un** camino |
| `runnp Op` | lo mismo sin probabilidades: grafo finito incluso con bucles RUS |
| `dist Op` | **distribución exacta** del resultado: suma todos los caminos, hasta 200 pasos, e informa de la masa sin explorar y de la bloqueada |
| `check Op ensures cond` | `cond` en todos los estados finales; `QS:Qubit` es el estado y `RES:Value` el resultado |
| `mc Op satisfies F` | model checking LTL de `F` |
| `module M` | módulo de trabajo (debe extender `QSHARP-PROPS`) |
| `q` / `quit` | salir |

Proposiciones LTL: `ended`, `returns(V)`, `qubit(N, V)`, `qubitPh(N, V)` (salvo fase),
`entangled(N)` y `liveLE(K)` (como mucho K qubits vivos).

## Ficheros

| Fichero | Contenido |
|---|---|
| `qsharp-syntax.maude` | `QSHARP-SYNTAX`: solo sintaxis; no depende de smc4qc |
| `qsharp-semantics.maude` | `QSHARP-SEMANTICS`: configuración, ecuaciones y reglas |
| `qsharp-props.maude` | `QSHARP-PROPS`: `eqUpToPhase` (fases ±1, ±i) |
| `qsharp-mc.maude` | `QSHARP-MC`: regla de *stutter* y proposiciones atómicas para el model checker |
| `smc4qc-patch.maude` | `SYMBOLIC-REASONING-PATCHED`: arreglos sobre smc4qc (`q[nil]: nil`, conjugado de `i` y aritmética sobre `Real`) |
| `smc4qc/` | `core.maude` y `symbolic-reasoning.maude` copiados sin cambios |
| `qsharp-io.maude` | herramienta interactiva: bucle de I/O al estilo de MUnit |
| `frontend/qsharp-lexer.maude` | lexer sobre `String`, previo a `tokenize` |
| `frontend/qsharp-surface.maude` | firma de la sintaxis de superficie de Q# y de los comandos, y gramáticas con bubbles construidas a metanivel |
| `frontend/qsharp-translate.maude` | traducción a metanivel de la superficie a `QSHARP-SYNTAX` |
| `examples/` | `bell.qs`, `teleport.qs`, `ghz.qs`, `rus.qs`, `functors.qs`, `random.qs`, `errors.qs` y `symbolic.maude` |
| `tests/` | pruebas a nivel objeto (`run-all.sh`) y sesión de la herramienta (`run-tool.sh`) |
| `validation/` | `validate.py` y `validation.qs`: comparación con el simulador oficial de Q# |

## Subconjunto soportado

- Declaraciones `operation 'F (p : T, ...) : T { ... }`. Los tipos son solo anotación.
- Sentencias: `use 'q = Qubit() ;`, `let`, `mutable`, `set`, `set +=`, `if`/`else`,
  `for 'i in a .. b { }`, `for 'q in 'qs { }`, `while`, `repeat { } until c ;`,
  `repeat { } until c fixup { }` y `return`.
- Arrays: `[e1, e2]`, `'qs[i]`, `Length('qs)` y `use 'qs = Qubit[n] ;`.
- Expresiones puras: `Int`, `true`/`false`, `Zero`/`One`, `+ - *` y las comparaciones
  `eq neq lt le gt ge`, que corresponden a `== != < <= > >=`; además `and`, `or` y `not`.
- Intrínsecas: `I X Y Z H S T CNOT CY CZ SWAP CCNOT M Reset ResetAll`.
- Llamadas a operaciones de usuario con paso de parámetros y valor de retorno.
- Functores: `Adjoint` y `Controlled` sobre intrínsecas y sobre operaciones de usuario,
  anidados y combinados (`Controlled Adjoint S`), y `within { } apply { }`.

**Restricción clave:** una llamada (`Call`) no es una expresión. Solo puede aparecer
en la raíz de una sentencia: `'H('q) ;`, `let 'r = 'M('q) ;`, `set 'x = 'F(...) ;`
o `return 'F(...) ;`. Así las condiciones son puras y la gramática lo garantiza.

## Frontend: de Q# textual a Maude

1. **Lectura**: el fichero se lee con `FILE` (`openFile`, `getLine`, `closeFile`).
2. **Lexer**: separa operadores pegados (`0..n-1`, `a==b`), quita comentarios `//` y conserva las cadenas.
3. **Parseo**: `metaParse` en `QSHARP-GRAMMAR`. Esta gramática es la firma `QSHARP-SURFACE-SIGN`
   más un token `Bubble (1 1)` para identificadores, con las palabras clave excluidas.
   En la superficie se escribe Q# tal cual: `==`, `<`, `elif`, `namespace`, `import`, `@EntryPoint()`, `is Adj + Ctl`.
4. **Traducción** a `QSHARP-SYNTAX`. Además de renombrar, desazucara:
   - Llamadas dentro de expresiones: se extraen a temporales `$t0, $t1, ...`, de izquierda a derecha.
     En `repeat-until`, el prólogo de la condición se coloca al final del cuerpo.
   - Una llamada en la condición de un `while` se rechaza, porque la condición se reevalúa en cada vuelta.
   - `elif` pasa a `else { if }` y `set x -= e` a `set x = x - e`.
   - `function` pasa a `operation`; `namespace`, `import`, `@EntryPoint()` y las características (`is Adj + Ctl`) se ignoran.
5. **Ejecución**: `metaSearch` sobre `upModule(M)`, con `M = QSHARP-PROPS` o el módulo elegido con `module`.
   Los argumentos, el estado y la condición del comando son bubbles que se parsean en `M`.

`QSHARP-SYNTAX` no puede compartir módulo con `META-LEVEL`: como `Qid < Exp`, `_,_` y `_[_]`
chocan con los de `META-TERM`. Por eso el frontend trabaja solo a metanivel.

## Validación frente al simulador de Q#

`python3 validation/validate.py [ejecuciones]` (requiere `pip install qdk` y `maude` en el PATH)
ejecuta cada operación en el simulador oficial de Q# y la compara con la distribución exacta
de `dist`. Para cada resultado calcula z = (k − Np)/√(Np(1−p)). Un caso falla si algún
|z| > 4, si aparece un resultado de probabilidad 0 o si falta uno de probabilidad 1.

Con 4000 ejecuciones, las **19 operaciones coinciden**: |z| máximo 1,95 y distancia de variación
total ≤ 0,008. Hay casos con probabilidades irracionales, como H T H, que da One con (2−√2)/4,
y con distribuciones conjuntas, Controlled S/T, teletransporte con estado preparado y RUS.

## Diseño de la semántica

- Configuración: `{(qstate: Q) (k: K) (env: Env) (decls: D) (next: N) (prob: P) (result: V) (isEnd: B)}`.
  `k:` es una continuación de sentencias.
- **Reglas**: puertas, `M` y `Reset`; cada paso cuántico es un estado. `M` ramifica
  en `M-Zero` y `M-One`, poda las ramas de probabilidad 0 y multiplica `prob:`.
- **Ecuaciones**: toda la parte clásica (entornos, bloques, llamadas, `return`).
- Los ámbitos usan `restore(Env)`. Como Q# no permite sombreado, basta restringir el
  entorno a las variables previas. Las llamadas usan `frame(Env)`.
- `use` inserta `release(N)` al final del bloque. Si el qubit está separado y en |0⟩,
  se elimina del estado.
- `repeat` y `while` ejecutan una iteración cada vez y vuelven a colocar el bucle tras el
  `restore`, así la continuación no crece.
- Al liberar un qubit, `next:` pasa a ser el primer índice libre según los qubits vivos.
  Los estados son canónicos y un `use` dentro de un bucle no hace infinito el grafo.
- Dos modos: `run`/`runWith` acumulan la probabilidad del camino en `prob:`;
  `runNP`/`runWithNP` la fijan a `untracked`. Con repeat-until-success, el primero da un
  espacio de estados infinito (1/2, 1/4, ...) y el segundo uno finito, apto para model checking.
- **Functores**:
  - `Adjoint Op` ejecuta `adj(cuerpo)`: orden inverso, cada llamada con `Adjoint` y los `for`
    recorridos hacia atrás. Las ligaduras clásicas y los `use` iniciales se mantienen delante.
  - `Controlled Op(ctrls, args)` ejecuta `ctl(cuerpo, ctrls)`: cada llamada del cuerpo recibe
    los controles. Los `Controlled` anidados juntan sus listas de controles.
  - Normalización: `Adjoint Adjoint C = C` y `Adjoint Controlled C = Controlled Adjoint C`.
  - `within {A} apply {B}` se ejecuta como `A; B; adj(A)`, cada parte en su ámbito.
- **Aplicador genérico de puertas controladas** `applyU(Q, ctrls, t, U)`: generaliza
  `CX = B0⊗I + B3⊗X` de smc4qc a k controles en posiciones arbitrarias, con
  G(c·Cs) = P0_c⊗I + P1_c⊗G(Cs). Antes junta en un bloque los qubits implicados y después aplica `simplify`.
  Se usa para `Controlled` y para T, S† y T†. La T de smc4qc está mal definida: usa `1 + i`
  (suma entera) en vez de `1 .+ i`, y por eso no reduce.
- **Distribución exacta** (`dist`): se recorre el **árbol** de ejecución con `metaApply`, regla a
  regla, usando las etiquetas de `getRls` del módulo aplanado. `search` no sirve porque
  fusiona configuraciones idénticas: en Bell, los caminos 00 y 11 acaban igual y daría 1/2 en
  vez de 1. Cada hoja suma su `prob:` al resultado (`.+` en el módulo de trabajo, así que
  funciona con amplitudes simbólicas). Se corta a 200 pasos y se informa del resto.
- **Model checking**: `QSHARP-MC` añade la regla de *stutter* en los estados finales y las
  proposiciones. La herramienta lo une a metanivel con el módulo de trabajo y ejecuta
  `modelCheck` en el modo sin probabilidades. Así `dist` usa el módulo sin *stutter*.
- **Fase global de un qubit separado**: un bloque `c . |k>` de un solo qubit pasa a `|k>`.
  Como el estado está normalizado, |c| = 1 y c es una fase global. Sin esto, tras medir estados
  con fases de T, smc4qc deja c como una expresión con raíces que no sabe reducir a módulo 1, y
  la siguiente medida se bloquea.
- Entrada: `run(Decls, 'Main)`, o `runWith(Decls, 'Op, args, estadoInicial, siguienteIndice)`
  para partir de estados simbólicos.

Los programas se escriben en módulos que importan **solo** `QSHARP-SYNTAX`. La
yuxtaposición `__` de `NatList` de smc4qc cae en el mismo kind que `Exp` y
produciría ambigüedades de parseo.

## Resultados de las pruebas

- **Bell**: el resultado siempre es `true` (medidas correlacionadas) y los qubits se liberan.
- **Teletransporte** con `a|0⟩+b|1⟩` simbólico: el destino recibe el estado en todas
  las ramas. La rama m1=m2=One da `-(a|0⟩+b|1⟩)`, es decir, una fase global.
- Con `eqUpToPhase` el teletransporte no tiene contraejemplos.
- **Llamadas**: `CountOnes(3)` con bits aleatorios da 0, 1, 2 o 3.
- **GHZ** con `Qubit[3]`: el estado antes de medir es (|000⟩+|111⟩)/√2 y siempre salen 0 o 3 unos.
- **Functores** (`functors.qs`):
  - `Adjoint` deshace operaciones de usuario, también con bucles.
  - `Controlled X` equivale a CNOT y, con dos controles, a Toffoli.
  - `Controlled` funciona sobre operaciones de usuario.
  - `within {H} apply {Z}` da X.
  - T⁴ = Z, y `Adjoint T`/`Adjoint S` deshacen T y S.
- **Distribución exacta**:
  - Bell: `true` con probabilidad 1.
  - Tres bits aleatorios (`random.qs`): 0, 1, 2 y 3 unos con 1/8, 3/8, 3/8 y 1/8, cuando
    `run` muestra cada camino con 1/8.
  - RUS: `One` con 1 − 2⁻⁶⁶ y 2⁻⁶⁶ sin explorar.
  - Teletransporte simbólico: 1, gracias a |a|²+|b|²=1.
- **LTL**:
  - Bell cumple `<> returns(true)` y `[] liveLE(2)`, y no cumple `[] ~ entangled(0)`.
  - El teletransporte cumple `<> [] qubitPh(1, a|0⟩+b|1⟩)`.
  - En RUS, `<> ended` **falla** con el ciclo `H M-Zero Reset-Zero`. Es un camino de
    probabilidad 0 que LTL sin equidad no descarta, mientras que `dist` da 1. Es un buen
    ejemplo para el paper de por qué hacen falta las dos vistas.
- **Bucles**: `while` da 3. RUS en modo `runNP` tiene 5 estados y el resultado es siempre `One`.
  El `fixup` ve las variables del cuerpo y el qubit se libera.

## Limitaciones conocidas y próximos pasos

1. `eqUpToPhase` solo cubre las fases ±1 y ±i; las fases de T necesitarían más.
2. `run` sigue mostrando la probabilidad de un camino; para la distribución está `dist`.
   LTL sin equidad: las propiedades de terminación de bucles RUS fallan por caminos de
   probabilidad 0. Falta añadir equidad o una lógica probabilística.
3. Falta en el subconjunto: callables como valores (`ApplyToEach`), tuplas, `Double` y rotaciones.
   Sin tuplas, `Controlled SWAP([c], (a, b))` no se puede escribir en Q#; la semántica sí lo
   admite con argumentos planos: `(Controlled 'SWAP)(arr(c), a, b)`. Dentro de un `Controlled`
   no se comprueba que el cuerpo no mida, cosa que Q# prohíbe. Las llamadas dentro de
   expresiones solo se admiten a través del frontend, que las extrae a temporales,
   y no en la condición de un `while`.
4. Contraejemplos LTL más informativos: ahora solo se muestran las reglas aplicadas.
5. Mensajes de error del frontend más precisos: ahora se indica el token, no la regla.
6. Fallos de smc4qc encontrados, para comunicar al autor: `q[nil]: nil` tras medir un
   bloque entero, `(i)^*` sin reducir, la puerta T definida con `1 + i` y `Sqrt`/`./`/`.*`/`.+`
   declarados solo sobre `Complex`, por lo que la medida se bloquea cuando la probabilidad
   contiene una raíz.
