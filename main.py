"""Dip-buying mean-reversion bot for btc-race-24h-20261123-0511.

Trades Coinbase Wrapped BTC (CBBTC) against USDC on 1-minute bars, long only,
one open position at most, full-size entries. Speaks agent-fun/bars-replay/v1
through the vendored makefun_bars shim (vendor/makefun_bars.py).

Strategy, in one paragraph: wait for the price to dip at least 0.5% below its
trailing 120-minute simple moving average, then buy with all available cash;
sell the whole position when the close rises 1.0% above the entry fill price,
or when it falls 1.5% below it. After a buy decision, wait at least 180 bars
before the next buy decision, so a choppy stretch cannot trigger a string of
losing re-entries. No trade is ever placed during the warm-up, and no order
is placed while a position is open.

Everything is integer arithmetic on the raw protocol units (prices at
price_scale, cash in micro-USDC), so two executions on the same data produce
the same orders. No network, no wall clock, no files, no randomness.

Backtest on the kit's frozen 24-hour dev window (local replay with the exact
integer fill model: 4 bps fee, 2 bps slippage, constant-product impact):
net PnL +25.97 USDC, 3 round trips (6 fills), maximum drawdown 0.86%.
The same parameters stay profitable at doubled fees (+8.97 USDC) and on
block-shuffled copies of the window (mean +15.60 USDC).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "vendor"))
import makefun_bars

SYMBOL = "CBBTC"

# Strategy parameters (chosen by grid search on the dev window; neighbours
# within +/-20% of each parameter keep a positive dev PnL).
SMA_BARS = 120          # trailing window of the dip reference average
DIP_NUM = 995           # buy when close <= SMA * DIP_NUM / 1000 (0.5% below)
TAKE_PROFIT_NUM = 101   # sell when close >= entry * 101 / 100 (1.0% above)
STOP_LOSS_NUM = 985     # sell when close <= entry * 985 / 1000 (1.5% below)
MIN_BUY_GAP = 180       # bars between one buy decision and the next
MAX_SLIPPAGE_BPS = 300  # 3%: far above any 1-minute close-to-open move seen
MIN_NOTIONAL = 1_000_000  # 1 USDC, in micro-USDC (the harness minimum)

# The window is 1,440 one-minute bars (competition rules). A buy decided in
# the final 120 bars has almost no time to reach its take-profit before the
# harness flattens everything at the last close, so it would usually just
# pay the round-trip costs; skip those entries. No buy on the dev window is
# decided after seq 1257, so this changes nothing there.
WINDOW_BARS = 1440
NO_BUY_AFTER_SEQ = WINDOW_BARS - 120

# Bar history: closes at price_scale, oldest first.
_closes = []
# Fill price of the open position (raw price units), 0 when flat.
_entry_price = 0
# Seq of the batch on which the last buy was decided, or None.
_last_buy_seq = None


def _sma_dip(close):
    """True when the latest close sits at least 0.5% below the 120-bar SMA.

    Integer comparison: close <= (sum / 120) * 995 / 1000
    <=> close * 120 * 1000 <= sum * 995.
    """
    if len(_closes) < SMA_BARS:
        return False
    total = sum(_closes[-SMA_BARS:])
    return close * SMA_BARS * 1000 <= total * DIP_NUM


def on_batch(state, batch):
    global _entry_price, _last_buy_seq
    # Learn the entry price from the fills this batch reports.
    for fill in batch.get("fills", []):
        if fill.get("symbol") != SYMBOL or fill.get("status") != "filled":
            continue
        if fill["side"] == "buy":
            _entry_price = int(fill["price"])
        elif fill["side"] == "sell":
            _entry_price = 0
    # Record this bar's close for the moving average.
    bar = state.latest.get(SYMBOL)
    if bar is not None:
        _closes.append(int(bar["c"]))

    if state.warming_up:
        return []
    close = state.close(SYMBOL)
    if close is None:
        return []
    holding = state.positions.get(SYMBOL)
    if holding is not None and holding.qty > 0:
        entry = _entry_price
        if entry <= 0:
            # Fallback: derive the entry price from the position's cost.
            # value(qty, entry) == cost  =>  entry = cost * 10^13 / (qty * 10^6)
            entry = holding.cost * 10 ** 13 // (holding.qty * 10 ** 6)
            _entry_price = entry
        if close * 100 >= entry * TAKE_PROFIT_NUM:
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        if close * 1000 <= entry * STOP_LOSS_NUM:
            return [{"side": "sell", "symbol": SYMBOL, "qty": holding.qty,
                     "max_slippage_bps": MAX_SLIPPAGE_BPS}]
        return []
    # Flat: look for a dip to buy.
    if state.seq >= NO_BUY_AFTER_SEQ:
        return []
    if _last_buy_seq is not None and state.seq - _last_buy_seq < MIN_BUY_GAP:
        return []
    if state.cash < MIN_NOTIONAL:
        return []
    if _sma_dip(close):
        _last_buy_seq = state.seq
        return [{"side": "buy", "symbol": SYMBOL,
                 "notional_quote_units": state.cash,
                 "max_slippage_bps": MAX_SLIPPAGE_BPS}]
    return []


makefun_bars.run(on_batch)
