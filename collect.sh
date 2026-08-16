#!/usr/bin/env bash
#
# collect.sh - raccoglie i file del progetto dalla cartella muBench/ (lo
# strumento) alla struttura pulita di ProgettoSPE/ (il lavoro da consegnare).
#
# Uso:  ./collect.sh
# Va lanciato dalla root di ProgettoSPE/. Assume che muBench/ sia in ../muBench.
#
set -euo pipefail

MUBENCH="../muBench"
HERE="$(pwd)"

echo ">> Raccolgo i file da $MUBENCH in $HERE"

mkdir -p config scripts/analysis data/{low,mid,high,bursty} report

# --- Config dell'applicazione e degli esperimenti ---
cp "$MUBENCH/SimulationWorkspace/workmodel.json"         config/
cp "$MUBENCH/CustomFunctions/heavy_tail.py"              config/
cp "$MUBENCH/Configs/TrafficParameters-low.json"         config/
cp "$MUBENCH/Configs/TrafficParameters-mid.json"         config/
cp "$MUBENCH/Configs/TrafficParameters-high.json"        config/
cp "$MUBENCH/Configs/RunnerParameters-low.json"          config/
cp "$MUBENCH/Configs/RunnerParameters-mid.json"          config/
cp "$MUBENCH/Configs/RunnerParameters-high.json"         config/
cp "$MUBENCH/Configs/RunnerParameters-bursty.json"       config/

# --- Infrastruttura (stanno in spe/, fuori da muBench) ---
cp ../prometheus-minimal.yaml                            config/ 2>/dev/null || echo "   (!) prometheus-minimal.yaml non trovato in ../ - copialo a mano"
cp ../kind-config.yaml                                   config/ 2>/dev/null || echo "   (!) kind-config.yaml non trovato in ../ - copialo a mano"

# --- Workload generati (input riproducibile degli esperimenti) ---
mkdir -p config/workloads
cp "$MUBENCH/SimulationWorkspace/workloads/"*.json       config/workloads/

# --- Script ---
cp "$MUBENCH/gen_bursty.py"                              scripts/

# --- Dati grezzi, se presenti ---
if [ -d "$MUBENCH/SimulationWorkspace/Result" ]; then
  echo ">> Copio i risultati raccolti"
  # ogni result-<scen>*.txt va nella sua sottocartella
  for scen in low mid high bursty; do
    find "$MUBENCH/SimulationWorkspace/Result" -name "result-${scen}*.txt" \
      -exec cp {} "data/${scen}/" \; 2>/dev/null || true
  done
else
  echo ">> Nessun risultato ancora (cartella Result assente) - normale se non hai ancora misurato"
fi

echo ">> Fatto. Struttura raccolta:"
find . -type f -not -path './.git/*' | sort
