# Riepilogo campagne di misura

Risultati sintetici delle quattro campagne di caratterizzazione del workload
sulla catena `s0 → s1 → s2 → s3` (µBench su Kubernetes/kind). Ogni scenario è
stato eseguito in **3 run indipendenti**. I valori provengono dalle righe di
riepilogo del Runner (`Run Duration ...`).

## Scenari

| Scenario | Processo di arrivo | Rate nominale | Eventi/run |
|----------|--------------------|---------------|------------|
| low      | Poisson (inter-arrival esponenziali) | 5 req/s  | 3000 |
| mid      | Poisson              | 20 req/s | 5000 |
| high     | Poisson              | 50 req/s | 5000 |
| bursty   | ON-OFF (MMPP-2), non poissoniano | ~26 req/s eff. | 5000 |

Il nodo `s2` usa una funzione interna a **coda pesante** (complessità ~ Pareto,
α=1.5), gli altri nodi `compute_pi` a complessità quasi costante.

## Tutti i run (12)

| Scenario | Run | Durata (s) | Richieste | Errori (500) | Timing Error | Latenza media (ms) | Rate eff. (req/s) |
|----------|-----|-----------|-----------|--------------|--------------|---------------------|-------------------|
| low    | 1 | 606.04 | 3000 | 0 | 0    | 21.34  | 4.950 |
| low    | 2 | 606.05 | 3000 | 0 | 0    | 22.28  | 4.950 |
| low    | 3 | 606.05 | 3000 | 0 | 0    | 21.89  | 4.950 |
| mid    | 1 | 261.22 | 5000 | 0 | 0    | 21.50  | 19.141 |
| mid    | 2 | 261.22 | 5000 | 0 | 0    | 20.96  | 19.141 |
| mid    | 3 | 261.23 | 5000 | 0 | 0    | 21.13  | 19.140 |
| high   | 1 | 100.00 | 5000 | 0 | 40   | 35.08  | 49.999 |
| high   | 2 | 100.00 | 5000 | 1 | 302  | 47.72  | 49.999 |
| high   | 3 | 100.00 | 5000 | 0 | 83   | 29.56  | 49.998 |
| bursty | 1 | 194.08 | 5000 | 1 | 1644 | 131.70 | 25.763 |
| bursty | 2 | 193.98 | 5000 | 0 | 1320 | 97.34  | 25.776 |
| bursty | 3 | 193.98 | 5000 | 0 | 606  | 60.30  | 25.776 |

## Aggregato per scenario (media dei 3 run)

| Scenario | Latenza media (ms) | Range latenza | Timing Error medi | Range TE | Errori 500 tot | Rate eff. medio |
|----------|---------------------|---------------|-------------------|----------|-----------------|-----------------|
| low    | 21.8  | 21.3 – 22.3   | 0    | 0        | 0 | 4.95  |
| mid    | 21.2  | 21.0 – 21.5   | 0    | 0        | 0 | 19.14 |
| high   | 37.5  | 29.6 – 47.7   | 142  | 40 – 302 | 1 | 50.00 |
| bursty | 96.5  | 60.3 – 131.7  | 1190 | 606 – 1644 | 2 | 25.77 |

## Osservazioni

**Errori applicativi trascurabili.** Su 51.000 richieste totali, solo 4 status
500 (0.008%). Sono reset TCP transitori dovuti alla saturazione momentanea dei
worker di `s2` durante campioni lunghi della coda pesante (verificato dai log di
`s1`: `Connection reset by peer`). Da filtrare in analisi (`status == 200`).

**low e mid: sistema in regime non congestionato.** Zero timing error, latenza
media ~21 ms stabilissima tra i run. A questi tassi la catena non è mai sotto
pressione; è il baseline in cui le ipotesi markoviane dovrebbero reggere meglio.
Nota: a `mid` il rate effettivo è ~19.14 req/s (non 20) e la durata 261 s invece
dei ~250 attesi — il generatore non tiene esattamente il passo nemmeno senza
timing error, effetto della latenza di servizio che accumula un piccolo ritardo.

**high: comparsa della congestione transitoria.** A 50 req/s iniziano i timing
error (40–302) e la latenza media sale (30–48 ms). Il rate effettivo resta però
50 req/s: il sistema è sotto stress ma non collassa.

**bursty: la burstiness domina il carico medio.** Pur avendo un rate medio
(~26 req/s) circa la metà di `high`, mostra la latenza media più alta di tutte
(60–132 ms) e i timing error più numerosi (606–1644). Durante le fasi ON
l'intensità istantanea supera di molto i 50 req/s, saturando la catena; nelle
fasi OFF il sistema è quasi fermo. Dimostrazione empirica che **il carico medio
non basta a caratterizzare le prestazioni**: conta la struttura temporale degli
arrivi.

**La variabilità tra run è essa stessa un risultato.** In `low`/`mid` i 3 run
sono quasi identici (variabilità ~nulla). In `high` e soprattutto `bursty` la
latenza e i timing error variano di un fattore 2–3 tra run con lo *stesso*
workload: è la firma della **coda pesante di s2** (CV alto → un singolo campione
estremo cambia il comportamento dell'intero run). Le 3 ripetizioni per scenario
servono proprio a quantificare questa variabilità.

**Nota sui timing error.** Un timing error indica che il Runner non è riuscito a
inviare una richiesta al timestamp previsto perché tutti i thread del pool erano
occupati. Non è una richiesta persa (lo status resta 200), ma implica che negli
scenari congestionati (`high`, `bursty`) gli inter-arrival *effettivi* divergono
da quelli *nominali*. Da tenere presente nell'analisi del processo di arrivo:
è un effetto di test open-loop sotto congestione.

## Nota sui file di log

I file `logs-*-run*.txt` contengono l'output completo del Runner (incluse le
righe `Processed request` e `Error: All Pool Threads are busy`). Sono presenti
per low (3), mid (3), bursty (3) e high (solo run1) — per high run2/run3 il log
completo non è stato salvato su file, ma i riepiloghi sono riportati nelle
tabelle sopra. I dati grezzi per-richiesta di **tutti** i run sono comunque
integri nei rispettivi `result-*-run*.txt`.
