"""Gráficas de resultados del modelo de validación (se llaman desde linea_embotellado.py)."""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Paleta (slots categóricos en orden fijo) y tinta de los ejes
AZUL, NARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
GRIS_DATO = "#c3c2b7"
SUPERFICIE = "#fcfcfb"
TINTA, TINTA_2, TINTA_MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASE_EJE = "#e1e0d9", "#c3c2b7"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "axes.edgecolor": BASE_EJE,
    "axes.labelcolor": TINTA_2,
    "axes.titlecolor": TINTA,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.grid": True,
    "grid.color": GRID,
    "grid.linewidth": 0.6,
    "xtick.color": TINTA_MUTED,
    "ytick.color": TINTA_2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "legend.frameon": False,
    "savefig.dpi": 160,
    "savefig.bbox": "tight",
})

NOMBRES = {"Inspeccion": "Inspección"}


def _n(x):
    return NOMBRES.get(x, x)


def estados_estaciones(detalle, orden, base, ruta):
    reps = detalle["base"]
    estados = [("procesando", "Procesando", AZUL), ("bloqueado", "Bloqueado", NARANJA),
               ("falla", "En falla", AQUA), ("ocioso", "Ocioso", GRIS_DATO)]
    fig, ax = plt.subplots(figsize=(8.5, 3.8))
    y = np.arange(len(orden))[::-1]
    izquierda = np.zeros(len(orden))
    for clave, etiqueta, color in estados:
        v = np.array([np.mean([r[f"{n}_{clave}"] for r in reps]) for n in orden]) * 100
        ax.barh(y, v, left=izquierda, color=color, height=0.55, label=etiqueta,
                edgecolor=SUPERFICIE, linewidth=2)
        if clave == "procesando":
            for yi, vi in zip(y, v):
                ax.text(vi / 2, yi, f"{vi:.0f} %", va="center", ha="center",
                        color="white", fontsize=9, fontweight="bold")
        izquierda += v
    etiquetas = [f"{_n(n)} ({base['estaciones'][n]['servidores']})" for n in orden]
    ax.set_yticks(y, etiquetas)
    ax.set_xlim(0, 100)
    ax.set_xlabel("% del tiempo del turno (480 min)")
    ax.grid(axis="y", visible=False)
    ax.set_title("Estado de cada estación – escenario base (prom. 30 réplicas)", loc="left")
    ax.legend(ncol=4, loc="upper left", bbox_to_anchor=(0, -0.18))
    fig.text(0.0, -0.12, "Entre paréntesis: número de servidores (máquinas/operarios).",
             color=TINTA_MUTED, fontsize=8)
    fig.savefig(ruta)
    plt.close(fig)


def colas_en_el_tiempo(correr_replica, base, ruta, semilla=1000):
    r = correr_replica(base, semilla, guardar_series=True)
    series, fallas = r["_series"], r["_fallas"].get("Tapado", [])
    paneles = [("Buffer_Tapado", "Cola antes de Tapado"),
               ("Buffer_Etiquetado", "Cola antes de Etiquetado (cuello de botella)"),
               ("Almacen_MP", "Almacén de materia prima (antes de Llenado)")]
    fig, axes = plt.subplots(len(paneles), 1, figsize=(9, 6.6), sharex=True)
    for ax, (cola, titulo) in zip(axes, paneles):
        t, q = zip(*series[cola])
        ax.step(t, q, where="post", color=AZUL, linewidth=1.0)
        cap = base["colas"][cola]
        if cap < 100:
            ax.axhline(cap, color=TINTA_MUTED, linewidth=0.8)
            ax.text(base["duracion"], cap, f" capacidad {cap}", va="center",
                    color=TINTA_MUTED, fontsize=8)
            ax.set_ylim(0, cap * 1.15)
        for a, b in fallas:
            ax.axvspan(a, b, color=NARANJA, alpha=0.18, linewidth=0)
        ax.set_title(titulo, loc="left", fontsize=10)
        ax.set_ylabel("botellas")
    axes[-1].set_xlabel("Tiempo de simulación (min)")
    axes[-1].set_xlim(0, base["duracion"])
    axes[0].text(0, 1.32, "Acumulación de botellas en las colas – una réplica del escenario base",
                 transform=axes[0].transAxes, fontsize=12, fontweight="bold", color=TINTA)
    axes[0].text(0, 1.17, "Franjas naranjas: la tapadora está en falla (MTBF/MTTR).",
                 transform=axes[0].transAxes, fontsize=9, color=TINTA_2)
    fig.tight_layout()
    fig.savefig(ruta)
    plt.close(fig)


