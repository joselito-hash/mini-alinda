# 1. Conceptualización del modelo

## 1.1 Definición del problema

Una empresa de agua embotellada observa que **en algunos momentos se acumulan botellas entre
estaciones** de su línea. Quiere conocer:

1. La **capacidad de producción** de la línea (botellas/hora).
2. El **nivel de utilización** de sus recursos (máquinas y operarios).
3. Los **cuellos de botella**, es decir, las estaciones que limitan el flujo y generan colas.
4. El efecto de **escenarios de mejora** antes de invertir.

## 1.2 Objetivo del estudio

Construir en FlexSim un modelo de simulación de eventos discretos de la línea
*Recepción de materia prima → Llenado → Tapado → Etiquetado → Inspección → Empaque* que permita
medir producción, utilizaciones, colas y tiempos de espera, y comparar escenarios.

## 1.3 Alcance y fronteras del sistema

| Dentro del modelo | Fuera del modelo |
|---|---|
| Llegada de botellas vacías a la línea | Producción y compra de las botellas (proveedor) |
| Llenado, tapado, etiquetado, inspección y empaque | Tratamiento/purificación del agua (se supone siempre disponible) |
| Colas o bandas de acumulación entre estaciones | Almacén de producto terminado y distribución |
| Fallas de la tapadora | Fallas del resto de las máquinas (no se registraron) |
| Rechazo de botellas no conformes | Retrabajo de las botellas defectuosas |
| Operarios de inspección y empaque | Supervisión, mantenimiento y personal administrativo |

**Horizonte de simulación:** un turno de 8 horas (480 minutos), iniciando con la línea vacía
(simulación con condición de término). **Unidad de tiempo:** minutos.

## 1.4 Elementos del sistema

| Elemento | En este sistema | Objeto en FlexSim |
|---|---|---|
| **Entidad** (lo que fluye) | Botella | *Flowitem* (Box) creado por el Source |
| **Atributos** de la entidad | Hora de llegada, estado de calidad (conforme / defectuosa) | Etiquetas (*labels*) o puerto de salida |
| **Llegadas** | Botellas vacías que llegan del almacén de materia prima | `Recepcion_MP` (Source) |
| **Actividades** (consumen tiempo) | Llenar, tapar, etiquetar, inspeccionar, empacar | `Llenado`, `Tapado`, `Etiquetado`, `Inspeccion`, `Empaque` (Processor) |
| **Recursos fijos** | Llenadora, tapadora, etiquetadora (máquinas automáticas), mesa de inspección, mesa de empaque | Processor |
| **Recursos móviles / personal** | 1 inspector de calidad, 2 empacadores | `Inspector`, `Empacador_1`, `Empacador_2` (Operator) + `Equipo_Empaque` (Dispatcher) |
| **Colas** (acumulación) | Almacén de materia prima y bandas de acumulación entre máquinas | `Almacen_MP`, `Buffer_Tapado`, `Buffer_Etiquetado`, `Buffer_Inspeccion`, `Buffer_Empaque` (Queue) |
| **Decisión** | ¿Hay capacidad para continuar? / ¿Producto conforme? | Capacidad máxima de las colas (bloqueo) / *Send To Port* de Inspección |
| **Salidas** | Producto terminado, producto defectuoso | `Producto_Terminado`, `Producto_Defectuoso` (Sink) |
| **Interrupciones** | Fallas de la tapadora | Herramienta MTBF/MTTR |

## 1.5 Eventos del sistema

| Evento | Qué cambia en el sistema |
|---|---|
| Llegada de una botella | +1 botella en el almacén de materia prima |
| Inicio de proceso en una estación | La estación pasa de *ociosa* a *procesando*; −1 en la cola anterior |
| Fin de proceso | La botella intenta pasar a la cola siguiente; si está llena la estación queda **bloqueada** |
| Fin de inspección | Se decide si la botella es conforme (96 %) o defectuosa (4 %) |
| Falla de la tapadora | La tapadora se detiene; la botella en proceso espera la reparación |
| Fin de reparación | La tapadora continúa con el tiempo de proceso que le faltaba |
| Salida de botella terminada / defectuosa | +1 en el contador de producción o de rechazo |

## 1.6 Variables

**Variables de entrada (datos):** tiempo entre llegadas, tiempos de llenado, tapado, etiquetado,
inspección y empaque, tiempo entre fallas y de reparación de la tapadora, porcentaje de defectos,
número de operarios y capacidad de cada cola. Los valores están en
[02_coleccion_datos.md](02_coleccion_datos.md).

**Variables de estado (cambian durante la simulación):** número de botellas en cada cola, estado de
cada estación (ociosa, procesando, bloqueada, en falla, esperando operario), estado de cada operario.

**Variables de decisión (lo que se cambia en los escenarios):** número de etiquetadoras, tasa de
llegada (demanda), tamaño de las colas, mantenimiento de la tapadora.

**Variables de respuesta (indicadores, KPI):**

| Indicador | Unidad | Cómo se mide en FlexSim |
|---|---|---|
| Producción (*throughput*) | botellas/hora | Entradas a `Producto_Terminado` ÷ horas simuladas |
| Botellas defectuosas | botellas/hora | Entradas a `Producto_Defectuoso` ÷ horas |
| Utilización de cada estación | % | Gráfica *State* / script 3 (% procesando) |
| Tiempo bloqueado | % | Estado *blocked* de cada Processor |
| Utilización de operarios | % | 100 % − % ocioso del Operator |
| Contenido promedio y máximo de cada cola | botellas | `stats.content.average` / `maximum` |
| Tiempo promedio de espera en cola | min | `stats.staytime.average` de cada Queue |
| Tiempo promedio en el sistema | min | Ley de Little (WIP ÷ tasa de salida) |
| Trabajo en proceso (WIP) | botellas | Suma de contenidos promedio |

## 1.7 Supuestos y simplificaciones

1. Hay siempre agua tratada, tapas y etiquetas disponibles (no se modelan sus inventarios).
2. Cada botella se procesa de manera individual; el empaque se mide por botella (tiempo por botella
   colocada en la caja).
3. Solo la tapadora tiene fallas significativas (según el registro de mantenimiento supuesto).
4. Las botellas defectuosas salen del sistema (no hay retrabajo).
5. Las colas se atienden en orden de llegada (FIFO).
6. Llenado, tapado y etiquetado son máquinas automáticas: no requieren un operario por botella.
   Inspección y empaque son manuales.
7. Los operarios se desplazan a 1 m/s y trabajan junto a su estación (el traslado es despreciable).
8. Los tiempos son independientes entre sí y entre botellas.
9. La línea empieza vacía al inicio del turno.

> **Importante:** los valores numéricos son **supuestos razonables para el ejercicio**, porque la
> actividad no entrega datos. Si el profesor o la empresa proporcionan cronometrajes, solo hay que
> reemplazarlos en la tabla de datos, en los scripts y en `validacion_python/linea_embotellado.py`.
