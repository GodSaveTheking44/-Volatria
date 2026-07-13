#pragma once

namespace volatria {

// Calculate cumulative standard normal distribution CDF N(x)
double normal_cdf(double x);

// Calculate standard normal distribution PDF n(x)
double normal_pdf(double x);

// Analytical Black-Scholes European option price
double black_scholes_price(double S, double K, double r, double T, double sigma, bool is_call);

// Greeks
double bs_delta(double S, double K, double r, double T, double sigma, bool is_call);
double bs_gamma(double S, double K, double r, double T, double sigma);
double bs_vega(double S, double K, double r, double T, double sigma);
double bs_theta(double S, double K, double r, double T, double sigma, bool is_call);
double bs_rho(double S, double K, double r, double T, double sigma, bool is_call);

// Implied Volatility calculation via Newton-Raphson with fallback to Bisection
double bs_implied_volatility(double market_price, double S, double K, double r, double T, bool is_call, double tol = 1e-6, int max_iter = 100);

} // namespace volatria
