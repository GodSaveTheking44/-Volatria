import numpy as np
from typing import List, Optional

def generate_gbm_paths(
    S0: float, drift: float, vol: float, T: float, steps: int, seed: Optional[int] = None
) -> np.ndarray:
    """
    Generates a single Geometric Brownian Motion stock price trajectory.
    """
    if seed is not None:
        np.random.seed(seed)
    dt = T / steps
    t = np.linspace(0, T, steps + 1)
    
    # Generate cumulative normal sums
    W = np.random.standard_normal(size=steps)
    W = np.insert(W, 0, 0.0)
    W = np.cumsum(W) * np.sqrt(dt)
    
    # Stock path formulation
    S = S0 * np.exp((drift - 0.5 * vol**2) * t + vol * W)
    return S

def simulate_poisson_arrival_times(rate: float, T: float, seed: Optional[int] = None) -> List[float]:
    """
    Simulates Poisson process arrival timestamps up to time T.
    """
    if seed is not None:
        np.random.seed(seed)
    arrival_times = []
    t = 0.0
    
    while t < T:
        # Inter-arrival time is exponentially distributed
        t_inter = np.random.exponential(1.0 / rate)
        t += t_inter
        if t < T:
            arrival_times.append(t)
            
    return arrival_times
