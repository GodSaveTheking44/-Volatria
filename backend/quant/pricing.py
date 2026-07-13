import os
import sys
import numpy as np
from scipy.stats import norm
from typing import Optional

# Setup Windows compiler DLL path
if sys.platform == "win32":
    dll_dir = r"C:\Users\stanl\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260602-ucrt-x86_64\bin"
    if os.path.exists(dll_dir):
        try:
            os.add_dll_directory(dll_dir)
        except Exception:
            pass

# Import compiled bindings with pure-Python math fallback
HAS_CPP_KERNELS = False
try:
    import volatria_core_py as vc
    HAS_CPP_KERNELS = True
except ImportError:
    pass

# --- Pure Python Fallbacks for Option Pricing ---

def py_black_scholes_price(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if T <= 0:
        return max(0.0, S - K) if is_call else max(0.0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if is_call:
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    else:
        return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def py_bs_delta(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if T <= 0:
        return 1.0 if is_call and S >= K else (0.0 if is_call else (-1.0 if S <= K else 0.0))
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return float(norm.cdf(d1)) if is_call else float(norm.cdf(d1) - 1.0)

def py_bs_gamma(S: float, K: float, r: float, T: float, sigma: float) -> float:
    if T <= 0 or S <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return float(norm.pdf(d1) / (S * sigma * np.sqrt(T)))

def py_bs_vega(S: float, K: float, r: float, T: float, sigma: float) -> float:
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    return float(S * norm.pdf(d1) * np.sqrt(T))

def py_bs_theta(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    term1 = - (S * norm.pdf(d1) * sigma) / (2.0 * np.sqrt(T))
    if is_call:
        return float(term1 - r * K * np.exp(-r * T) * norm.cdf(d2))
    else:
        return float(term1 + r * K * np.exp(-r * T) * norm.cdf(-d2))

def py_bs_rho(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if T <= 0:
        return 0.0
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if is_call:
        return float(K * T * np.exp(-r * T) * norm.cdf(d2))
    else:
        return float(-K * T * np.exp(-r * T) * norm.cdf(-d2))

def py_binomial_tree_price(S: float, K: float, r: float, T: float, sigma: float, steps: int, is_call: bool, is_american: bool) -> float:
    dt = T / steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    p = (np.exp(r * dt) - d) / (u - d)
    disc = np.exp(-r * dt)
    
    # Initialize asset prices at maturity
    prices = np.zeros(steps + 1)
    for i in range(steps + 1):
        prices[i] = S * (u ** (steps - i)) * (d ** i)
        
    # Initialize option values at maturity
    values = np.zeros(steps + 1)
    for i in range(steps + 1):
        values[i] = max(0.0, prices[i] - K) if is_call else max(0.0, K - prices[i])
        
    # Step backward through the tree
    for j in range(steps - 1, -1, -1):
        for i in range(j + 1):
            prices[i] = S * (u ** (j - i)) * (d ** i)
            continuation = disc * (p * values[i] + (1.0 - p) * values[i+1])
            if is_american:
                intrinsic = max(0.0, prices[i] - K) if is_call else max(0.0, K - prices[i])
                values[i] = max(intrinsic, continuation)
            else:
                values[i] = continuation
                
    return float(values[0])

def py_lsm_monte_carlo_price(S: float, K: float, r: float, T: float, sigma: float, paths: int, steps: int, is_call: bool, is_american: bool, seed: int = 42) -> float:
    np.random.seed(seed)
    dt = T / steps
    df = np.exp(-r * dt)
    
    # Generate GBM path matrix (steps + 1, paths)
    S_paths = np.zeros((steps + 1, paths))
    S_paths[0] = S
    for t in range(1, steps + 1):
        z = np.random.standard_normal(paths)
        S_paths[t] = S_paths[t-1] * np.exp((r - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
        
    # Option payoff matrix
    payoff = np.maximum(S_paths - K, 0.0) if is_call else np.maximum(K - S_paths, 0.0)
    
    # Cash flows at maturity
    cash_flows = payoff[-1]
    
    # Backward induction
    for t in range(steps - 1, 0, -1):
        # Select in-the-money paths
        itm_mask = payoff[t] > 0
        if not np.any(itm_mask):
            continue
            
        x_itm = S_paths[t, itm_mask]
        y_itm = cash_flows[itm_mask] * df
        
        # Polynomial fit (degree = 2)
        poly_coefs = np.polyfit(x_itm, y_itm, 2)
        continuation_values = np.polyval(poly_coefs, x_itm)
        
        # Compare immediate exercise to continuation
        exercise_values = payoff[t, itm_mask]
        exercise_mask = exercise_values > continuation_values
        
        # Update cash flows
        actual_itm_indices = np.where(itm_mask)[0]
        exercise_indices = actual_itm_indices[exercise_mask]
        
        cash_flows[exercise_indices] = exercise_values[exercise_mask]
        # Set later cash flows on exercised paths to 0
        non_exercise_indices = actual_itm_indices[~exercise_mask]
        cash_flows[non_exercise_indices] = cash_flows[non_exercise_indices] * df
        
        # For paths that were not in-the-money at step t, discount their future cash flow
        other_indices = np.where(~itm_mask)[0]
        cash_flows[other_indices] = cash_flows[other_indices] * df
        
    return float(np.mean(cash_flows * df))

# --- Public Interfaces serving as unified Router ---

def black_scholes_price(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if HAS_CPP_KERNELS:
        return vc.black_scholes_price(S, K, r, T, sigma, is_call)
    return py_black_scholes_price(S, K, r, T, sigma, is_call)

def bs_delta(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if HAS_CPP_KERNELS:
        return vc.bs_delta(S, K, r, T, sigma, is_call)
    return py_bs_delta(S, K, r, T, sigma, is_call)

def bs_gamma(S: float, K: float, r: float, T: float, sigma: float) -> float:
    if HAS_CPP_KERNELS:
        return vc.bs_gamma(S, K, r, T, sigma)
    return py_bs_gamma(S, K, r, T, sigma)

def bs_vega(S: float, K: float, r: float, T: float, sigma: float) -> float:
    if HAS_CPP_KERNELS:
        return vc.bs_vega(S, K, r, T, sigma)
    return py_bs_vega(S, K, r, T, sigma)

def bs_theta(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if HAS_CPP_KERNELS:
        return vc.bs_theta(S, K, r, T, sigma, is_call)
    return py_bs_theta(S, K, r, T, sigma, is_call)

def bs_rho(S: float, K: float, r: float, T: float, sigma: float, is_call: bool) -> float:
    if HAS_CPP_KERNELS:
        return vc.bs_rho(S, K, r, T, sigma, is_call)
    return py_bs_rho(S, K, r, T, sigma, is_call)

def binomial_tree_price(S: float, K: float, r: float, T: float, sigma: float, steps: int, is_call: bool, is_american: bool) -> float:
    if HAS_CPP_KERNELS:
        return vc.binomial_tree_price(S, K, r, T, sigma, steps, is_call, is_american)
    return py_binomial_tree_price(S, K, r, T, sigma, steps, is_call, is_american)

def lsm_monte_carlo_price(S: float, K: float, r: float, T: float, sigma: float, paths: int, steps: int, is_call: bool, is_american: bool, seed: int = 42) -> float:
    if HAS_CPP_KERNELS:
        return vc.lsm_monte_carlo_price(S, K, r, T, sigma, paths, steps, is_call, is_american, seed)
    return py_lsm_monte_carlo_price(S, K, r, T, sigma, paths, steps, is_call, is_american, seed)
