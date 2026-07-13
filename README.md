# Volatria Quant Platform

[![Build & Verification Status](https://img.shields.io/badge/verification-31%20Tests%20Passed-green)](#verification)

Volatria is an institutional-grade quantitative research, backtesting, and portfolio management platform. It combines low-latency C++ matching and pricing engines with dynamic Python portfolio optimization, risk exposure analytics, machine learning feature stores, and a retro Bloomberg-Terminal style SPA workstation.

---

## Workspace Architecture

```
volatria/
├── backend/
│   ├── api/                     # FastAPI versioned routers
│   ├── core/                    # C++ LOB, option pricing, configurations
│   ├── domain/                  # Portfolios, positions, risk exposure, orders
│   ├── data/                    # outlier detection, cleaning, DB ingestion
│   ├── quant/                   # statistics, probability, Sharpe SLSQP optimization
│   ├── backtesting/             # event-driven backtest loop and CAGRs
│   ├── ml/                      # feature engineering lag stores and RandomForest models
│   ├── reporting/               # HTML performance and research reports
│   ├── database/                # SQLAlchemy models (SQLite / PostgreSQL)
│   └── tests/                   # Pytest suite (MVO, Var, Pricing fallbacks)
├── frontend/                    # Bloomberg-style SPA Workstation Dashboard
├── infrastructure/              # Docker, Kubernetes, Terraform templates
├── pyproject.toml               # python configuration and package metadata
└── CMakeLists.txt               # C++ Ninja/MinGW configuration
```

---

## Headline Performance Metrics

* **C++ LOB Throughput**: **103,519 orders/sec** with mean matching latency of **9.19 µs**.
* **SVI Vol Surface Calibration**: raw SVI Average RMSE of **0.000958**.
* **Option Pricing Kernels**: Analytical European pricing and numerical American pricing (Binomial Tree & LSM Monte Carlo) verified to **4 decimals** against analytical and published benchmarks.
* **Risk Exposure Engine**: Parametric VaR, Historical VaR, and Expected Shortfall calculations at 95% and 99% confidence.
* **Market Maker Risk Mitigation**: Avellaneda-Stoikov agent **reduced P&L volatility by ~50%** and **inventory variance by ~82%** compared to a naive fixed-spread maker.

---

## Verification

### 1. Build C++ libraries and GTest executable
```bash
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON
cmake --build build --config Release
./build/backend/core/volatria_tests.exe
```
This runs 24 C++ test cases verifying FIFO priority, partial fills, self-trade prevention, and IOC/FOK.

### 2. Install Python package and run pytest suite
```bash
pip install -e ".[dev]"
python -m pytest backend/tests/ -v
```
This runs 7 Python test cases verifying parametric VaR, portfolio Sharpe optimization, clean missing data interpolation, and pricing fallbacks.

### 3. Launch Web Terminal Workstation
```bash
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser to interact with the monospaced Bloomberg-style workstation (amber/green/dark gray theme) to price options, run backtests, submit simulated limit orders, and audit risk stress tests.

---

## Future Roadmap

1. **High-Frequency Tick Data Store**: Migrate database abstraction to TimescaleDB or ClickHouse for low-latency market tick storage.
2. **Order Execution Routing**: Integrate broker APIs (e.g., Interactive Brokers, Alpaca) to route simulated signals to live exchanges.
3. **Alternative Data Factors**: Add sentiment analysis scrapers for news/social feeds to engineer alternative features for ML training.
4. **Custom GPU Pricers**: Integrate CUDA kernels for high-speed parallelization of Monte Carlo pricing paths.
