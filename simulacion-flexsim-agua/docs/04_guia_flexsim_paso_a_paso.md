# 4. Desarrollo del modelo en FlexSim: guía paso a paso

Hay dos formas de construirlo. Las dos llegan al mismo modelo:

- **Opción A, automática (recomendada):** pegar los scripts de la carpeta [`../flexsim`](../flexsim) en
  la consola de scripts de FlexSim. Arma la línea en segundos.
- **Opción B, manual:** arrastrar y configurar cada objeto. Conviene hacerla al menos una vez para
  entender el modelo (y para explicarlo en clase).

Después de cualquiera de las dos, se hacen los **pasos comunes** (operarios, fallas, tablero de
indicadores, corrida y escenarios).

> Los nombres de menús y botones están en inglés, como aparecen en FlexSim. Pueden cambiar un poco
> entre versiones (2022 a 2026), pero las opciones son las mismas.

---

## 4.0 Antes de empezar

1. Abre FlexSim y crea un modelo nuevo: **File → New Model**.
2. En la ventana **Model Units** elige **Time Units: Minutes** y **Length Units: Meters**.
   Todos los tiempos del modelo están en **minutos**.
3. Guarda el modelo: **File → Save Model As…** → `Linea_Agua_Embotellada.fsm`.

El modelo usa 17 objetos más el navegador de los operarios, dentro del límite de la versión
estudiantil.

---

## 4.1 Opción A: construcción con scripts

### Paso A1. Estructura de la línea (script 1)

1. En la barra superior, presiona **Script** (abre la consola de scripts).
2. Abre [`../flexsim/01_construir_modelo.fs`](../flexsim/01_construir_modelo.fs) con el Bloc de notas,
   copia **todo** y pégalo en la consola con **Ctrl+V**. No lo escribas a mano: el editor completa
   las llaves `{}` solo y se duplicarían.
3. Presiona **Execute** (▶). Debe aparecer un resumen como:
   `Modelo creado. Puerto 1 de Inspeccion -> Buffer_Empaque | Puerto 2 -> Producto_Defectuoso | ...`

El script crea las 17 piezas, las acomoda en línea, hace las conexiones, fija la capacidad de las
colas y pone **tiempos promedio constantes**. Guarda con **Ctrl+S**.

### Paso A2. Prueba de verificación (opcional, recomendada)

