# 🎰 FEEFLIP — PumpFun Creator Fee Lottery Bot

> Turn your PumpFun creator fees into a jackpot lottery for token holders on Solana

## Overview

**FEEFLIP** is an automated Solana bot that transforms PumpFun creator fees into a **lottery system** for token holders. Instead of the typical buyback-and-burn model, FEEFLIP collects creator fees and distributes them as **SOL jackpots** to random holders — with winning probability weighted by token balance.

This creates a powerful **hold incentive**: the more tokens you hold, the higher your chance of winning the next jackpot. Every trade on your token feeds the prize pool.

## How It Works

```
Trading Activity → Creator Fees Accumulate → Fee Claim → Lottery Pool Grows
                                                              ↓
                                              Timer Triggers Drawing
                                                              ↓
                                              Weighted Random Selection
                                                              ↓
                                              Winner Receives SOL Jackpot
                                                              ↓
                                              Cycle Repeats ♻️
```

### The Lottery Cycle

1. **Fee Collection** — Bot automatically claims creator fees from PumpFun at configurable intervals
2. **Pool Accumulation** — Claimed SOL accumulates in the lottery pool
3. **Drawing Trigger** — When the pool reaches a threshold OR timer expires, a drawing is triggered
4. **Weighted Selection** — A random holder is selected, weighted by their token balance (more tokens = higher chance)
5. **Jackpot Distribution** — Winner receives the SOL jackpot directly to their wallet
6. **Announcement** — Results are logged and optionally announced via Telegram
7. **Repeat** — The cycle restarts immediately

### Probability Formula

```
P(win) = holder_balance / total_circulating_supply
```

A holder with 5% of the supply has a 5% chance of winning each drawing.

## Features

- **Automated Fee Claiming** — Claims creator fees from PumpFun (pump) or Meteora DBC pools
- **Weighted Lottery** — Fair probability based on token holdings
- **Configurable Intervals** — Set drawing frequency (every N minutes)
- **Minimum Jackpot Threshold** — Only draw when pool reaches minimum SOL amount
- **Holder Snapshot** — Fetches current token holders via Solana RPC
- **Telegram Notifications** — Optional winner announcements to your community
- **Anti-Dust Filter** — Minimum token balance to qualify for lottery
- **Full Statistics** — Track total distributed, number of drawings, biggest jackpot
- **WebSocket Monitoring** — Real-time trade monitoring via PumpPortal WebSocket
- **SOL Reserve** — Keeps minimum SOL for transaction fees

## Quick Start

### Prerequisites

- Python 3.9+
- PumpPortal API key ([get one here](https://pumpportal.fun/create-wallet))
- Solana RPC endpoint (Helius, QuickNode, etc.)

### Installation

```bash
git clone https://github.com/mihafalev8/feeflip.git
cd feeflip
pip install -r requirements.txt
cp .env.example .env
```

### Configuration

Edit `.env` with your settings:

```env
PUMPPORTAL_API_KEY=your-api-key
TOKEN_MINT=your-token-contract-address
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
POOL_TYPE=pump
DRAW_INTERVAL_MINUTES=30
MIN_JACKPOT_SOL=0.1
MIN_HOLDER_TOKENS=1000
SOL_RESERVE=0.05
TELEGRAM_BOT_TOKEN=optional
TELEGRAM_CHAT_ID=optional
```

### Run

```bash
python feeflip.py
```

## Configuration Reference

| Parameter | Description | Default |
|---|---|---|
| `PUMPPORTAL_API_KEY` | Your PumpPortal Lightning API key | Required |
| `TOKEN_MINT` | Token contract address on PumpFun | Required |
| `SOLANA_RPC_URL` | Solana RPC endpoint | mainnet-beta |
| `POOL_TYPE` | Fee pool: `pump` or `meteora-dbc` | `pump` |
| `DRAW_INTERVAL_MINUTES` | Minutes between lottery drawings | `30` |
| `MIN_JACKPOT_SOL` | Minimum SOL in pool to trigger draw | `0.1` |
| `MIN_HOLDER_TOKENS` | Minimum tokens to qualify for lottery | `1000` |
| `SOL_RESERVE` | SOL kept for transaction fees | `0.05` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token for announcements | Optional |
| `TELEGRAM_CHAT_ID` | Telegram chat ID for announcements | Optional |

## Architecture

```
feeflip/
├── feeflip.py          # Main bot entry point
├── core/
│   ├── fee_claimer.py   # PumpPortal fee claiming logic
│   ├── lottery.py       # Weighted lottery engine
│   ├── holders.py       # Token holder snapshot fetcher
│   ├── distributor.py   # SOL distribution to winners
│   └── monitor.py       # WebSocket trade monitor
├── utils/
│   ├── config.py        # Configuration loader
│   ├── logger.py        # Logging setup
│   └── telegram.py      # Telegram notification helper
├── requirements.txt
├── .env.example
└── README.md
```

## How It Differs From Other Tools

| Feature | SNOWBALL | MeatballBot | FEEFLIP |
|---|---|---|---|
| Fee Usage | Buyback + Burn | Buyback + Burn | **Lottery Jackpot** |
| Holder Incentive | Price support | Price support | **Direct SOL rewards** |
| Gamification | None | None | **Lottery excitement** |
| Hold Motivation | Indirect | Indirect | **Direct (more tokens = more chance)** |
| Community Engagement | Low | Low | **High (drawings create events)** |

## Disclaimer

This bot is provided for educational and experimental purposes. Use at your own risk. Always test with small amounts first. The developers are not responsible for any financial losses.

## License

MIT License
