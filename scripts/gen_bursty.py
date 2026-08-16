#!/usr/bin/env python3
"""
Genera un workload bursty (processo ON-OFF / MMPP-2) nel formato del Runner
muBench v6.

Il TrafficGenerator standard produce solo inter-arrival esponenziali (Poisson).
Questo script serve a creare lo scenario di CONTRASTO: un processo di arrivo
NON poissoniano, con burst e autocorrelazione, per mostrare nel report che:
  - gli inter-arrival non sono piu' esponenziali (test K-S fallisce)
  - l'ACF e' significativamente != 0 (l'ipotesi di indipendenza cade)
  - serve un MMPP/MAP al posto del processo di Poisson.

Formato di output: lista di eventi [{"time": <ms>, "service": "s0"}, ...]
ordinati per tempo crescente, esattamente come il TrafficGenerator v6.
"""
import json
import os
import random

# ----------------------- parametri -----------------------
SEED = 42
INGRESS = "s0"
N_EVENTS = 5000

MEAN_IAT_ON = 15.0      # ms - inter-arrival medio in fase ON (burst intenso)
MEAN_IAT_OFF = 400.0    # ms - inter-arrival medio in fase OFF (quasi silenzio)
MEAN_DUR_ON = 2000.0    # ms - durata media fase ON
MEAN_DUR_OFF = 4000.0   # ms - durata media fase OFF

# percorso di output relativo alla root di muBench
OUT = "SimulationWorkspace/workloads/workload-bursty.json"
# ---------------------------------------------------------

random.seed(SEED)

events = []
t = 0.0
state_on = True
state_deadline = random.expovariate(1.0 / MEAN_DUR_ON)

while len(events) < N_EVENTS:
    mean_iat = MEAN_IAT_ON if state_on else MEAN_IAT_OFF
    t += random.expovariate(1.0 / mean_iat)

    # eventuale transizione di stato ON<->OFF
    if t >= state_deadline:
        state_on = not state_on
        mean_dur = MEAN_DUR_ON if state_on else MEAN_DUR_OFF
        state_deadline = t + random.expovariate(1.0 / mean_dur)

    events.append({"time": int(round(t)), "service": INGRESS})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(events, f, indent=2)

# statistiche di riepilogo
iats = [events[i]["time"] - events[i - 1]["time"] for i in range(1, len(events))]
mean_iat = sum(iats) / len(iats)
var_iat = sum((x - mean_iat) ** 2 for x in iats) / len(iats)
cv = (var_iat ** 0.5) / mean_iat if mean_iat > 0 else float("nan")

print(f"Eventi generati : {len(events)}")
print(f"Durata totale   : {t/1000:.1f} s")
print(f"IAT medio       : {mean_iat:.1f} ms")
print(f"CV degli IAT    : {cv:.2f}  (un Poisson darebbe ~1.0; qui atteso > 1)")
print(f"File salvato in  : {OUT}")
