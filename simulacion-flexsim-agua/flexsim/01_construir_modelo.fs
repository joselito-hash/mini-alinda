/* =====================================================================
   LÍNEA DE PRODUCCIÓN DE AGUA EMBOTELLADA - SCRIPT 1 DE 3
   Construye la estructura del modelo en FlexSim:
     objetos, posiciones, conexiones, capacidades de cola,
     operarios y tiempos de proceso PROMEDIO (constantes).
   El script 2 cambia los tiempos constantes por distribuciones.

   Requisitos:
     - FlexSim 2022 o superior (probado el API en FlexSim 2026 Student).
     - Modelo NUEVO creado con: Time units = Minutes, Length units = Meters.
   Cómo ejecutarlo:
     Barra superior > Script  ->  pegar TODO este texto con Ctrl+V
     (no lo escribas a mano: el editor autocompleta las llaves {})
     -> botón Execute (▶). Al final aparece un resumen en la consola.
   Se puede volver a ejecutar: borra los objetos anteriores con los
   mismos nombres y los crea de nuevo.
   ===================================================================== */

/* ---------- 0. Borrar objetos previos con los mismos nombres ---------- */
Array nombres = ["Recepcion_MP", "Almacen_MP", "Llenado", "Buffer_Tapado", "Tapado",
                 "Buffer_Etiquetado", "Etiquetado", "Buffer_Inspeccion", "Inspeccion",
                 "Buffer_Empaque", "Empaque", "Producto_Terminado", "Producto_Defectuoso",
                 "Inspector", "Equipo_Empaque", "Empacador_1", "Empacador_2"];
for (int i = 1; i <= nombres.length; i++) {
    string nom = nombres[i];
    treenode viejo = Model.find(nom);
    if (viejo != NULL) {
        destroyobject(viejo);
    }
}

/* ---------- 1. Crear y ubicar los objetos (x, y en metros) ---------- */
/* Entrada: recepción de materia prima (botellas vacías) */
Object recepcion = Object.create("Source");
recepcion.name = "Recepcion_MP";
recepcion.setLocation(0, 0, 0);

/* Almacén de materia prima = cola antes de Llenado */
Object almacen = Object.create("Queue");
almacen.name = "Almacen_MP";
almacen.setLocation(4, 0, 0);

Object llenado = Object.create("Processor");
llenado.name = "Llenado";
llenado.setLocation(8, 0, 0);

Object bufTapado = Object.create("Queue");
bufTapado.name = "Buffer_Tapado";
bufTapado.setLocation(12, 0, 0);

Object tapado = Object.create("Processor");
tapado.name = "Tapado";
tapado.setLocation(16, 0, 0);

Object bufEtiq = Object.create("Queue");
bufEtiq.name = "Buffer_Etiquetado";
bufEtiq.setLocation(20, 0, 0);

Object etiquetado = Object.create("Processor");
etiquetado.name = "Etiquetado";
etiquetado.setLocation(24, 0, 0);

Object bufInsp = Object.create("Queue");
bufInsp.name = "Buffer_Inspeccion";
bufInsp.setLocation(28, 0, 0);

Object inspeccion = Object.create("Processor");
inspeccion.name = "Inspeccion";
inspeccion.setLocation(32, 0, 0);

Object bufEmp = Object.create("Queue");
bufEmp.name = "Buffer_Empaque";
bufEmp.setLocation(36, 0, 0);

Object empaque = Object.create("Processor");
empaque.name = "Empaque";
empaque.setLocation(40, 0, 0);

/* Salidas: producto terminado y producto defectuoso */
Object terminado = Object.create("Sink");
terminado.name = "Producto_Terminado";
terminado.setLocation(44, 0, 0);

Object defectuoso = Object.create("Sink");
defectuoso.name = "Producto_Defectuoso";
defectuoso.setLocation(32, -6, 0);

/* Recursos humanos: 1 inspector de calidad y 2 empacadores con su despachador */
Object inspector = Object.create("Operator");
inspector.name = "Inspector";
inspector.setLocation(32, 4, 0);

