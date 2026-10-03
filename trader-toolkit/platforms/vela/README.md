# Vela custom chart starter

Use this when you want to build a small browser-based chart of your own.

Vela is an external charting library. BSV does not redistribute Vela here. Install it from its official package and review its license.

## Install

```bash
npm install @luxalgo/vela
```

## Run

Provide your own OHLCV bars and import `starter.js`.

Each bar must contain:

```js
{ time, open, high, low, close, volume }
```

`time` is epoch milliseconds.

## Why this matters

With this route, BSV can provide reusable chart-tool recipes while you control:

- the page
- the data source
- the theme
- indicators
- drawings/plugins
- how the result is embedded in your own product

This starter uses only the Vela chart package. Add an external scripting engine only after reviewing that engine's own license and requirements.

Official quickstart: https://docs.luxalgo.com/vela/user/quickstart
