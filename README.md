# My Portfolio Management Project

An automated portfolio rebalancer built in Python, leveraging Alpaca’s API to maintain a strategic 50/25/25 split across FICC bond ETFs, US equities, and diversified ETFs. It performs statistical modeling, Monte Carlo simulation, risk forecasting (VaR), and convex optimization to decide daily trades—and executes them via Alpaca.

## Repository Structure

```
portfolio-management/
├─ config.json                # Single source of truth for tickers, weights, and risk parameters
├─ README.md                  # Project overview and instructions
├─ .env                       # (gitignored) Alpaca API credentials
├─ pyproject.toml             # Dependency manager is poetry
│
├─ settings/
│  ├─ __init__.py             # package marker
│  └─ config.py               # loads config.json into `Config` class attrs
│
├─ data/
│  ├─ __init__.py
│  └─ market_data.py          # `get_price_bars()` via alpaca-py
│
├─ models/
│  ├─ __init__.py
│  ├─ return_model.py         # `MixtureReturnModel` for multi-modal return forecasts
│  └─ simulator.py            # `MonteCarloSimulator` for price path simulation
│
├─ risk/
│  ├─ __init__.py
│  └─ var.py                  # `VaRCalculator` for Value-at-Risk estimation
│
├─ portfolio/
│  ├─ __init__.py
│  └─ allocator.py            # `Allocator` performs convex optimization
│
├─ trader/
│  ├─ __init__.py
│  └─ executor.py             # `submit_orders()` logs & sends Alpaca orders
│
└─ src/
   └─ main.py                 # Orchestrates daily_rebalance workflow
```

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-username/portfolio-management.git
   cd portfolio-management
   ```
2. **Create a virtual environment & install**
   ```bash
   poetry install
   poetry env activate
   ```
3. **Configure API credentials**
   - Copy `.env.example` to `.env` and fill in your Alpaca keys:
     ```ini
     ALPACA_API_KEY=your_key_here
     ALPACA_API_SECRET=your_secret_here
     TRADE_LOG="logs/trade_log.json"  # optional override
     ```
4. **Adjust **``
   - Edit tickers, `TARGET_WEIGHTS`, `VAR_CI`, etc., to suit your strategy.

## Usage

Run the daily rebalance script:

```bash
poetry shell
python -m src.main
```

Optionally, schedule it via cron or APScheduler by enabling the decorator in `main.py`.

## Workflow

1. **Load config**: tickers, weights, risk settings.
2. **Fetch data**: 1-year history of prices → log-returns.
3. **Model & simulate**: Gaussian-mixture fit → 5 000 next-day paths.
4. **Compute VaR**: quantify worst-case loss at CI.
5. **Optimize**: solve for weights maximizing `exp_return - 0.5*variance` under 50/25/25 and position limits.
6. **Execute**: calculate dollar deltas → buy/sell orders → log to `trade_log.json`.

## Logs and Outputs

- **Raw orders** are appended as NDJSON in `trade_log.json`, one JSON object per line:
  ```json
  {"timestamp":"2025-07-25T20:03:02.628516","symbol":"AAPL","side":"BUY","qty":10,"price":179.45,"nav":1002483.77, "cash_left": 51614.72}
  ```
- **Console** prints VaR and high-level status for each run.

## Extending

- Swap in different **return\_model** or **simulator** implementations.
- Adjust the **risk penalty** (λ) in `allocator.py` for more/less aggressive weighting.
- Integrate other Alpaca endpoints (crypto, options).

## References

- [alpaca-py Documentation](https://alpaca.markets/docs/)
- [CVXPY User Guide](https://www.cvxpy.org/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)

---

*Author: Riccardo di Silvio*
