#pragma once

#include <cstdint>

namespace volatria {

// Longstaff-Schwartz Least-Squares Monte Carlo (LSM) model for American options
double lsm_monte_carlo_price(double S, double K, double r, double T, double sigma,
                             int paths, int steps, bool is_call, bool is_american,
                             uint64_t seed = 42);

} // namespace volatria
