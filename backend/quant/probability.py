import numpy as np
from scipy.stats import norm
from typing import List, Tuple

def normal_pdf(x: float, mean: float = 0.0, std: float = 1.0) -> float:
    return float(norm.pdf(x, loc=mean, scale=std))

def normal_cdf(x: float, mean: float = 0.0, std: float = 1.0) -> float:
    return float(norm.cdf(x, loc=mean, scale=std))

def run_monte_carlo_simulation(
    S0: float, mu: float, sigma: float, T: float, steps: int, paths: int, seed: int = 42
) -> np.ndarray:
    """
    Simulates price paths using Geometric Brownian Motion (GBM).
    Returns a matrix of shape (steps + 1, paths).
    """
    np.random.seed(seed)
    dt = T / steps
    # Generate path trajectories
    paths_matrix = np.zeros((steps + 1, paths))
    paths_matrix[0] = S0
    
    for t in range(1, steps + 1):
        z = np.random.standard_normal(paths)
        paths_matrix[t] = paths_matrix[t-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
        
    return paths_matrix

def simulate_markov_chain(
    transition_matrix: np.ndarray, initial_state: int, steps: int, seed: int = 42
) -> List[int]:
    """
    Simulates discrete-time state transitions on a Markov chain.
    """
    np.random.seed(seed)
    current_state = initial_state
    states = [current_state]
    
    n_states = transition_matrix.shape[0]
    state_indices = np.arange(n_states)
    
    for _ in range(steps):
        probabilities = transition_matrix[current_state]
        current_state = int(np.random.choice(state_indices, p=probabilities))
        states.append(current_state)
        
    return states

def bayesian_normal_mean_update(
    prior_mean: float, prior_var: float, sample_mean: float, sample_var: float, n_samples: int
) -> Tuple[float, float]:
    """
    Performs a Bayesian conjugate update for the mean of a normal distribution with known variance.
    Returns (posterior_mean, posterior_variance).
    """
    precision_prior = 1.0 / prior_var
    precision_sample = n_samples / sample_var
    
    precision_post = precision_prior + precision_sample
    mean_post = (prior_mean * precision_prior + sample_mean * precision_sample) / precision_post
    
    return mean_post, (1.0 / precision_post)
