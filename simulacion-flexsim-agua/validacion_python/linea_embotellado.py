"""
Modelo de validación (gemelo en Python/SimPy) de la línea de agua embotellada.

Reproduce la misma lógica que el modelo de FlexSim:

    Recepción MP (Source) -> Almacén MP (Queue) -> Llenado -> Buffer -> Tapado
    -> Buffer -> Etiquetado -> Buffer -> Inspección -> {Empaque | Defectuoso}
    -> Buffer -> Empaque (2 empacadores) -> Producto terminado (Sink)

Semántica igual a FlexSim:
  * Las colas (Queue) tienen capacidad máxima; si una cola está llena, la
    estación anterior queda BLOQUEADA con la botella adentro.
  * La Tapadora tiene fallas (MTBF/MTTR); durante la falla la botella en
    proceso se detiene y continúa con el tiempo restante al repararse.
  * Inspección envía el 4 % de las botellas al Sink de defectuosos
    (Send To Port = bernoulli(96, 1, 2)).

Unidad de tiempo: MINUTOS (igual que el modelo de FlexSim).

Uso:
    python linea_embotellado.py                 # todos los escenarios, 30 réplicas
    python linea_embotellado.py --reps 10       # menos réplicas
    python linea_embotellado.py --escenario base
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from copy import deepcopy
from dataclasses import dataclass, field

import numpy as np
import simpy

try:
    from scipy import stats as sps
except ImportError:  # scipy es opcional
    sps = None

DIR_RESULTADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultados")

# ---------------------------------------------------------------------------
# 1. Datos de entrada (mismos valores que datos/parametros_modelo.csv)
#    Distribuciones expresadas como en numpy:
#       ("tri", minimo, moda, maximo)   ("uni", a, b)
#       ("exp", media)                  ("norm", media, desv)
#       ("const", valor)
# ---------------------------------------------------------------------------
BASE = {
    "nombre": "1. Base (situación actual)",
    "duracion": 480.0,            # un turno de 8 h
    "llegadas": ("exp", 0.48),    # tiempo entre llegadas de botellas vacías
    "estaciones": {
        #  nombre       distribución                    servidores
        "Llenado":    {"dist": ("tri", 0.30, 0.35, 0.45), "servidores": 1},
        "Tapado":     {"dist": ("uni", 0.25, 0.33),       "servidores": 1},
        "Etiquetado": {"dist": ("tri", 0.38, 0.42, 0.52), "servidores": 1},
        "Inspeccion": {"dist": ("norm", 0.33, 0.03),      "servidores": 1},
        "Empaque":    {"dist": ("tri", 0.55, 0.65, 0.80), "servidores": 2},
    },
    # Capacidad máxima de cada cola (lo que cabe ANTES de cada estación)
    "colas": {
        "Almacen_MP": 1000,
        "Buffer_Tapado": 15,
        "Buffer_Etiquetado": 20,
        "Buffer_Inspeccion": 15,
        "Buffer_Empaque": 20,
    },
    "prob_defecto": 0.04,
    # Fallas de la tapadora: tiempo entre fallas ~ Exp(60) y reparación ~ Tri(2,3,6)
    "fallas": {"Tapado": {"tbf": ("exp", 60.0), "ttr": ("tri", 2.0, 3.0, 6.0)}},
}

ORDEN_ESTACIONES = ["Llenado", "Tapado", "Etiquetado", "Inspeccion", "Empaque"]
COLA_ANTES = {
    "Llenado": "Almacen_MP",
    "Tapado": "Buffer_Tapado",
    "Etiquetado": "Buffer_Etiquetado",
    "Inspeccion": "Buffer_Inspeccion",
    "Empaque": "Buffer_Empaque",
}


def escenario(nombre: str, **cambios) -> dict:
    """Crea un escenario a partir del caso base aplicando cambios."""
    e = deepcopy(BASE)
    e["nombre"] = nombre
    for clave, valor in cambios.items():
        if clave == "servidores":
            for est, n in valor.items():
                e["estaciones"][est]["servidores"] = n
        elif clave == "colas":
            e["colas"].update(valor)
        else:
            e[clave] = valor
    return e


ESCENARIOS = {
    "base": BASE,
    "capacidad": escenario("2. Capacidad máxima (alimentación saturada)", llegadas=("exp", 0.20)),
    "etiq2": escenario("3. Segunda etiquetadora", servidores={"Etiquetado": 2}),
    "demanda": escenario("4. Demanda +20 %", llegadas=("exp", 0.40)),
    "demanda_etiq2": escenario("5. Demanda +20 % con 2 etiquetadoras",
                               llegadas=("exp", 0.40), servidores={"Etiquetado": 2}),
    "buffers5": escenario("6. Buffers reducidos (5 botellas)",
                          colas={"Buffer_Tapado": 5, "Buffer_Etiquetado": 5,
                                 "Buffer_Inspeccion": 5, "Buffer_Empaque": 5}),
    "sin_fallas": escenario("7. Tapadora sin fallas (mantenimiento preventivo)", fallas={}),
}


# Verificación: tiempos constantes (= modelo de FlexSim después del script 1,
# antes de cargar distribuciones, operarios y fallas). Resultado predecible a mano.
VERIFICACION = escenario(
    "Verificación determinista (tiempos constantes)",
    llegadas=("const", 0.48), prob_defecto=0.0, fallas={},
)
for _n, _t in {"Llenado": 0.3667, "Tapado": 0.29, "Etiquetado": 0.44,
               "Inspeccion": 0.33, "Empaque": 0.6667}.items():
    VERIFICACION["estaciones"][_n]["dist"] = ("const", _t)


# ---------------------------------------------------------------------------
# 2. Utilidades
# ---------------------------------------------------------------------------
def muestrear(rng: np.random.Generator, dist: tuple) -> float:
    tipo = dist[0]
    if tipo == "const":
        return float(dist[1])
    if tipo == "exp":
        return float(rng.exponential(dist[1]))
    if tipo == "tri":
        return float(rng.triangular(dist[1], dist[2], dist[3]))
    if tipo == "uni":
        return float(rng.uniform(dist[1], dist[2]))
    if tipo == "norm":
        return max(0.0, float(rng.normal(dist[1], dist[2])))
    raise ValueError(f"Distribución desconocida: {dist}")


def media_dist(dist: tuple) -> float:
    tipo = dist[0]
    if tipo in ("const", "exp"):
        return dist[1]
    if tipo == "tri":
        return (dist[1] + dist[2] + dist[3]) / 3
    if tipo == "uni":
        return (dist[1] + dist[2]) / 2
    if tipo == "norm":
        return dist[1]
    raise ValueError(dist)


class ColaMonitoreada(simpy.Store):
    """Store de SimPy que registra el contenido promedio/máximo y la espera."""

    def __init__(self, env, nombre, capacidad):
        super().__init__(env, capacity=capacidad)
        self.nombre = nombre
        self._area = 0.0
        self._t_ult = 0.0
        self.maximo = 0
        self.esperas: list[float] = []
        self.serie: list[tuple[float, int]] = [(0.0, 0)]

    def _registrar(self):
        ahora = self._env.now
        self._area += len(self.items) * (ahora - self._t_ult)
        self._t_ult = ahora

    def _do_put(self, event):
        self._registrar()
        resultado = super()._do_put(event)
        if event.triggered:
            event.item["t_cola"] = self._env.now
            self.maximo = max(self.maximo, len(self.items))
            self.serie.append((self._env.now, len(self.items)))
        return resultado

    def _do_get(self, event):
        self._registrar()
        resultado = super()._do_get(event)
        if event.triggered:
            item = event.value
            self.esperas.append(self._env.now - item["t_cola"])
            self.serie.append((self._env.now, len(self.items)))
        return resultado

    def promedio(self, t_fin):
        return (self._area + len(self.items) * (t_fin - self._t_ult)) / t_fin


ESTADOS = ("ocioso", "procesando", "bloqueado", "falla")


@dataclass
class Servidor:
    estado: str = "ocioso"
    t_estado: float = 0.0
    acumulado: dict = field(default_factory=lambda: {e: 0.0 for e in ESTADOS})
    proceso: simpy.Process | None = None

    def cambiar(self, ahora, nuevo):
        self.acumulado[self.estado] += ahora - self.t_estado
        self.estado, self.t_estado = nuevo, ahora

    def cerrar(self, ahora):
        self.cambiar(ahora, self.estado)


class Estacion:
    def __init__(self, env, nombre, cfg, entrada, rng):
        self.env, self.nombre, self.cfg, self.entrada, self.rng = env, nombre, cfg, entrada, rng
        self.salida = None          # cola siguiente (o función de ruteo)
        self.caida = False
        self.evento_reparada = env.event()
        self.tiempo_caida = 0.0
        self.n_fallas = 0
        self.intervalos_falla: list[tuple[float, float]] = []
        self.procesadas = 0
        self.servidores = [Servidor() for _ in range(cfg["servidores"])]
        for s in self.servidores:
            s.proceso = env.process(self._trabajar(s))

    def _esperar_reparacion(self, s):
        while self.caida:
            s.cambiar(self.env.now, "falla")
            yield self.evento_reparada

    def _trabajar(self, s: Servidor):
        env = self.env
        while True:
            s.cambiar(env.now, "falla" if self.caida else "ocioso")
            item = yield self.entrada.get()
            yield from self._esperar_reparacion(s)
            s.cambiar(env.now, "procesando")
            restante = muestrear(self.rng, self.cfg["dist"])
            while restante > 1e-12:
                inicio = env.now
                try:
                    yield env.timeout(restante)
                    restante = 0.0
                except simpy.Interrupt:          # llegó una falla
                    restante -= env.now - inicio
                    yield from self._esperar_reparacion(s)
                    s.cambiar(env.now, "procesando")
            self.procesadas += 1
            destino = self.salida(item) if callable(self.salida) else self.salida
            s.cambiar(env.now, "bloqueado")
            yield destino.put(item)

    def fallas(self, tbf, ttr):
        env = self.env
        while True:
            yield env.timeout(muestrear(self.rng, tbf))
            self.caida, self.n_fallas = True, self.n_fallas + 1
            self.evento_reparada = env.event()
            for s in self.servidores:
                if s.estado == "procesando":
                    s.proceso.interrupt()
                elif s.estado == "ocioso":
                    s.cambiar(env.now, "falla")
            duracion = muestrear(self.rng, ttr)
            self.tiempo_caida += duracion
            self.intervalos_falla.append((env.now, env.now + duracion))
            yield env.timeout(duracion)
            self.caida = False
            for s in self.servidores:
                if s.estado == "falla":
                    s.cambiar(env.now, "ocioso")
            self.evento_reparada.succeed()


class Sumidero:
    def __init__(self, env):
        self.env = env
        self.items = []

    def put(self, item):
        item["t_salida"] = self.env.now
        self.items.append(item)
        return self.env.timeout(0)


# ---------------------------------------------------------------------------
# 3. Una réplica
# ---------------------------------------------------------------------------
def correr_replica(esc: dict, semilla: int, guardar_series=False) -> dict:
    env = simpy.Environment()
    rng = np.random.default_rng(semilla)
    T = esc["duracion"]

    colas = {n: ColaMonitoreada(env, n, c) for n, c in esc["colas"].items()}
    terminado, defectuoso = Sumidero(env), Sumidero(env)

    est = {n: Estacion(env, n, esc["estaciones"][n], colas[COLA_ANTES[n]], rng)
           for n in ORDEN_ESTACIONES}
    est["Llenado"].salida = colas["Buffer_Tapado"]
    est["Tapado"].salida = colas["Buffer_Etiquetado"]
    est["Etiquetado"].salida = colas["Buffer_Inspeccion"]
    est["Inspeccion"].salida = (
        lambda item: defectuoso if rng.random() < esc["prob_defecto"] else colas["Buffer_Empaque"])
    est["Empaque"].salida = terminado

    for nombre, f in esc["fallas"].items():
        env.process(est[nombre].fallas(f["tbf"], f["ttr"]))

    llegadas = {"n": 0}

    def fuente():
        i = 0
        while True:
            yield env.timeout(muestrear(rng, esc["llegadas"]))
            i += 1
            llegadas["n"] = i
            yield colas["Almacen_MP"].put({"id": i, "t_llegada": env.now})

    env.process(fuente())
    env.run(until=T)

    # ---- Indicadores
    for e in est.values():
        for s in e.servidores:
            s.cerrar(T)

    buenas = len(terminado.items)
    malas = len(defectuoso.items)
    tiempos_sistema = [it["t_salida"] - it["t_llegada"] for it in terminado.items]
    wip_colas = sum(c.promedio(T) for c in colas.values())
    wip_est = sum(sum(s.acumulado[x] for x in ("procesando", "bloqueado")) / T
                  for e in est.values() for s in e.servidores)

    r = {
        "llegadas": llegadas["n"],
        "terminadas": buenas,
        "defectuosas": malas,
        "throughput_h": buenas / (T / 60),
        "defectuosas_h": malas / (T / 60),
        "tiempo_sistema_prom": float(np.mean(tiempos_sistema)) if tiempos_sistema else math.nan,
        "tiempo_sistema_max": float(np.max(tiempos_sistema)) if tiempos_sistema else math.nan,
        "wip_prom": wip_colas + wip_est,
    }
    for n, e in est.items():
        k = len(e.servidores)
        for x in ESTADOS:
            r[f"{n}_{x}"] = sum(s.acumulado[x] for s in e.servidores) / (k * T)
        r[f"{n}_procesadas"] = e.procesadas
        r[f"{n}_fallas"] = e.n_fallas
    for n, c in colas.items():
        r[f"{n}_prom"] = c.promedio(T)
        r[f"{n}_max"] = c.maximo
        r[f"{n}_espera"] = float(np.mean(c.esperas)) if c.esperas else 0.0
    # Operarios: inspector = servidor de Inspección; empacadores = servidores de Empaque
    r["Inspector_util"] = r["Inspeccion_procesando"]
    r["Empacadores_util"] = r["Empaque_procesando"]
    if guardar_series:
        r["_series"] = {n: c.serie for n, c in colas.items()}
        r["_fallas"] = {n: e.intervalos_falla for n, e in est.items() if e.intervalos_falla}
    return r


# ---------------------------------------------------------------------------
# 4. Réplicas, intervalos de confianza y reportes
# ---------------------------------------------------------------------------
def intervalo(valores, conf=0.95):
    x = np.asarray(valores, dtype=float)
    x = x[~np.isnan(x)]
    n = len(x)
    media = float(x.mean())
    if n < 2:
        return media, 0.0
    if sps is not None:
        t = sps.t.ppf((1 + conf) / 2, n - 1)
    else:
        t = 1.96
    return media, float(t * x.std(ddof=1) / math.sqrt(n))


def capacidad_teorica(esc: dict) -> list[dict]:
    """Capacidad de cada estación en botellas/hora (cálculo analítico)."""
    filas = []
    tasa_llegada = 60 / media_dist(esc["llegadas"])
    for n in ORDEN_ESTACIONES:
        cfg = esc["estaciones"][n]
        t = media_dist(cfg["dist"])
        disp = 1.0
        if n in esc["fallas"]:
            f = esc["fallas"][n]
            mtbf, mttr = media_dist(f["tbf"]), media_dist(f["ttr"])
            disp = mtbf / (mtbf + mttr)
        cap = cfg["servidores"] * 60 / t * disp
        carga = tasa_llegada * ((1 - esc["prob_defecto"]) if n == "Empaque" else 1)
        filas.append({"estacion": n, "tiempo_medio_min": t, "servidores": cfg["servidores"],
                      "disponibilidad": disp, "capacidad_bot_h": cap,
                      "carga_bot_h": carga, "utilizacion_teorica": carga / cap})
    return filas


def correr_escenario(clave, reps, semilla0=1000):
    esc = ESCENARIOS[clave]
    return [correr_replica(esc, semilla0 + i) for i in range(reps)]


def guardar_csv(ruta, filas, campos=None):
    campos = campos or list(filas[0].keys())
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for fila in filas:
            w.writerow({k: (round(v, 4) if isinstance(v, float) else v) for k, v in fila.items()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--escenario", default="todos", choices=["todos", *ESCENARIOS])
    ap.add_argument("--sin-graficas", action="store_true")
    ap.add_argument("--verificacion", action="store_true",
                    help="corre solo la prueba determinista y muestra los valores esperados")
    args = ap.parse_args()
    os.makedirs(DIR_RESULTADOS, exist_ok=True)

    if args.verificacion:
        r = correr_replica(VERIFICACION, 1)
        print("Prueba determinista (480 min):")
        print(f"  Llegadas: {r['llegadas']}  Terminadas: {r['terminadas']}  Defectuosas: {r['defectuosas']}")
        for n in ORDEN_ESTACIONES:
            print(f"  {n:<11} procesando {r[n + '_procesando']:.1%}  bloqueado {r[n + '_bloqueado']:.1%}")
        for q in VERIFICACION["colas"]:
            print(f"  {q:<18} contenido máx {r[q + '_max']}")
        return

    claves = list(ESCENARIOS) if args.escenario == "todos" else [args.escenario]
    resumen, detalle = [], {}
    for clave in claves:
        reps = correr_escenario(clave, args.reps)
        detalle[clave] = reps
        fila = {"escenario": ESCENARIOS[clave]["nombre"]}
        for k in ("throughput_h", "defectuosas_h", "terminadas", "tiempo_sistema_prom",
                  "wip_prom", "Etiquetado_procesando", "Buffer_Etiquetado_prom",
                  "Buffer_Etiquetado_max", "Almacen_MP_prom", "Llenado_bloqueado"):
            m, hw = intervalo([r[k] for r in reps])
            fila[k] = m
            fila[k + "_ic95"] = hw
        resumen.append(fila)
        print(f"\n=== {fila['escenario']} ({args.reps} réplicas de {ESCENARIOS[clave]['duracion']:.0f} min)")
        print(f"  Botellas terminadas/h : {fila['throughput_h']:.1f} ± {fila['throughput_h_ic95']:.1f}")
        print(f"  Defectuosas/h         : {fila['defectuosas_h']:.1f}")
        print(f"  Tiempo en sistema     : {fila['tiempo_sistema_prom']:.2f} ± {fila['tiempo_sistema_prom_ic95']:.2f} min")
        print(f"  WIP promedio          : {fila['wip_prom']:.1f} botellas")
        for n in ORDEN_ESTACIONES:
            u = np.mean([r[f"{n}_procesando"] for r in reps])
            b = np.mean([r[f"{n}_bloqueado"] for r in reps])
            fa = np.mean([r[f"{n}_falla"] for r in reps])
            q = COLA_ANTES[n]
            qp = np.mean([r[f"{q}_prom"] for r in reps])
            qm = np.mean([r[f"{q}_max"] for r in reps])
            print(f"  {n:<11} util {u:6.1%}  bloq {b:6.1%}  falla {fa:5.1%} | cola antes ({q}) prom {qp:6.2f} máx {qm:6.1f}")

    guardar_csv(os.path.join(DIR_RESULTADOS, "resumen_escenarios.csv"), resumen)
    guardar_csv(os.path.join(DIR_RESULTADOS, "capacidad_teorica_base.csv"), capacidad_teorica(BASE))

    if "base" in detalle:
        reps = detalle["base"]
        filas_est = []
        for n in ORDEN_ESTACIONES:
            f = {"estacion": n, "servidores": BASE["estaciones"][n]["servidores"]}
            for x in ESTADOS:
                f[x] = float(np.mean([r[f"{n}_{x}"] for r in reps]))
            f["botellas_procesadas"] = float(np.mean([r[f"{n}_procesadas"] for r in reps]))
            filas_est.append(f)
        guardar_csv(os.path.join(DIR_RESULTADOS, "estaciones_base.csv"), filas_est)
        filas_cola = []
        for q, cap in BASE["colas"].items():
            filas_cola.append({
                "cola": q, "capacidad": cap,
                "contenido_promedio": float(np.mean([r[f"{q}_prom"] for r in reps])),
                "contenido_maximo_prom": float(np.mean([r[f"{q}_max"] for r in reps])),
                "contenido_maximo_abs": float(np.max([r[f"{q}_max"] for r in reps])),
                "espera_promedio_min": float(np.mean([r[f"{q}_espera"] for r in reps])),
            })
        guardar_csv(os.path.join(DIR_RESULTADOS, "colas_base.csv"), filas_cola)
        guardar_csv(os.path.join(DIR_RESULTADOS, "replicas_base.csv"),
                    [{k: v for k, v in r.items() if not k.startswith("_")} for r in reps])

    if not args.sin_graficas:
        import graficas
        graficas.generar(detalle, ESCENARIOS, ORDEN_ESTACIONES, COLA_ANTES, BASE,
                         correr_replica, DIR_RESULTADOS)


if __name__ == "__main__":
    main()