Con los tiempos constantes el resultado se puede calcular a mano. Esto **verifica** que el modelo
está bien armado antes de agregar la aleatoriedad (ver [4.4](#44-verificación-y-validación)).

1. Fija el tiempo de corrida en 480 min (paso 9) → **Reset** → **Run**.
2. Compara con los valores esperados de la tabla de la sección 4.4.

### Paso A3. Distribuciones y decisión de calidad (script 2)

1. Guarda el modelo (**Ctrl+S**).
2. Pega [`../flexsim/02_distribuciones_y_ruteo.fs`](../flexsim/02_distribuciones_y_ruteo.fs) en la
   consola → **Execute**.
3. La respuesta muestra el código guardado en *Inter-Arrival Time*, en el *Process Time* de
   Etiquetado y en el *Send To Port* de Inspección. Para comprobarlo, haz clic en `Etiquetado` y
   revisa que su *Process Time* diga `triangular(0.38, 0.52, 0.42, getstream(current))`.

> Si tu versión no acepta el código por script (error en la consola o campos vacíos), escribe las
> expresiones a mano siguiendo los pasos B4 y B5. Es lo mismo.

Continúa con los **pasos comunes (4.3)**.

---

## 4.2 Opción B: construcción manual

### Paso B1. Arrastrar los objetos

Desde la **Library** (panel izquierdo) arrastra al modelo y renombra cada objeto (doble clic → campo
del nombre, o en el panel *Properties* de la derecha):

| Objeto (Library) | Nombre | Posición x, y (m) |
|---|---|---|
| Source | `Recepcion_MP` | 0, 0 |
| Queue | `Almacen_MP` | 4, 0 |
| Processor | `Llenado` | 8, 0 |
| Queue | `Buffer_Tapado` | 12, 0 |
| Processor | `Tapado` | 16, 0 |
| Queue | `Buffer_Etiquetado` | 20, 0 |
| Processor | `Etiquetado` | 24, 0 |
| Queue | `Buffer_Inspeccion` | 28, 0 |
| Processor | `Inspeccion` | 32, 0 |
| Queue | `Buffer_Empaque` | 36, 0 |
| Processor | `Empaque` | 40, 0 |
| Sink | `Producto_Terminado` | 44, 0 |
| Sink | `Producto_Defectuoso` | 32, −6 |
| Operator | `Inspector` | 32, 4 |
| Operator | `Empacador_1` | 39, 4 |
| Operator | `Empacador_2` | 42, 4 |
| Dispatcher | `Equipo_Empaque` | 41, 8 |

La posición se escribe en *Properties → General → Position* (o se acomoda arrastrando).

### Paso B2. Conexiones

**Flujo de botellas:** mantén presionada la tecla **A**, haz clic en el objeto de origen y arrastra
hasta el destino. Conecta en este orden:

```
Recepcion_MP → Almacen_MP → Llenado → Buffer_Tapado → Tapado → Buffer_Etiquetado → Etiquetado
→ Buffer_Inspeccion → Inspeccion → Buffer_Empaque → Empaque → Producto_Terminado
Inspeccion → Producto_Defectuoso        (DESPUÉS de Inspeccion → Buffer_Empaque)
```

El orden importa: la primera conexión que sale de `Inspeccion` es el **puerto 1** (producto
conforme) y la segunda es el **puerto 2** (defectuoso).

**Recursos:** mantén la tecla **S** y arrastra:

- `Inspeccion` → `Inspector`
- `Empaque` → `Equipo_Empaque`

Luego con la tecla **A**: `Equipo_Empaque` → `Empacador_1` y `Equipo_Empaque` → `Empacador_2`.

(Para borrar una conexión equivocada: tecla **Q** para flujo y **W** para recursos, arrastrando
entre los mismos objetos.)

### Paso B3. Capacidad de las colas y estaciones

Selecciona cada objeto y en *Properties* cambia **Maximum Content**:

| Objeto | Maximum Content | Qué representa |
|---|---|---|
| `Almacen_MP` | 1000 | Almacén de botellas vacías (casi ilimitado) |
| `Buffer_Tapado` | 15 | Banda de acumulación antes de la tapadora |
| `Buffer_Etiquetado` | 20 | Banda antes de la etiquetadora |
| `Buffer_Inspeccion` | 15 | Banda antes de inspección |
| `Buffer_Empaque` | 20 | Banda antes de empaque |
| `Empaque` (Processor) | **2** | Dos puestos de empaque, uno por empacador |

Los demás Processor se quedan con Max Content = 1.

### Paso B4. Tiempos (datos de entrada)

En *Properties*, en el campo indicado, abre la flecha del campo y elige
**Statistical Distribution**, o escribe directamente la expresión:

| Objeto | Campo | Expresión FlexSim (minutos) |
|---|---|---|
| `Recepcion_MP` | Inter-Arrival Time | `exponential(0, 0.48, getstream(current))` |
| `Llenado` | Process Time | `triangular(0.30, 0.45, 0.35, getstream(current))` |
| `Tapado` | Process Time | `uniform(0.25, 0.33, getstream(current))` |
| `Etiquetado` | Process Time | `triangular(0.38, 0.52, 0.42, getstream(current))` |
| `Inspeccion` | Process Time | `normal(0.33, 0.03, getstream(current))` |
| `Empaque` | Process Time | `triangular(0.55, 0.80, 0.65, getstream(current))` |

> En FlexSim la triangular es `triangular(mínimo, máximo, moda, stream)`: la **moda va al final**.

### Paso B5. ¿Producto conforme? (Send To Port)

1. Selecciona `Inspeccion` → sección **Flow** (pestaña *Output* en versiones antiguas).
2. En **Send To Port** elige *By Percentage* y captura: puerto 1 = 96 %, puerto 2 = 4 %.
   O escribe directamente: `bernoulli(96, 1, 2, getstream(current))`.

> No dejes el valor por defecto (*First available*): con él, cuando `Buffer_Empaque` se llena las
> botellas buenas se irían al Sink de defectuosos.

---

## 4.3 Pasos comunes

### Paso 6. Operarios en Inspección y Empaque

1. Selecciona `Inspeccion` → sección **Processor** → **Operators**:
   marca **Use Operator(s) for Process**, *Number of Operators* = 1.
2. Selecciona `Empaque` → igual: **Use Operator(s) for Process**, *Number of Operators* = 1.
   Como `Empaque` tiene 2 puestos y está conectado al despachador con 2 empacadores, cada botella
   toma al empacador que esté libre.
3. Selecciona cada operario (`Inspector`, `Empacador_1`, `Empacador_2`) y revisa que **Max Speed**
   sea **60** (m/min = 1 m/s). El script 1 ya lo hace. Si el modelo está en minutos y se deja el
   valor por defecto (2), los operarios caminarían a 2 m/min.

Llenado, Tapado y Etiquetado son máquinas automáticas y no llevan operario por botella.

### Paso 7. Fallas de la tapadora (MTBF/MTTR)

1. Abre el **Toolbox** (*View → Toolbox*) → botón **+** → **Modeling Logic → MTBF MTTR**.
2. Nómbralo `Fallas_Tapadora`.
3. Pestaña **Members**: agrega `Tapado` (botón + o el muestreador).
4. Pestaña **Functions**:
   - *First Failure Time*: `exponential(0, 60, getstream(current))`
   - *Up Time* (tiempo entre fallas, MTBF): `exponential(0, 60, getstream(current))`
   - *Down Time* (tiempo de reparación, MTTR): `triangular(2, 6, 3, getstream(current))`
5. **Down Behavior**: *Stop Object*, con el estado **breakdown**.
6. **Apply → OK**.

Con esto la tapadora se detiene en promedio cada hora durante unos 3.7 minutos, que es una de las
causas de las acumulaciones repentinas que observa la empresa.

### Paso 8. Apariencia (opcional, ayuda a la presentación)

- **Botellas como cilindros:** `Recepcion_MP` → *FlowItem Class* → **Cylinder**.
- **Color según la etapa:** en *Triggers* de cada Processor → **On Exit** → **+** →
  *Visual → Set Object Color* → objeto `item`:
  Llenado = azul (agua), Tapado = blanco, Etiquetado = verde.
- **Producto defectuoso en rojo:** `Producto_Defectuoso` → *Triggers* → **On Entry** →
  *Set Object Color* → rojo.
- Agrega **Text** (en *Visual* de la Library) sobre cada estación con su nombre.

### Paso 9. Tiempo de corrida

1. En la barra de ejecución, junto al reloj (*Run Time*), abre la flecha y elige
   **Stop Time** → **480** (un turno de 8 h).
2. Velocidad (*Run Speed*): 4 a 8 para ver la animación; al máximo para obtener resultados rápido.
3. Siempre **Reset** antes de **Run**.

### Paso 10. Tablero de indicadores (Dashboard)

1. Barra superior → **Dashboards → Add a dashboard**.
2. Desde la Library de gráficas agrega y elige los objetos de cada una:
   - **State Bar** (o *State Pie*) con `Llenado`, `Tapado`, `Etiquetado`, `Inspeccion`, `Empaque`:
     % procesando, bloqueado, ocioso, en falla. Es la gráfica de **utilización**.
   - **State Bar** con `Inspector`, `Empacador_1`, `Empacador_2`: utilización de operarios.
   - **Content vs Time** con las cinco colas: muestra **cuándo y dónde se acumulan** las botellas.
   - **Average Content** / **Maximum Content** de las colas (barras).
   - **Throughput per Hour** de `Producto_Terminado` y `Producto_Defectuoso`.
   - **Average Staytime** de las colas: tiempo de espera antes de cada estación.
3. Corre el modelo y observa cómo se actualizan las gráficas.

### Paso 11. Reporte de indicadores (script 3)

Al terminar la corrida (t = 480), pega
[`../flexsim/03_reporte_kpi.fs`](../flexsim/03_reporte_kpi.fs) en la consola → **Execute**. Imprime
la producción por hora, los defectos, el % de tiempo de cada estación en cada estado, las colas, la
utilización de los operarios, el WIP, el tiempo en el sistema (Ley de Little) y la estación cuello de
botella. Para copiarlo a Excel: *Debug → Output Console*.

### Paso 12. Experimenter: réplicas y escenarios

Una sola corrida no basta, porque el resultado depende de los números aleatorios. Se hacen
**réplicas** y se reportan promedios con intervalo de confianza.

**12.1 Parámetros del modelo** (*Toolbox → Parameters*; los modelos nuevos ya traen esta tabla):

| Parámetro | Valor base | Cómo se conecta al modelo |
|---|---|---|
| `MediaLlegadas` | 0.48 | En *Inter-Arrival Time* de `Recepcion_MP` escribe `exponential(0, Model.parameters.MediaLlegadas, getstream(current))` |
| `Etiquetadoras` | 1 | En el valor del parámetro usa el **muestreador** (gotero) sobre `Etiquetado` y elige **MaxContent**. FlexSim crea el código *On Set* que cambia la capacidad en cada Reset |

**12.2 Medidas de desempeño** (*Toolbox → Performance Measures*): con el muestreador agrega
- entradas (*Input*) de `Producto_Terminado` = botellas producidas,
- entradas de `Producto_Defectuoso`,
- contenido promedio (*Content average*) de `Buffer_Etiquetado` y del `Almacen_MP`,
- tiempo de espera promedio (*Staytime average*) de `Buffer_Etiquetado`,
- % del tiempo *processing* (State) de `Etiquetado`.

**12.3 Experimenter** (*Statistics → Experimenter*):

1. **Scenarios:** un escenario por fila con los valores de los parámetros:

   | Escenario | MediaLlegadas | Etiquetadoras |
   |---|---|---|
   | 1 Base | 0.48 | 1 |
   | 2 Capacidad máxima (alimentación saturada) | 0.20 | 1 |
   | 3 Segunda etiquetadora | 0.48 | 2 |
   | 4 Demanda +20 % | 0.40 | 1 |
   | 5 Demanda +20 % y 2 etiquetadoras | 0.40 | 2 |

2. **Run time / End Time:** 480; **Warmup:** 0; **Replications per Scenario:** 10 a 30.
3. **Run Experiment** → **View Results**: para cada medida aparecen el promedio y el intervalo de
   confianza por escenario. Esos son los resultados para el reporte.

**12.4 Escenarios que cambian la estructura** (se corren con una copia del modelo,
*File → Save Model As…*, y el mismo Experimenter con el escenario base):

| Escenario | Cambio en la copia del modelo |
|---|---|
| 6 Bandas reducidas | *Maximum Content* = 5 en `Buffer_Tapado`, `Buffer_Etiquetado`, `Buffer_Inspeccion` y `Buffer_Empaque` |
| 7 Tapadora sin fallas (mantenimiento preventivo) | Desactiva `Fallas_Tapadora` (casilla *Enabled*) o pon su *Up Time* en 100000 |

---

## 4.4 Verificación y validación

**Verificación** (¿el modelo hace lo que creemos que hace?):

1. Con los tiempos constantes del script 1, sin operarios ni fallas, la línea no forma colas:
   cada estación tarda menos que el tiempo entre llegadas (0.48 min; Empaque 0.667 min, pero con 2
   puestos). El resultado esperado en 480 min es:

   | Medida | Valor esperado | Cálculo |
   |---|---|---|
   | Botellas recibidas | 999 a 1000 | 480 / 0.48 |
   | Botellas terminadas | ≈ 995 | menos las ≈ 4 que siguen en proceso |
   | Defectuosas | 0 | todavía no hay *Send To Port* |
   | % procesando Llenado / Tapado / Etiquetado / Inspección | 76 % / 60 % / 92 % / 69 % | tiempo ÷ 0.48 |
   | Contenido máximo de las colas | 1 | no hay espera |

   El mismo resultado da `python linea_embotellado.py --verificacion`.
2. Revisa con la animación que las botellas sigan la ruta correcta y que aproximadamente 1 de cada
   25 llegue a `Producto_Defectuoso`.
3. Comprueba que la tapadora se detiene (cambia de color/estado) durante las fallas.
4. Con distribuciones, la utilización de cada estación debe acercarse a la teórica
   (tabla 2.4): Etiquetado ≈ 90 %, Llenado ≈ 76 %, etc.

**Validación** (¿el modelo representa el sistema real?):

1. Comparar la producción simulada (≈ 118 botellas buenas/h) con el **conteo real** de botellas
   producidas por hora, y los defectos simulados (≈ 5/h) con el **registro** de calidad.
2. Comparar en qué colas se acumulan botellas en el modelo con lo que se observa en la planta (la
   empresa reporta acumulaciones entre algunas estaciones).
3. Si hay datos reales, usar una prueba t entre la producción real y la simulada por turno.
4. Comparar con el modelo gemelo en Python ([`../validacion_python`](../validacion_python)): los dos
   deben dar valores parecidos (dentro de los intervalos de confianza).

---

## 4.5 Problemas frecuentes

| Síntoma | Causa probable | Solución |
|---|---|---|
| No sale nada de la línea | Falta una conexión | Revisa las flechas con la tecla A; el Source debe estar conectado al almacén |
| Las botellas buenas llegan a `Producto_Defectuoso` | *Send To Port* en *First available* o puertos invertidos | Paso B5; conecta primero Inspección → Buffer_Empaque |
| Inspección o Empaque nunca trabajan | Marcaste *Use Operator(s)* pero falta la conexión S | Conecta con S Inspección → Inspector y Empaque → Equipo_Empaque |
| Los operarios caminan lentísimo | Modelo en minutos con *Max Speed* = 2 | *Max Speed* = 60 |
| Los tiempos parecen 60 veces más rápidos o lentos | Unidades del modelo en segundos | Crea el modelo con *Time Units = Minutes* |
| Error con `triangular` | Parámetros en el orden de los libros | Orden FlexSim: mínimo, máximo, moda |
| Cada corrida da exactamente lo mismo | Es normal: FlexSim repite la semilla en cada Reset | Para variar resultados usa el Experimenter (cada réplica usa otra semilla) |
