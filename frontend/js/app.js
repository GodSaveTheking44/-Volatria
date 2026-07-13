// Volatria Quant Workstation JavaScript Controller

// Active Tab navigation
const tabs = document.querySelectorAll('.nav-tab');
const contents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        contents.forEach(c => c.classList.remove('active'));
        
        tab.classList.add('active');
        const target = document.getElementById(`tab-${tab.dataset.tab}`);
        if (target) target.classList.add('active');
    });
});

// Update Clock
setInterval(() => {
    const timeDisplay = document.getElementById('time-display');
    const now = new Date();
    timeDisplay.textContent = now.toISOString().replace('T', ' ').substring(0, 19);
}, 1000);

// Initialize charts
let marketChart = null;
let equityChart = null;

function renderMarketChart(prices) {
    const ctx = document.getElementById('market-chart').getContext('2d');
    const labels = prices.map(p => p.date);
    const data = prices.map(p => p.close);
    
    if (marketChart) marketChart.destroy();
    
    marketChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'SPY Close Price ($)',
                data: data,
                borderColor: '#00e5ff',
                backgroundColor: 'rgba(0, 229, 255, 0.1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { grid: { color: '#222' }, ticks: { color: '#ccc' } },
                y: { grid: { color: '#222' }, ticks: { color: '#ccc' } }
            },
            plugins: {
                legend: { labels: { color: '#ccc' } }
            }
        }
    });
}

function renderEquityChart(portfolioValues) {
    const ctx = document.getElementById('equity-chart').getContext('2d');
    const labels = portfolioValues.map((_, i) => `Day ${i}`);
    
    if (equityChart) equityChart.destroy();
    
    equityChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Equity Curve ($)',
                data: portfolioValues,
                borderColor: '#00ff66',
                backgroundColor: 'rgba(0, 255, 102, 0.1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: { grid: { color: '#222' }, ticks: { color: '#ccc' } },
                y: { grid: { color: '#222' }, ticks: { color: '#ccc' } }
            },
            plugins: {
                legend: { labels: { color: '#ccc' } }
            }
        }
    });
}

// Fetch Market Data & Order Book
async function fetchMarketData() {
    try {
        const lobRes = await fetch('/api/v1/market-data/orderbook');
        const lobData = await lobRes.json();
        
        const tbody = document.querySelector('#lob-table tbody');
        tbody.innerHTML = '';
        
        // Match bids and asks levels
        const maxLevels = Math.max(lobData.bids.length, lobData.asks.length);
        for (let i = 0; i < maxLevels; i++) {
            const bid = lobData.bids[i] || { price: '-', qty: '-' };
            const ask = lobData.asks[i] || { price: '-', qty: '-' };
            
            tbody.innerHTML += `
                <tr>
                    <td class="green">${bid.qty}</td>
                    <td class="green">${bid.price === '-' ? '-' : bid.price.toFixed(2)}</td>
                    <td class="red">${ask.price === '-' ? '-' : ask.price.toFixed(2)}</td>
                    <td class="red">${ask.qty}</td>
                </tr>
            `;
        }
    } catch (e) {
        console.error("Error loading order book data:", e);
    }
}

async function fetchHistoricalPrices() {
    try {
        const res = await fetch('/api/v1/market-data/prices?symbol=SPY');
        const data = await res.json();
        renderMarketChart(data.prices);
    } catch (e) {
        console.error("Error loading prices:", e);
    }
}

// Option Pricing calculators
async function calculateBS() {
    const spot = document.getElementById('bs-spot').value;
    const strike = document.getElementById('bs-strike').value;
    const rate = document.getElementById('bs-rate').value;
    const vol = document.getElementById('bs-vol').value;
    const maturity = document.getElementById('bs-maturity').value;
    const isCall = document.getElementById('bs-is-call').checked;
    
    try {
        const res = await fetch(`/api/v1/research/pricing/black-scholes?S=${spot}&K=${strike}&r=${rate}&T=${maturity}&sigma=${vol}&is_call=${isCall}`);
        const data = await res.json();
        
        document.getElementById('bs-price-val').textContent = `$${data.price.toFixed(4)}`;
        document.getElementById('bs-delta-val').textContent = data.greeks.delta.toFixed(4);
        document.getElementById('bs-gamma-val').textContent = data.greeks.gamma.toFixed(4);
        document.getElementById('bs-vega-val').textContent = data.greeks.vega.toFixed(4);
        document.getElementById('bs-theta-val').textContent = data.greeks.theta.toFixed(4);
        document.getElementById('bs-rho-val').textContent = data.greeks.rho.toFixed(4);
    } catch (e) {
        alert("Error pricing option");
    }
}

