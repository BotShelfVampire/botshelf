#!/usr/bin/env node
// Structural check of the generator's TradeStation EasyLanguage output for every recipe.
// NOT a TradeStation Verify: it only checks things BSV can check without the platform
// (balanced comments/parentheses, statements end with ';', every V_/S_ name is declared in Vars,
// only documented functions/reserved words are called, plot numbers 1-99, alert text <= 256 chars, no order words).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '../..');
const dir = path.join(root, 'trader-toolkit/recipes');
const allowedCalls = new Set(['XAverage', 'Average', 'RSI', 'AvgTrueRange', 'BarStatus', 'IFF', 'Alert']);
const keywords = new Set(['and', 'or', 'not', 'if', 'then', 'Vars', 'double', 'bool', 'true', 'false', 'Time', 'Open', 'High', 'Low', 'Close']);
let checks = 0, failures = 0, files = 0;
const fail = (f, m) => { failures++; console.error('FAIL', f, m); };
for (const f of fs.readdirSync(dir).filter(x => x.endsWith('.json')).sort()) {
  const code = execFileSync('node', [path.join(root, 'trader-toolkit/generator/render.mjs'), path.join(dir, f), '--target', 'easylanguage'], { encoding: 'utf8' });
  files++;
  // 1. comments: balanced, not nested
  let depth = 0, ok = true;
  for (const ch of code) { if (ch === '{') { depth++; if (depth > 1) ok = false; } if (ch === '}') { depth--; if (depth < 0) ok = false; } }
  checks++; if (!ok || depth !== 0) fail(f, 'unbalanced or nested { } comments');
  const body = code.replace(/\{[^}]*\}/g, ' ');
  // 2. strings: balanced quotes per line; strip them for the remaining checks
  checks++; if (body.split('\n').some(l => (l.match(/"/g) || []).length % 2)) fail(f, 'odd number of quotes on a line');
  const strings = [...body.matchAll(/"([^"]*)"/g)].map(m => m[1]);
  const plain = body.replace(/"[^"]*"/g, '""');
  // 3. statements: join "if ... then" with the next line, then each statement ends with ';'
  const stmts = plain.split(';').map(s => s.trim()).filter(Boolean);
  checks++; if (plain.trim() && !plain.trim().endsWith(';')) fail(f, 'last statement does not end with ;');
  for (const s of stmts) {
    checks++;
    let d = 0; for (const ch of s) { if (ch === '(') d++; if (ch === ')') d--; if (d < 0) break; }
    if (d !== 0) fail(f, 'unbalanced parentheses: ' + s.slice(0, 80));
  }
  // 4. declarations
  const decl = /Vars:\s*([^;]*);/.exec(plain);
  const declared = new Set(decl ? [...decl[1].matchAll(/\b(?:double|bool)\s+([VS]_[A-Za-z0-9_]+)\(/g)].map(m => m[1].toLowerCase()) : []);
  for (const m of plain.matchAll(/\b([VS]_[A-Za-z0-9_]+)\b/g)) { checks++; if (!declared.has(m[1].toLowerCase())) fail(f, 'undeclared ' + m[1]); }
  checks++; if (decl && [...decl[1].matchAll(/\b([VS]_[A-Za-z0-9_]+)\(/g)].length !== declared.size) fail(f, 'duplicate or untyped declaration');
  // 5. calls
  for (const m of plain.matchAll(/\b([A-Za-z_][A-Za-z0-9_]*)\s*\(/g)) {
    const n = m[1]; if (/^[VS]_/.test(n) || keywords.has(n)) continue;
    checks++;
    if (/^Plot(\d+)$/.test(n)) { const k = +n.slice(4); if (k < 1 || k > 99) fail(f, 'plot number ' + k); continue; }
    if (!allowedCalls.has(n)) fail(f, 'call not in documented list: ' + n);
  }
  // 6. alerts / order words
  for (const s of strings) { checks++; if (s.length > 256) fail(f, 'string > 256 chars'); }
  checks++; if (/\b(Buy|Sell|SellShort|BuyToCover)\b/i.test(plain)) fail(f, 'order word in an indicator');
}
console.log(JSON.stringify({ target: 'easylanguage', recipes: files, checks, failures, note: 'structural check only, not a TradeStation Verify' }));
process.exit(failures ? 1 : 0);
