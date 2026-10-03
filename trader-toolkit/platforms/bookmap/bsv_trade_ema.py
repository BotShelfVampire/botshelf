# BSV Trade EMA (Bookmap Python API add-on)
# ORIGINAL BSV STARTER. Not runtime tested by BSV. No order placement. No profitability claim.
# Bookmap's Python API is in open beta: https://github.com/BookmapAPI/python-api
# Draws an EMA of trade prices on the main heatmap, sampled every SAMPLE_SECONDS.
import bookmap as bm

EMA_LENGTH = 50
SAMPLE_SECONDS = 1.0
INTERVALS_PER_SAMPLE = int(SAMPLE_SECONDS * 10)  # on_interval fires every 0.1 s

state = {}
requests = {}
next_req = [1]


def new_request_id():
    req = next_req[0]
    next_req[0] += 1
    return req


def handle_subscribe_instrument(addon, alias, full_name, is_crypto, pips, size_multiplier, instrument_multiplier, supported_features):
    state[alias] = {"pips": pips, "last": None, "ema": None, "ticks": 0, "indicator": None}
    req = new_request_id()
    requests[req] = alias
    bm.register_indicator(addon, alias, req, "BSV Trade EMA %d" % EMA_LENGTH, "PRIMARY")
    bm.subscribe_to_trades(addon, alias, new_request_id())


def handle_unsubscribe_instrument(addon, alias):
    state.pop(alias, None)


def handle_indicator_response(addon, request_id, indicator_id):
    alias = requests.get(request_id)
    if alias in state:
        state[alias]["indicator"] = indicator_id


def handle_trades(addon, alias, price_level, size_level, is_otc, is_bid, is_execution_start, is_execution_end, aggressor_order_id, passive_order_id):
    s = state.get(alias)
    if s is not None:
        s["last"] = price_level  # price in pips (price level units)


def on_interval(addon, alias):
    s = state.get(alias)
    if s is None or s["last"] is None:
        return
    s["ticks"] += 1
    if s["ticks"] < INTERVALS_PER_SAMPLE:
        return
    s["ticks"] = 0
    a = 2.0 / (EMA_LENGTH + 1)
    s["ema"] = s["last"] if s["ema"] is None else s["last"] * a + s["ema"] * (1 - a)
    if s["indicator"] is not None:
        bm.add_point(addon, alias, s["indicator"], s["ema"])


if __name__ == "__main__":
    addon = bm.create_addon()
    bm.add_trades_handler(addon, handle_trades)
    bm.add_on_interval_handler(addon, on_interval)
    bm.add_indicator_response_handler(addon, handle_indicator_response)
    bm.start_addon(addon, handle_subscribe_instrument, handle_unsubscribe_instrument)
    bm.wait_until_addon_is_turned_off(addon)