Object equipoEmpaque = Object.create("Dispatcher");
equipoEmpaque.name = "Equipo_Empaque";
equipoEmpaque.setLocation(41, 8, 0);

Object empacador1 = Object.create("Operator");
empacador1.name = "Empacador_1";
empacador1.setLocation(39, 4, 0);

Object empacador2 = Object.create("Operator");
empacador2.name = "Empacador_2";
empacador2.setLocation(42, 4, 0);

/* ---------- 2. Conexiones de flujo (equivale a arrastrar con la tecla A) ---------- */
contextdragconnection(recepcion, almacen, "A");
contextdragconnection(almacen, llenado, "A");
contextdragconnection(llenado, bufTapado, "A");
contextdragconnection(bufTapado, tapado, "A");
contextdragconnection(tapado, bufEtiq, "A");
contextdragconnection(bufEtiq, etiquetado, "A");
contextdragconnection(etiquetado, bufInsp, "A");
contextdragconnection(bufInsp, inspeccion, "A");
/* IMPORTANTE: el ORDEN define los puertos de salida de Inspección
   puerto 1 = producto conforme (va a empaque), puerto 2 = defectuoso */
contextdragconnection(inspeccion, bufEmp, "A");
contextdragconnection(inspeccion, defectuoso, "A");
contextdragconnection(bufEmp, empaque, "A");
contextdragconnection(empaque, terminado, "A");

/* ---------- 3. Conexiones de recursos (equivale a arrastrar con la tecla S) ---------- */
contextdragconnection(inspeccion, inspector, "S");       /* Inspección usa al inspector */
contextdragconnection(empaque, equipoEmpaque, "S");      /* Empaque pide operarios al despachador */
contextdragconnection(equipoEmpaque, empacador1, "A");   /* el despachador asigna a los 2 empacadores */
contextdragconnection(equipoEmpaque, empacador2, "A");

/* ---------- 4. Capacidades (Max Content) ---------- */
almacen.setProperty("MaxContent", 1000);    /* almacén de botellas vacías (prácticamente ilimitado) */
bufTapado.setProperty("MaxContent", 15);    /* banda de acumulación antes de la tapadora */
bufEtiq.setProperty("MaxContent", 20);      /* banda de acumulación antes de la etiquetadora */
bufInsp.setProperty("MaxContent", 15);
bufEmp.setProperty("MaxContent", 20);
empaque.setProperty("MaxContent", 2);       /* 2 puestos de empaque (uno por empacador) */

/* ---------- 5. Tiempos PROMEDIO en minutos (el script 2 los vuelve aleatorios) ---------- */
recepcion.setProperty("InterArrivalTime", 0.48);   /* 125 botellas/hora */
llenado.setProperty("ProcessTime", 0.3667);
tapado.setProperty("ProcessTime", 0.29);
etiquetado.setProperty("ProcessTime", 0.44);
inspeccion.setProperty("ProcessTime", 0.33);
empaque.setProperty("ProcessTime", 0.6667);

/* ---------- 6. Velocidad de los operarios: 60 m/min (= 1 m/s) ----------
   En un modelo en minutos la velocidad por defecto (2) sería 2 m/min.   */
int velocidadOk = 0;
treenode vel1 = inspector.find(">variables/maxspeed");
if (vel1 != NULL) {
    vel1.value = 60;
    velocidadOk++;
}
treenode vel2 = empacador1.find(">variables/maxspeed");
if (vel2 != NULL) {
    vel2.value = 60;
    velocidadOk++;
}
treenode vel3 = empacador2.find(">variables/maxspeed");
if (vel3 != NULL) {
    vel3.value = 60;
    velocidadOk++;
}

/* ---------- 7. Resumen ---------- */
string resumen = "Modelo creado. Puerto 1 de Inspeccion -> " + inspeccion.outObjects[1].name
    + " | Puerto 2 -> " + inspeccion.outObjects[2].name
    + " | Operarios con velocidad 60 m/min: " + string.fromNum(velocidadOk, 0) + " de 3"
    + " | FALTA (manual): marcar 'Use Operator(s) for Process' en Inspeccion y Empaque"
    + " y ejecutar el script 2.";
print(resumen);
return resumen;
