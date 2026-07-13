#include "black_scholes.h"

#define _USE_MATH_DEFINES
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace volatria {

double normal_cdf(double x) {
    return 0.5 * std::erfc(-x * M_SQRT1_2);
}

double normal_pdf(double x) {
    static const double inv_sqrt_2pi = 1.0 / std::sqrt(2.0 * M_PI);
    return inv_sqrt_2pi * std::exp(-0.5 * x * x);
}

double black_scholes_price(double S, double K, double r, double T, double sigma, bool is_call) {
    if (S <= 0.0 || K <= 0.0 || T < 0.0 || sigma < 0.0) {
        return 0.0;
    }
    if (T == 0.0) {
        if (is_call) {
            return std::max(0.0, S - K);
        } else {
            return std::max(0.0, K - S);
        }
    }

    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    double d2 = d1 - sigma * std::sqrt(T);

    if (is_call) {
        return S * normal_cdf(d1) - K * std::exp(-r * T) * normal_cdf(d2);
    } else {
        return K * std::exp(-r * T) * normal_cdf(-d2) - S * normal_cdf(-d1);
    }
}

double bs_delta(double S, double K, double r, double T, double sigma, bool is_call) {
    if (S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    if (is_call) {
        return normal_cdf(d1);
    } else {
        return normal_cdf(d1) - 1.0;
    }
}

double bs_gamma(double S, double K, double r, double T, double sigma) {
    if (S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    return normal_pdf(d1) / (S * sigma * std::sqrt(T));
}

double bs_vega(double S, double K, double r, double T, double sigma) {
    if (S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    return S * normal_pdf(d1) * std::sqrt(T);
}

double bs_theta(double S, double K, double r, double T, double sigma, bool is_call) {
    if (S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    double d2 = d1 - sigma * std::sqrt(T);

    double term1 = -(S * normal_pdf(d1) * sigma) / (2.0 * std::sqrt(T));
    if (is_call) {
        return term1 - r * K * std::exp(-r * T) * normal_cdf(d2);
    } else {
        return term1 + r * K * std::exp(-r * T) * normal_cdf(-d2);
    }
}

double bs_rho(double S, double K, double r, double T, double sigma, bool is_call) {
    if (S <= 0.0 || K <= 0.0 || T <= 0.0 || sigma <= 0.0) {
        return 0.0;
    }
    double d1 = (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
    double d2 = d1 - sigma * std::sqrt(T);

    if (is_call) {
        return K * T * std::exp(-r * T) * normal_cdf(d2);
    } else {
        return -K * T * std::exp(-r * T) * normal_cdf(-d2);
    }
}

double bs_implied_volatility(double market_price, double S, double K, double r, double T, bool is_call, double tol, int max_iter) {
    // Upper and lower bounds for bisection fallback
    double low_vol = 1e-5;
    double high_vol = 5.0;

    // Check bounds
    double min_price = is_call ? std::max(0.0, S - K * std::exp(-r * T)) : std::max(0.0, K * std::exp(-r * T) - S);
    double max_price = is_call ? S : K * std::exp(-r * T);

    if (market_price <= min_price) return 0.0;
    if (market_price >= max_price) return 5.0; // cap at upper bound

    // Initial guess
    double vol = 0.25;

    for (int i = 0; i < max_iter; ++i) {
        double price = black_scholes_price(S, K, r, T, vol, is_call);
        double diff = price - market_price;

        if (std::abs(diff) < tol) {
            return vol;
        }

        double vega = bs_vega(S, K, r, T, vol);

        // Newton-Raphson update if vega is large enough
        if (vega > 1e-4) {
            double next_vol = vol - diff / vega;
            if (next_vol > low_vol && next_vol < high_vol) {
                vol = next_vol;
                continue;
            }
        }

        // Bisection fallback
        if (diff > 0.0) {
            high_vol = vol;
        } else {
            low_vol = vol;
        }
        vol = 0.5 * (low_vol + high_vol);

        if ((high_vol - low_vol) < tol) {
            break;
        }
    }

    return vol;
}

} // namespace volatria