def comparacion_escenarios(detalle, escenarios, ruta_thr, ruta_tis):
    from linea_embotellado import intervalo

    claves = list(detalle)
    nombres = [escenarios[k]["nombre"] for k in claves]
    y = np.arange(len(claves))[::-1]

    def barras(metrica, xlabel, titulo, ruta, excluir=()):
        fig, ax = plt.subplots(figsize=(8.5, 4.2))
        for yi, k in zip(y, claves):
            if k in excluir:
                ax.text(0.5, yi, "no aplica (alimentación saturada: el almacén se llena)",
                        va="center", color=TINTA_MUTED, fontsize=8)
                continue
            m, hw = intervalo([r[metrica] for r in detalle[k]])
            color = AZUL if k == "base" else GRIS_DATO
            ax.barh(yi, m, color=color, height=0.55, edgecolor=SUPERFICIE, linewidth=2)
            ax.errorbar(m, yi, xerr=hw, color=TINTA_2, capsize=3, linewidth=1)
            ax.text(m + hw, yi, f"  {m:.1f}", va="center", color=TINTA, fontsize=9)
        ax.set_yticks(y, nombres)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel(xlabel)
        ax.set_title(titulo, loc="left")
        ax.set_xlim(0, ax.get_xlim()[1] * 1.08)
        fig.text(0.0, -0.04, "Barras de error: intervalo de confianza del 95 % (30 réplicas). "
                 "En azul, el escenario base.", color=TINTA_MUTED, fontsize=8)
        fig.savefig(ruta)
        plt.close(fig)

    barras("throughput_h", "Botellas buenas por hora",
           "Producción de la línea por escenario", ruta_thr)
    barras("tiempo_sistema_prom", "Minutos desde la recepción hasta el empaque",
           "Tiempo promedio de una botella en el sistema", ruta_tis, excluir=("capacidad",))


def capacidad_estaciones(base, ruta):
    from linea_embotellado import capacidad_teorica

    filas = capacidad_teorica(base)
    llegada = filas[0]["carga_bot_h"]
    cuello = min(filas, key=lambda f: f["capacidad_bot_h"])["estacion"]
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    y = np.arange(len(filas))[::-1]
    for yi, f in zip(y, filas):
        es_cuello = f["estacion"] == cuello
        ax.barh(yi, f["capacidad_bot_h"], color=AZUL if es_cuello else GRIS_DATO, height=0.55,
                edgecolor=SUPERFICIE, linewidth=2)
        txt = f"  {f['capacidad_bot_h']:.0f} bot/h" + ("  ← cuello de botella" if es_cuello else "")
        ax.text(f["capacidad_bot_h"], yi, txt, va="center", color=TINTA, fontsize=9,
                fontweight="bold" if es_cuello else "normal")
    ax.axvline(llegada, color=NARANJA, linewidth=2)
    ax.text(llegada, y[0] + 0.55, f"llegadas: {llegada:.0f} bot/h", color=TINTA_2,
            fontsize=8, ha="center")
    ax.set_yticks(y, [_n(f["estacion"]) for f in filas])
    ax.set_xlim(0, 300)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Capacidad teórica (botellas/hora) = servidores × 60 / tiempo medio × disponibilidad")
    ax.set_title("Capacidad de cada estación frente a la tasa de llegada", loc="left", pad=16)
    fig.savefig(ruta)
    plt.close(fig)


def generar(detalle, escenarios, orden, cola_antes, base, correr_replica, carpeta):
    if "base" in detalle:
        estados_estaciones(detalle, orden, base, os.path.join(carpeta, "estados_estaciones_base.png"))
        colas_en_el_tiempo(correr_replica, base, os.path.join(carpeta, "colas_en_el_tiempo_base.png"))
    capacidad_estaciones(base, os.path.join(carpeta, "capacidad_estaciones.png"))
    if len(detalle) > 1:
        comparacion_escenarios(detalle, escenarios,
                               os.path.join(carpeta, "escenarios_produccion.png"),
                               os.path.join(carpeta, "escenarios_tiempo_sistema.png"))
    print(f"\nGráficas guardadas en {carpeta}")
