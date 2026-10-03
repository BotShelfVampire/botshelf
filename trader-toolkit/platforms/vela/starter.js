import { Vela } from '@luxalgo/vela';

/**
 * ORIGINAL BSV STARTER.
 * Replace sampleBars with your own OHLCV data.
 * This file intentionally performs no network request and no order execution.
 */
const sampleBars = [
  { time: Date.UTC(2026, 0, 1), open: 100, high: 106, low: 98, close: 104, volume: 1000 },
  { time: Date.UTC(2026, 0, 2), open: 104, high: 108, low: 102, close: 107, volume: 1200 },
  { time: Date.UTC(2026, 0, 3), open: 107, high: 109, low: 103, close: 105, volume: 900 }
];

const chart = new Vela('#chart', {
  data: sampleBars,
  timeframe: '1d',
  theme: 'dark'
});

await chart.ready();

console.log('BSV Vela starter ready. Replace sampleBars with your own OHLCV data.');
