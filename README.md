# Workload Characterization di un'applicazione a microservizi

Progetto per il corso di **Software Performance Engineering**.

Caratterizzazione dei processi di arrivo e di servizio di una catena di
microservizi deployata su Kubernetes, con verifica delle ipotesi alla base dei
modelli markoviani e delle reti di code (arrivi di Poisson, tempi di servizio
esponenziali, indipendenza).

## Idea dell'esperimento

Una catena lineare di 4 microservizi `s0 → s1 → s2 → s3` generata con
[µBench](https://github.com/mSvcBench/muBench). Tre servizi (`s0`, `s1`, `s3`)
hanno tempo di servizio quasi deterministico; `s2` usa una funzione interna
custom a **coda pesante** (complessità campionata da una Pareto), così da avere
un nodo con coefficiente di variazione > 1.

Il sistema viene sollecitato con quattro workload:

| Scenario | Processo di arrivo | Tasso medio |
|----------|--------------------|-------------|
| low      | Poisson (inter-arrival esponenziali) | ~5 req/s  |
| mid      | Poisson                              | ~20 req/s |
| high     | Poisson                              | ~50 req/s |
| bursty   | ON-OFF (MMPP-2), non poissoniano     | variabile |

Su ogni scenario si misurano inter-arrival effettivi, response time end-to-end
e tempi di servizio per-servizio (da Prometheus), e si verifica quanto reggono
le ipotesi markoviane.

## Struttura della repo

```
config/           file di configurazione dell'esperimento (input)
  workmodel.json          topologia della catena + parametri dei servizi
  heavy_tail.py           funzione interna custom a coda pesante (nodo s2)
  TrafficParameters-*.json parametri di generazione dei workload poissoniani
  RunnerParameters-*.json  parametri di esecuzione delle campagne di misura
  workloads/              workload generati (input riproducibile)
  kind-config.yaml        definizione del cluster kind (port mapping)
  prometheus-minimal.yaml deploy di Prometheus per la raccolta metriche
scripts/
  gen_bursty.py           generatore del workload ON-OFF
  analysis/               script/notebook di analisi e fitting
data/                     risultati grezzi delle campagne (result-*.txt)
report/                   relazione finale
```

`muBench/` **non** è incluso: è uno strumento esterno che si clona a parte (vedi
sotto). Questa repo contiene solo il lavoro originale del progetto.

## Riproduzione

### Prerequisiti
- Docker, kubectl, kind
- Python 3.10 (per l'ambiente di µBench)

### 1. Clona µBench (lo strumento)
```bash
git clone https://github.com/mSvcBench/muBench.git
cd muBench
python3.10 -m venv .venv && source .venv/bin/activate
pip install "setuptools<66" "Cython<3.0" wheel
pip install --no-build-isolation PyYAML==5.4.1
pip install -r requirements.txt        # richiede cmake, bison, flex a livello di sistema
cd ..
```

### 2. Crea il cluster
```bash
kind create cluster --name spe --config config/kind-config.yaml
```

### 3. Copia i file di progetto dentro µBench
```bash
cp config/workmodel.json           muBench/SimulationWorkspace/
cp config/heavy_tail.py            muBench/CustomFunctions/
cp config/TrafficParameters-*.json muBench/Configs/
cp config/RunnerParameters-*.json  muBench/Configs/
cp config/workloads/*.json         muBench/SimulationWorkspace/workloads/
cp scripts/gen_bursty.py           muBench/
```
Imposta in `muBench/Configs/K8sParameters.json`:
- `"WorkModelPath": "SimulationWorkspace/workmodel.json"`
- `"dns-resolver": "kube-dns.kube-system.svc.cluster.local"`

### 4. Monitoring
```bash
kubectl apply -f config/prometheus-minimal.yaml
```

### 5. Deploy dell'applicazione
```bash
cd muBench && source .venv/bin/activate
python3 Deployers/K8sDeployer/RunK8sDeployer.py -c Configs/K8sParameters.json
```

### 6. Campagne di misura
```bash
python3 Benchmarks/Runner/Runner.py -c Configs/RunnerParameters-low.json
python3 Benchmarks/Runner/Runner.py -c Configs/RunnerParameters-mid.json
python3 Benchmarks/Runner/Runner.py -c Configs/RunnerParameters-high.json
python3 Benchmarks/Runner/Runner.py -c Configs/RunnerParameters-bursty.json
```
I risultati finiscono in `muBench/SimulationWorkspace/Result/` e vanno copiati
in `data/` per l'analisi.

### 7. Analisi
Vedi `scripts/analysis/`.

## Nota sullo strumento

µBench è sviluppato da mSvcBench ed è rilasciato con la propria licenza. Qui
viene usato come strumento di generazione del benchmark: non è parte del
contributo di questo progetto e non è ridistribuito in questa repo.