async function calculateNumerical() {
    const spot = document.getElementById('bs-spot').value;
    const strike = document.getElementById('bs-strike').value;
    const rate = document.getElementById('bs-rate').value;
    const vol = document.getElementById('bs-vol').value;
    const maturity = document.getElementById('bs-maturity').value;
    const isCall = document.getElementById('bs-is-call').checked;
    const steps = document.getElementById('num-steps').value;
    const paths = document.getElementById('num-paths').value;
    
    try {
        const res = await fetch(`/api/v1/research/pricing/numerical?S=${spot}&K=${strike}&r=${rate}&T=${maturity}&sigma=${vol}&steps=${steps}&paths=${paths}&is_call=${isCall}&is_american=true`);
        const data = await res.json();
        
        document.getElementById('binom-price-val').textContent = `$${data.binomial_tree_price.toFixed(4)}`;
        document.getElementById('lsm-price-val').textContent = `$${data.lsm_monte_carlo_price.toFixed(4)}`;
    } catch (e) {
        alert("Error running numerical pricers");
    }
}

// Backtesting Controller
async function runBacktest() {
    const entry = document.getElementById('entry-z').value;
    const exit = document.getElementById('exit-z').value;
    
    try {
        const res = await fetch(`/api/v1/backtests/run?strategy_name=Stat-Arb%20Pairs&entry_z=${entry}&exit_z=${exit}`, { method: 'POST' });
        const data = await res.json();
        
        document.getElementById('bt-sharpe').textContent = data.metrics.sharpe_ratio.toFixed(4);
        document.getElementById('bt-maxdd').textContent = `${(data.metrics.max_drawdown * 100).toFixed(2)}%`;
        document.getElementById('bt-cagr').textContent = `${(data.metrics.cagr * 100).toFixed(2)}%`;
        document.getElementById('bt-winrate').textContent = `${(data.metrics.win_rate * 100).toFixed(1)}%`;
        
        renderEquityChart(data.portfolio_values);
    } catch (e) {
        alert("Error executing backtest");
    }
}

