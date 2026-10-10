/* =====================================================================
   LÍNEA DE PRODUCCIÓN DE AGUA EMBOTELLADA - SCRIPT 3 DE 3
   Reporte de indicadores (KPI) al terminar una corrida.

   Uso: Reset -> Run hasta 480 min (un turno) -> Script > pegar > Execute.
   El reporte sale en la consola del script y en Debug > Output Console
   (de ahí se puede copiar a Excel o al reporte).

   Estados de FlexSim usados: STATE_IDLE (ocioso), STATE_PROCESSING
   (procesando) y STATE_BLOCKED (bloqueado: no hay lugar en la cola
   siguiente). "Otros" = 100 % - los tres anteriores = tiempo en falla
   (MTBF/MTTR) + esperando operario + traslado del operario.
   ===================================================================== */

double T = Model.time;
if (T <= 0) {
    return "Primero corre el modelo (Reset y Run hasta 480 min).";
}
double horas = T / 60;

Object recepcion = Model.find("Recepcion_MP");
Object terminado = Model.find("Producto_Terminado");
Object defectuoso = Model.find("Producto_Defectuoso");

double llegadas = recepcion.stats.output.value;
double buenas = terminado.stats.input.value;
double malas = defectuoso.stats.input.value;

string r = "===== KPI LINEA DE AGUA EMBOTELLADA (t = " + string.fromNum(T, 1) + " min) =====\n";
r = r + "Botellas recibidas:        " + string.fromNum(llegadas, 0) + "\n";
r = r + "Botellas terminadas:       " + string.fromNum(buenas, 0)
      + "  (" + string.fromNum(buenas / horas, 1) + " botellas/h)\n";
r = r + "Botellas defectuosas:      " + string.fromNum(malas, 0)
      + "  (" + string.fromNum(malas / horas, 1) + " botellas/h, "
      + string.fromNum(100 * malas / (buenas + malas + 0.000001), 1) + " %)\n";

/* ---- Estaciones: % del tiempo en cada estado ---- */
r = r + "\nESTACION      Procesando  Bloqueado  Ocioso  Otros(falla/espera operario)  | Utilizacion por servidor\n";
Array estaciones = ["Llenado", "Tapado", "Etiquetado", "Inspeccion", "Empaque"];
double wip = 0;
string cuello = "";
double maxUtil = 0;
for (int i = 1; i <= estaciones.length; i++) {
    string nom = estaciones[i];
    Object e = Model.find(nom);
    double k = e.getProperty("MaxContent");    /* servidores en paralelo */
    if (k < 1) {
        k = 1;
    }
    double proc = e.stats.state().getTotalTimeAt(STATE_PROCESSING) / T;
    double bloq = e.stats.state().getTotalTimeAt(STATE_BLOCKED) / T;
    double ocio = e.stats.state().getTotalTimeAt(STATE_IDLE) / T;
    double otros = 1 - proc - bloq - ocio;
    /* Utilización por servidor: con 1 servidor = % procesando.
       Con k puestos (Empaque) el estado "processing" se marca si AL MENOS
       un puesto trabaja, así que se usa contenido promedio / k. */
    double util = proc;
    if (k > 1) {
        util = e.stats.content.average / k;
    }
    wip = wip + e.stats.content.average;
    if (util > maxUtil) {
        maxUtil = util;
        cuello = nom;
    }
    r = r + nom + "   " + string.fromNum(100 * proc, 1) + "%   " + string.fromNum(100 * bloq, 1)
          + "%   " + string.fromNum(100 * ocio, 1) + "%   " + string.fromNum(100 * otros, 1)
          + "%   | " + string.fromNum(100 * util, 1) + "%\n";
}

/* ---- Colas: acumulación antes de cada estación ---- */
r = r + "\nCOLA                 Promedio   Maximo   Espera prom (min)\n";
Array colas = ["Almacen_MP", "Buffer_Tapado", "Buffer_Etiquetado", "Buffer_Inspeccion", "Buffer_Empaque"];
for (int j = 1; j <= colas.length; j++) {
    string nq = colas[j];
    Object q = Model.find(nq);
    wip = wip + q.stats.content.average;
    r = r + nq + "   " + string.fromNum(q.stats.content.average, 2) + "   "
          + string.fromNum(q.stats.content.maximum, 0) + "   "
          + string.fromNum(q.stats.staytime.average, 2) + "\n";
}

/* ---- Operarios ---- */
r = r + "\nOPERARIO        Utilizacion (1 - ocioso)\n";
Array ops = ["Inspector", "Empacador_1", "Empacador_2"];
for (int m = 1; m <= ops.length; m++) {
    string no = ops[m];
    Object op = Model.find(no);
    double ocioOp = op.stats.state().getTotalTimeAt(STATE_IDLE) / T;
    r = r + no + "   " + string.fromNum(100 * (1 - ocioOp), 1) + "%\n";
}

/* ---- Ley de Little: tiempo en sistema = WIP / tasa de salida ---- */
double tasaSalida = (buenas + malas) / T;   /* botellas por minuto */
r = r + "\nWIP promedio (botellas en el sistema): " + string.fromNum(wip, 1) + "\n";
if (tasaSalida > 0) {
    r = r + "Tiempo promedio en el sistema (Little): " + string.fromNum(wip / tasaSalida, 2) + " min\n";
}
r = r + "Estacion con mayor utilizacion (cuello de botella): " + cuello
      + " (" + string.fromNum(100 * maxUtil, 1) + "%)\n";

print(r);
return r;
