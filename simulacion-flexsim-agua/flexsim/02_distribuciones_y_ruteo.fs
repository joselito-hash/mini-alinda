/* =====================================================================
   LÍNEA DE PRODUCCIÓN DE AGUA EMBOTELLADA - SCRIPT 2 DE 3
   Cambia los tiempos promedio por DISTRIBUCIONES de probabilidad y
   programa la decisión "¿Producto conforme?" en Inspección.

   ANTES DE EJECUTARLO: guarda el modelo (Ctrl+S).
   Cómo ejecutarlo: Script > pegar con Ctrl+V > Execute (▶).

   Notas de FlexSim usadas aquí:
     triangular(mínimo, MÁXIMO, MODA, stream)   <- ojo con el orden
     uniform(mínimo, máximo, stream)
     normal(media, desviación, stream)
     exponential(localización, media, stream)
     bernoulli(PORCENTAJE 0-100, valor si éxito, valor si fracaso, stream)
   getstream(current) da a cada objeto su propia secuencia aleatoria.

   Si tu versión no acepta el código por script, escribe a mano la
   expresión de la columna "Expresión FlexSim" de la tabla de la guía
   (docs/04_guia_flexsim_paso_a_paso.md, paso 5) en cada campo.
   ===================================================================== */

Object recepcion = Model.find("Recepcion_MP");
Object llenado = Model.find("Llenado");
Object tapado = Model.find("Tapado");
Object etiquetado = Model.find("Etiquetado");
Object inspeccion = Model.find("Inspeccion");
Object empaque = Model.find("Empaque");

if (recepcion == NULL || empaque == NULL || inspeccion == NULL) {
    return "No encuentro los objetos. Ejecuta primero 01_construir_modelo.fs";
}

/* Encabezado que define 'current' (el objeto) e 'item' (la botella) */
string enc = "Object current = ownerobject(c); Object item = param(1); ";

/* Tiempo entre llegadas: exponencial con media 0.48 min (125 botellas/h) */
recepcion.setProperty("InterArrivalTime",
    "Object current = ownerobject(c); return exponential(0, 0.48, getstream(current));");

/* Tiempos de proceso (minutos por botella) */
llenado.setProperty("ProcessTime", enc + "return triangular(0.30, 0.45, 0.35, getstream(current));");
tapado.setProperty("ProcessTime", enc + "return uniform(0.25, 0.33, getstream(current));");
etiquetado.setProperty("ProcessTime", enc + "return triangular(0.38, 0.52, 0.42, getstream(current));");
inspeccion.setProperty("ProcessTime", enc + "return normal(0.33, 0.03, getstream(current));");
empaque.setProperty("ProcessTime", enc + "return triangular(0.55, 0.80, 0.65, getstream(current));");

/* ¿Producto conforme?  96 % -> puerto 1 (Buffer_Empaque)
                         4 % -> puerto 2 (Producto_Defectuoso) */
inspeccion.setProperty("SendToPort", enc + "return bernoulli(96, 1, 2, getstream(current));");

/* Verificación: se leen de vuelta los valores guardados */
string a = recepcion.getProperty("InterArrivalTime");
string b = etiquetado.getProperty("ProcessTime");
string d = inspeccion.getProperty("SendToPort");
string resumen = "Llegadas: " + a + "  ||  Etiquetado: " + b + "  ||  Send To Port: " + d;
print(resumen);
return resumen;
