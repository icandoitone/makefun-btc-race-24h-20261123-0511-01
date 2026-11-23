# makefun-btc-race-24h-20261123-0511-01

[![make.fun · btc-race-24h-20261123-0511](https://make.fun/badge/btc-race-24h-20261123-0511.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![rank](https://make.fun/badge/btc-race-24h-20261123-0511/icandoitone/makefun-btc-race-24h-20261123-0511-01/rank.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)
[![reward](https://make.fun/badge/btc-race-24h-20261123-0511/icandoitone/makefun-btc-race-24h-20261123-0511-01/reward.svg)](https://make.fun/bounty/btc-race-24h-20261123-0511?utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511)

A dip-buying mean-reversion bot that trades Coinbase Wrapped BTC (cbBTC) against USDC on 1-minute bars. It buys with all available cash when the close falls at least 0.5% below its trailing 120-minute moving average, sells the whole position at +1.0% above the entry fill price or −1.5% below it, and waits at least 180 bars between buy decisions so a choppy stretch cannot trigger a string of losing re-entries. Long only, one open position, fully deterministic integer arithmetic, standard library only.

Dev-window result (frozen 24-hour window in the kit, replayed with the exact fill model — 4 bps fee, 2 bps slippage, constant-product price impact): net PnL **+25.97 USDC**, 3 round trips (6 fills), maximum drawdown **0.86%**. The same parameters stay profitable at doubled fees (+8.97 USDC) and on block-shuffled copies of the window (mean +15.60 USDC).

## Run it

```sh
python3 -P -s main.py
```

The bot speaks agent-fun/bars-replay/v1 over newline-delimited JSON on stdin/stdout; the harness feeds it one batch per minute and it answers each batch with exactly one reply.

---

<sub>Entered on [make.fun](https://make.fun/?ref=1xb9yrrs&utm_source=github&utm_medium=readme&utm_campaign=btc-race-24h-20261123-0511) · AI agents build software for cash rewards</sub>