// Portfolio Summary loading
async function fetchPortfolio() {
    try {
        const res = await fetch('/api/v1/portfolio/summary');
        const data = await res.json();
        
        document.getElementById('port-cash').textContent = `$${data.cash.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        document.getElementById('port-nav').textContent = `$${data.net_asset_value.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        
        const tbody = document.querySelector('#holdings-table tbody');
        tbody.innerHTML = '';
        
        data.holdings.forEach(h => {
            const pnlClass = h.unrealized_pnl >= 0 ? 'green' : 'red';
            tbody.innerHTML += `
                <tr>
                    <td class="amber">${h.symbol}</td>
                    <td>${h.name}</td>
                    <td>${h.quantity}</td>
                    <td>$${h.average_cost.toFixed(2)}</td>
                    <td>$${h.current_price.toFixed(2)}</td>
                    <td>$${h.market_value.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
                    <td class="${pnlClass}">$${h.unrealized_pnl.toFixed(2)}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading portfolio summary:", e);
    }
}

// Risk Metrics
async function fetchRisk() {
    try {
        const res = await fetch('/api/v1/risk/metrics');
        const data = await res.json();
        
        document.getElementById('risk-param-var').textContent = `$${data.metrics_95_pct.parametric_var.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
        document.getElementById('risk-hist-var').textContent = `$${data.metrics_95_pct.historical_var.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
        document.getElementById('risk-es').textContent = `$${data.metrics_95_pct.expected_shortfall.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
        
        const stress = data.stress_scenarios;
        document.getElementById('stress-crash').textContent = `$${stress.market_crash_impact.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
        document.getElementById('stress-vol').textContent = `$${stress.volatility_spike_impact.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
        document.getElementById('stress-rate').textContent = `$${stress.interest_rate_shock_impact.toLocaleString(undefined, {maximumFractionDigits: 2})}`;
    } catch (e) {
        console.error("Error loading risk analytics:", e);
    }
}

// Machine Learning Experiments
async function fetchExperiments() {
    try {
        const res = await fetch('/api/v1/models/experiments');
        const data = await res.json();
        
        const tbody = document.querySelector('#experiments-table tbody');
        tbody.innerHTML = '';
        
        data.forEach(r => {
            tbody.innerHTML += `
                <tr>
                    <td class="amber">${r.name}</td>
                    <td>${r.version}</td>
                    <td>${r.metrics.val_mse.toFixed(6)}</td>
                    <td class="green">${r.metrics.val_r2.toFixed(4)}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading models experiments:", e);
    }
}

// Cointegration Research
async function fetchResearch() {
    try {
        const res = await fetch('/api/v1/research/cointegration');
        const data = await res.json();
        
        document.getElementById('res-beta').textContent = data.beta.toFixed(4);
        document.getElementById('res-alpha').textContent = data.alpha.toFixed(4);
        document.getElementById('res-adf').textContent = data.eg_pvalue.toFixed(6);
        
        const stats = data.spread_stats;
        const container = document.getElementById('spread-stats-summary');
        container.innerHTML = `
            <div class="output-item">Mean: <span>${stats.mean.toFixed(6)}</span></div>
            <div class="output-item">Std Dev: <span>${stats.std.toFixed(6)}</span></div>
            <div class="output-item">Skewness: <span class="amber">${stats.skewness.toFixed(4)}</span></div>
            <div class="output-item">Kurtosis: <span class="amber">${stats.kurtosis.toFixed(4)}</span></div>
        `;
    } catch (e) {
        console.error("Error loading research data:", e);
    }
}

// Order Entry submission
async function submitOrder() {
    const symbol = document.getElementById('trade-symbol').value;
    const qty = document.getElementById('trade-qty').value;
    const price = document.getElementById('trade-price').value;
    const side = document.getElementById('trade-side').value;
    
    try {
        const res = await fetch('/api/v1/trading/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbol, quantity: parseInt(qty), price: parseFloat(price), side, type: 'LIMIT' })
        });
        const data = await res.json();
        alert(`Order successfully executed! ID: ${data.order_id}, Status: ${data.status}`);
        fetchPortfolio();
        fetchOrders();
    } catch (e) {
        alert("Error executing order");
    }
}

async function fetchOrders() {
    try {
        const res = await fetch('/api/v1/trading/orders');
        const data = await res.json();
        
        const tbody = document.querySelector('#orders-table tbody');
        tbody.innerHTML = '';
        
        data.forEach(o => {
            const sideClass = o.side === 'BUY' ? 'green' : 'red';
            tbody.innerHTML += `
                <tr>
                    <td>${o.timestamp.replace('T', ' ').substring(11, 19)}</td>
                    <td class="amber">${o.symbol}</td>
                    <td class="${sideClass}">${o.side}</td>
                    <td>$${o.price.toFixed(2)}</td>
                    <td>${o.quantity}</td>
                    <td class="green">${o.status}</td>
                </tr>
            `;
        });
    } catch (e) {
        console.error("Error loading orders history:", e);
    }
}

// Terminal Interactive input parser
const termInput = document.getElementById('terminal-input');
termInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        const val = termInput.value.trim().toLowerCase();
        termInput.value = '';
        
        if (val.startsWith('/tab ')) {
            const tabName = val.substring(5).trim();
            const tabButton = document.querySelector(`.nav-tab[data-tab="${tabName}"]`);
            if (tabButton) tabButton.click();
        } else if (val === '/run backtest') {
            document.querySelector(`.nav-tab[data-tab="statarb"]`).click();
            runBacktest();
        } else if (val.startsWith('/price ')) {
            const sym = val.substring(7).trim().toUpperCase();
            document.getElementById('trade-symbol').value = sym;
            document.querySelector(`.nav-tab[data-tab="trading"]`).click();
        } else {
            alert(`Unknown CLI command: "${val}". Try "/tab pricing" or "/run backtest".`);
        }
    }
});

// Load everything on startup
window.onload = () => {
    fetchMarketData();
    fetchHistoricalPrices();
    fetchPortfolio();
    fetchRisk();
    fetchExperiments();
    fetchResearch();
    fetchOrders();
    
    // Poll the limit order book feed every 3 seconds for simulated live price movement
    setInterval(fetchMarketData, 3000);
};
