#include "binomial_tree.h"
#include <cmath>
#include <vector>
#include <algorithm>
#include <stdexcept>

namespace volatria {

double binomial_tree_price(double S, double K, double r, double T, double sigma, 
                           int steps, bool is_call, bool is_american) {
    if (S <= 0.0 || K <= 0.0 || T < 0.0 || sigma < 0.0 || steps <= 0) {
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
    double u = std::exp(sigma * std::sqrt(dt));
    double d = 1.0 / u;
    double p = (std::exp(r * dt) - d) / (u - d);
    double df = std::exp(-r * dt);

    // Array to store option values at the current step level
    std::vector<double> V(steps + 1);

    // Initialize values at maturity
    for (int i = 0; i <= steps; ++i) {
        double spot = S * std::pow(u, steps - i) * std::pow(d, i);
        if (is_call) {
            V[i] = std::max(0.0, spot - K);
        } else {
            V[i] = std::max(0.0, K - spot);
        }
    }

    // Step backward in time
    for (int j = steps - 1; j >= 0; --j) {
        for (int i = 0; i <= j; ++i) {
            double continuation = df * (p * V[i] + (1.0 - p) * V[i + 1]);
            if (is_american) {
                double spot = S * std::pow(u, j - i) * std::pow(d, i);
                double exercise = is_call ? std::max(0.0, spot - K) : std::max(0.0, K - spot);
                V[i] = std::max(exercise, continuation);
            } else {
                V[i] = continuation;
            }
        }
    }

    return V[0];
}

} // namespace volatria
