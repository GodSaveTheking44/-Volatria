#include "lsm_monte_carlo.h"
#include <cmath>
#include <vector>
#include <random>
#include <algorithm>
#include <stdexcept>
#include <iostream>

namespace volatria {

// Solve a small linear system B * beta = C using Gaussian elimination with partial pivoting
static std::vector<double> solve_linear_system(std::vector<std::vector<double>>& B, std::vector<double>& C) {
    int n = B.size();
    for (int i = 0; i < n; ++i) {
        // Find pivot
        double max_val = std::abs(B[i][i]);
        int pivot_row = i;
        for (int r = i + 1; r < n; ++r) {
            if (std::abs(B[r][i]) > max_val) {
                max_val = std::abs(B[r][i]);
                pivot_row = r;
            }
        }

        // Swap rows
        if (pivot_row != i) {
            std::swap(B[i], B[pivot_row]);
            std::swap(C[i], C[pivot_row]);
        }

        // Check singularity
        if (std::abs(B[i][i]) < 1e-12) {
            // Singular or near-singular matrix, return fallback zero coefficients
            return std::vector<double>(n, 0.0);
        }

        // Eliminate
        for (int r = i + 1; r < n; ++r) {
            double factor = B[r][i] / B[i][i];
            for (int c = i; c < n; ++c) {
                B[r][c] -= factor * B[i][c];
            }
            C[r] -= factor * C[i];
        }
    }

    // Back substitution
    std::vector<double> beta(n);
    for (int i = n - 1; i >= 0; --i) {
        double sum = 0.0;
        for (int j = i + 1; j < n; ++j) {
            sum += B[i][j] * beta[j];
        }
        beta[i] = (C[i] - sum) / B[i][i];
    }

    return beta;
}

double lsm_monte_carlo_price(double S, double K, double r, double T, double sigma,
                             int paths, int steps, bool is_call, bool is_american,
                             uint64_t seed) {
    if (S <= 0.0 || K <= 0.0 || T < 0.0 || sigma < 0.0 || paths <= 0 || steps <= 0) {
        return 0.0;
    }
    if (T == 0.0) {
        if (is_call) {
            return std::max(0.0, S - K);
        } else {
            return std::max(0.0, K - S);
        }
    }

    double dt = T / steps;
    double df = std::exp(-r * dt);

    // Number of paths (use even number to support antithetic variates)
    int n_paths = (paths % 2 == 0) ? paths : paths + 1;

    // Simulate paths of Spot prices
    // paths_spot[i][j] stores the spot price of path i at step j
    std::vector<std::vector<double>> paths_spot(n_paths, std::vector<double>(steps + 1));
    for (int i = 0; i < n_paths; ++i) {
        paths_spot[i][0] = S;
    }

    std::mt19937_64 rng(seed);
    std::normal_distribution<double> normal_dist(0.0, 1.0);

    double drift = (r - 0.5 * sigma * sigma) * dt;
    double vol_sqrt_dt = sigma * std::sqrt(dt);

    for (int j = 1; j <= steps; ++j) {
        for (int i = 0; i < n_paths; i += 2) {
            double z = normal_dist(rng);
            // Path i (original)
            paths_spot[i][j] = paths_spot[i][j - 1] * std::exp(drift + vol_sqrt_dt * z);
            // Path i+1 (antithetic)
            paths_spot[i + 1][j] = paths_spot[i + 1][j - 1] * std::exp(drift - vol_sqrt_dt * z);
        }
    }

    // For European option, simply average the discounted payoffs at maturity
    if (!is_american) {
        double sum_payoff = 0.0;
        for (int i = 0; i < n_paths; ++i) {
            double spot = paths_spot[i][steps];
            double payoff = is_call ? std::max(0.0, spot - K) : std::max(0.0, K - spot);
            sum_payoff += payoff;
        }
        return (sum_payoff / n_paths) * std::exp(-r * T);
    }

    // American Option Valuation using Least-Squares backward induction
    // cash_flows[i] stores the cash flow for path i
    std::vector<double> cash_flows(n_paths);
    // stopping_steps[i] stores the step at which option is exercised
    std::vector<int> stopping_steps(n_paths);

    // Initialize at maturity
    for (int i = 0; i < n_paths; ++i) {
        double spot = paths_spot[i][steps];
        double payoff = is_call ? std::max(0.0, spot - K) : std::max(0.0, K - spot);
        cash_flows[i] = payoff;
        stopping_steps[i] = steps;
    }

    // Backward induction from steps-1 down to 1
    for (int j = steps - 1; j >= 1; --j) {
        // Step 1: Find paths that are in-the-money (ITM) at step j
        std::vector<int> itm_paths;
        for (int i = 0; i < n_paths; ++i) {
            double spot = paths_spot[i][j];
            double exercise = is_call ? (spot - K) : (K - spot);
            if (exercise > 0.0) {
                itm_paths.push_back(i);
            }
        }

        // If no paths are in-the-money, skip regression
        if (itm_paths.empty()) {
            continue;
        }

        // Step 2: Set up regression matrix
        // We use Monomials of normalized spot price (x = spot / K) up to degree 3: 1, x, x^2, x^3.
        // n_basis = 4
        int n_basis = 4;
        std::vector<std::vector<double>> B(n_basis, std::vector<double>(n_basis, 0.0));
        std::vector<double> C(n_basis, 0.0);

        for (int idx : itm_paths) {
            double spot = paths_spot[idx][j];
            double x = spot / K; // Normalize spot price

            // Basis functions
            double phi[4];
            phi[0] = 1.0;
            phi[1] = x;
            phi[2] = x * x;
            phi[3] = x * x * x;

            // Y is the discounted cash flow from optimal stopping step back to j
            double disc_y = cash_flows[idx] * std::exp(-r * (stopping_steps[idx] - j) * dt);

            for (int r_idx = 0; r_idx < n_basis; ++r_idx) {
                for (int c_idx = 0; c_idx < n_basis; ++c_idx) {
                    B[r_idx][c_idx] += phi[r_idx] * phi[c_idx];
                }
                C[r_idx] += phi[r_idx] * disc_y;
            }
        }

        // Step 3: Solve for regression coefficients beta
        std::vector<double> beta = solve_linear_system(B, C);

        // Step 4: Compare continuation value against immediate exercise
        for (int idx : itm_paths) {
            double spot = paths_spot[idx][j];
            double x = spot / K;

            // Immediate exercise value
            double exercise = is_call ? (spot - K) : (K - spot);

            // Continuation value estimate
            double continuation = beta[0] + beta[1] * x + beta[2] * x * x + beta[3] * x * x * x;

            if (exercise > continuation) {
                // Exercise early
                cash_flows[idx] = exercise;
                stopping_steps[idx] = j;
            }
        }
    }

    // Step 5: Average all cash flows discounted back to time 0
    double sum_pv = 0.0;
    for (int i = 0; i < n_paths; ++i) {
        sum_pv += cash_flows[i] * std::exp(-r * stopping_steps[i] * dt);
    }

    return sum_pv / n_paths;
}

} // namespace volatria
