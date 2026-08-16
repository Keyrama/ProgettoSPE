import random
import string


def heavy_tail(params):
    """
    Internal function con service time a CODA PESANTE.

    A differenza di compute_pi/loader (che estraggono la complessita' da una
    UNIFORME -> CV < 1), qui la complessita' e' estratta da una PARETO, quindi
    il tempo di servizio risultante ha CV > 1. Questo rende il nodo un caso
    M/G/1 non banale, utile per discutere la formula di Pollaczek-Khinchine e
    la rottura dell'ipotesi esponenziale nel report.

    Parametri (con default):
      pareto_alpha       : esponente di coda. Piu' basso -> coda piu' pesante.
                           alpha <= 2 -> varianza teorica infinita. Default 1.5
      scale_complexity   : complessita' minima (parametro di scala di Pareto).
                           Default 40
      cap_complexity     : tetto di sicurezza sulla complessita' per non
                           bloccare il pod su un campione estremo. Default 2500
      mean_response_size : media (kB) della dimensione risposta (esponenziale).
                           Default 10

    NB sul cap: la Pareto con alpha=1.5 ha varianza infinita; senza tetto un
    singolo campione puo' bloccare il pod per minuti. Il troncamento va
    DICHIARATO nel report: una Pareto troncata NON ha piu' varianza infinita,
    ma mantiene comunque CV > 1 nell'intervallo utile.
    """
    alpha = float(params.get("pareto_alpha", 1.5))
    scale = int(params.get("scale_complexity", 40))
    cap = int(params.get("cap_complexity", 2500))
    mean_size = float(params.get("mean_response_size", 10))

    # complessita' ~ Pareto troncata
    cpu_load = int(min(scale * random.paretovariate(alpha), cap))

    # calcolo di pi con cpu_load cifre (stesso kernel di compute_pi)
    pi_greco = list()
    q, r, t, k, m, x = 1, 0, 1, 1, 3, 3
    counter = 0
    while True:
        if 4 * q + r - t < m * t:
            pi_greco.append(m)
            q, r, t, k, m, x = 10*q, 10*(r-m*t), t, k, (10*(3*q+r))//t - 10*m, x
            if counter > cpu_load - 1:
                break
            else:
                counter = counter + 1
        else:
            q, r, t, k, m, x = q*k, (2*q+r)*x, t*x, k+1, (q*(7*k+2)+r*x)//(t*x), x+2

    # response size ~ esponenziale (come le altre funzioni)
    bandwidth_load = random.expovariate(1 / mean_size) if mean_size > 0 else 0
    num_chars = int(max(1, 1000 * bandwidth_load))
    response_body = ''.join(random.choice(string.ascii_letters) for _ in range(num_chars))
    return response_body