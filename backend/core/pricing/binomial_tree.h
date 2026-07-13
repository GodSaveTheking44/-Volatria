#pragma once

namespace volatria {

// Cox-Ross-Rubinstein (CRR) Binomial Tree pricing model for American/European options
double binomial_tree_price(double S, double K, double r, double T, double sigma, 
                           int steps, bool is_call, bool is_american);

} // namespace volatria
