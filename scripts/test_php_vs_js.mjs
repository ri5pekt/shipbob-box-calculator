/**
 * test_php_vs_js.mjs
 * Runs the JS packing logic directly and the PHP script via CLI,
 * then compares results for every individual product + several multi-item combos.
 */
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, '..');

// ── Load data ────────────────────────────────────────────────────────────────
const products = JSON.parse(readFileSync(path.join(ROOT, 'data/products.json'), 'utf8'));
const boxes    = JSON.parse(readFileSync(path.join(ROOT, 'data/boxes.json'),    'utf8'));

// ── JS packing (same logic as packItems.ts) ───────────────────────────────────
import { pack3D, getDimension } from 'binpackingjs/3d';

const PADDING = 0.03;
const FLAT_CATEGORIES = new Set(['bundle', 'kit']);
// For test: all items use all 6 rotations (flat categories omitted for simplicity)

// SKUs that get the dedicated single-item box when ordered alone
const SINGLE_BOX_SKUS = new Set(['860005339785', '751889384926']); // Gravité, Face Cream

const productBySku = Object.fromEntries(products.map(p => [p.sku, p]));

function expandBundles(skus) {
  const lines = {};
  const normalized = skus.map(s => typeof s === 'string' ? { sku: s, qty: 1 } : s);
  for (const { sku, qty = 1 } of normalized) {
    const p = productBySku[sku];
    if (!p) continue;
    if (p.components?.length) {
      for (const comp of p.components) {
        const cp = productBySku[comp.sku];
        if (!cp) continue;
        lines[cp.sku] = { product: cp, quantity: (lines[cp.sku]?.quantity ?? 0) + comp.quantity * qty };
      }
    } else if (p.dimensions) {
      lines[p.sku] = { product: p, quantity: (lines[p.sku]?.quantity ?? 0) + qty };
    }
  }
  return Object.values(lines);
}

function jsPack(skus) {
  const orderLines = expandBundles(skus);
  if (!orderLines.length) return 'error';

  // single_shipping_box: exactly 1 unit of Gravité or Face Cream
  if (orderLines.length === 1 && orderLines[0].quantity === 1 &&
      SINGLE_BOX_SKUS.has(orderLines[0].product.sku)) {
    return 'single_shipping_box';
  }

  const items = orderLines.flatMap(({ product: p, quantity }) =>
    Array.from({ length: quantity }, (_, i) => ({
      name: `${p.id}__${i}`,
      width:  p.dimensions.length,
      height: p.dimensions.height,
      depth:  p.dimensions.width,
      weight: p.unit_weight_lbs ?? 1,
    }))
  );

  // Try small first, then large
  for (const box of boxes) {
    const d = box.dimensions;
    const bin = {
      name: box.id,
      width:  Math.round((d.length + PADDING) * 10000) / 10000,
      height: Math.round((d.height + PADDING) * 10000) / 10000,
      depth:  Math.round((d.width  + PADDING) * 10000) / 10000,
      maxWeight: 99999,
    };
    const result = pack3D({ bins: [bin], items });
    if (result.unfitItems.length === 0) {
      return box.id === 'small-shipper' ? 'single_branded_shipping_box' : 'regular_shipping_box';
    }
  }
  return 'bigger_shipping_box';
}

// ── PHP packing via CLI ───────────────────────────────────────────────────────
function phpPack(skus) {
  const phpScript = path.join(ROOT, 'api/box_selector.php');
  // Build query string: skus=sku1,sku2,...
  const skuList = skus.map(s => typeof s === 'string' ? s : s.sku).join(',');

  // We call PHP CLI and pass skus via a mini wrapper that sets $_GET
  const wrapper = `<?php
$_GET['skus'] = '${skuList}';
$_SERVER['REQUEST_METHOD'] = 'GET';
ob_start();
include '${phpScript.replace(/\\/g, '/')}';
echo ob_get_clean();
`;
  try {
    const out = execSync(`php -r "${wrapper.replace(/"/g, '\\"').replace(/\n/g, ' ')}"`, {
      encoding: 'utf8', timeout: 15000
    });
    const json = JSON.parse(out);
    return json.result;
  } catch (e) {
    return `PHP_ERROR: ${e.message.slice(0, 100)}`;
  }
}

// Alternative: write temp file and call it
function phpPackFile(skus) {
  const phpScript = path.join(ROOT, 'api/box_selector.php');
  const skuParam  = skus.map(s => typeof s === 'string' ? s : s.sku).join(',');
  const tmpScript = path.join(ROOT, 'scripts/_tmp_test.php');

  const code = `<?php
$_GET['skus'] = '${skuParam}';
$_SERVER['REQUEST_METHOD'] = 'GET';
include '${phpScript.replace(/\\/g, '/')}';
`;
  require('fs').writeFileSync(tmpScript, code);
  try {
    const out = execSync(`php "${tmpScript}"`, { encoding: 'utf8', timeout: 15000 });
    const json = JSON.parse(out);
    return json.result;
  } catch (e) {
    return `PHP_ERROR: ${e.message.slice(0, 100)}`;
  }
}

import { writeFileSync, unlinkSync } from 'fs';

function phpRun(skus) {
  const phpScript = path.join(ROOT, 'api/box_selector.php').replace(/\\/g, '/');
  // Expand quantities so PHP receives the same number of items as JS
  const skuParam  = skus.flatMap(s => {
    if (typeof s === 'string') return [s];
    return Array(s.qty ?? 1).fill(s.sku);
  }).join(',');
  const tmpScript = path.join(ROOT, 'scripts/_tmp_test.php');

  writeFileSync(tmpScript, `<?php $_GET['skus']='${skuParam}'; include '${phpScript}'; ?>`);
  try {
    const out = execSync(`php "${tmpScript}"`, { encoding: 'utf8', timeout: 15000 });
    return JSON.parse(out).result;
  } catch (e) {
    return `PHP_ERROR: ${e.stderr?.slice(0, 120) ?? e.message.slice(0, 120)}`;
  }
}

// ── Build test cases ──────────────────────────────────────────────────────────
const individualProducts = products.filter(p => p.dimensions && !p.components);
const bundles            = products.filter(p => p.components?.length);

const testCases = [];

// Every individual product alone
for (const p of individualProducts) {
  testCases.push({ label: p.title, skus: [p.sku] });
}

// Every bundle
for (const b of bundles) {
  testCases.push({ label: b.title, skus: [b.sku] });
}

// Some multi-product combos
testCases.push({ label: '2x Face Cream',              skus: [{ sku: '751889384926', qty: 2 }] });
testCases.push({ label: 'Face Cream + Face Wash',     skus: ['751889384926', '636665869647'] });
testCases.push({ label: '3x Face Cream + Neck Cream', skus: [{ sku: '751889384926', qty: 3 }, '860005339778'] });
testCases.push({ label: 'Face Cream + Gravite',       skus: ['751889384926', '860005339785'] });
testCases.push({ label: 'Body Wash + Shampoo',        skus: ['636665869678', '636665869661'] });
testCases.push({ label: '4x Lip Balm',                skus: [{ sku: '00860012469789', qty: 4 }] });
testCases.push({ label: 'Gravite + Varros',           skus: ['860005339785', '00860012469765'] });

// ── 50 additional test cases ──────────────────────────────────────────────────
// Quantities of small items
testCases.push({ label: '2x Lip Balm',                       skus: [{ sku: '00860012469789', qty: 2 }] });
testCases.push({ label: '3x Lip Balm',                       skus: [{ sku: '00860012469789', qty: 3 }] });
testCases.push({ label: '6x Lip Balm',                       skus: [{ sku: '00860012469789', qty: 6 }] });
testCases.push({ label: '10x Lip Balm',                      skus: [{ sku: '00860012469789', qty: 10 }] });
testCases.push({ label: '3x Gravité Tester',                 skus: [{ sku: '70117000', qty: 3 }] });
testCases.push({ label: '5x Gravité Tester',                 skus: [{ sku: '70117000', qty: 5 }] });
testCases.push({ label: '3x Nose Trimmer',                   skus: [{ sku: '70114000', qty: 3 }] });
testCases.push({ label: '4x Nose Trimmer',                   skus: [{ sku: '70114000', qty: 4 }] });
testCases.push({ label: '3x Beard Oil',                      skus: [{ sku: '860005339723', qty: 3 }] });
testCases.push({ label: '4x Beard Oil',                      skus: [{ sku: '860005339723', qty: 4 }] });
// Quantities of medium items
testCases.push({ label: '2x Face Cream',                     skus: [{ sku: '751889384926', qty: 2 }] });
testCases.push({ label: '3x Face Cream',                     skus: [{ sku: '751889384926', qty: 3 }] });
testCases.push({ label: '2x Gravité (cologne)',              skus: [{ sku: '860005339785', qty: 2 }] });
testCases.push({ label: '2x Hand Cream',                     skus: [{ sku: '00860014497216', qty: 2 }] });
testCases.push({ label: '3x Hand Cream',                     skus: [{ sku: '00860014497216', qty: 3 }] });
testCases.push({ label: '2x Anti-Gray Serum',                skus: [{ sku: '860012469703', qty: 2 }] });
testCases.push({ label: '4x Anti-Gray Serum',                skus: [{ sku: '860012469703', qty: 4 }] });
testCases.push({ label: '5x Infinite Male',                  skus: [{ sku: '860012469727', qty: 5 }] });
testCases.push({ label: '6x Infinite Male',                  skus: [{ sku: '860012469727', qty: 6 }] });
testCases.push({ label: '5x Skin Vitamin Gummies',           skus: [{ sku: '860005339747', qty: 5 }] });
// Quantities of large items
testCases.push({ label: '2x Body Wash',                      skus: [{ sku: '636665869678', qty: 2 }] });
testCases.push({ label: '3x Body Wash',                      skus: [{ sku: '636665869678', qty: 3 }] });
testCases.push({ label: '2x Shampoo',                        skus: [{ sku: '636665869661', qty: 2 }] });
testCases.push({ label: '2x Face Wash',                      skus: [{ sku: '636665869647', qty: 2 }] });
testCases.push({ label: '3x Face Wash',                      skus: [{ sku: '636665869647', qty: 3 }] });
// Two-product combos
testCases.push({ label: 'Face Cream + Shaving Gel',          skus: ['751889384926', '00860012469772'] });
testCases.push({ label: 'Face Wash + Body Wash',             skus: ['636665869647', '636665869678'] });
testCases.push({ label: 'Gravité + Deodorant',               skus: ['860005339785', '860012469710'] });
testCases.push({ label: 'Eye Cream + Lip Balm',              skus: ['00860012469796', '00860012469789'] });
testCases.push({ label: 'Hand Cream + Face Cream',           skus: ['00860014497216', '751889384926'] });
testCases.push({ label: 'Beard Oil + Anti-Gray Serum',       skus: ['860005339723', '860012469703'] });
testCases.push({ label: 'Comb + Nose Trimmer',               skus: ['70113000', '70114000'] });
testCases.push({ label: 'Scalp Massager + Comb',             skus: ['9162027', '70113000'] });
testCases.push({ label: 'Shaving Cream Stand + Shaving Gel', skus: ['00860012469758', '00860012469772'] });
testCases.push({ label: 'Face Mask + Neck Cream',            skus: ['636665869654', '860005339778'] });
testCases.push({ label: '2x Varros',                         skus: [{ sku: '00860012469765', qty: 2 }] });
testCases.push({ label: 'Face Cream + Ab Firming Cream',     skus: ['751889384926', '860010338421'] });
// Three-product combos
testCases.push({ label: 'Face Cream + Face Wash + Face Mask',     skus: ['751889384926', '636665869647', '636665869654'] });
testCases.push({ label: 'Gravité + Face Cream + Face Wash',       skus: ['860005339785', '751889384926', '636665869647'] });
testCases.push({ label: 'Comb + Nose Trimmer + Gravité Tester',   skus: ['70113000', '70114000', '70117000'] });
testCases.push({ label: 'Anti-Gray + Beard Oil + Face Cream',     skus: ['860012469703', '860005339723', '751889384926'] });
testCases.push({ label: 'Infinite Male + Skin + Hair Gummies',    skus: ['860012469727', '860005339747', '860005339761'] });
testCases.push({ label: 'Face Cream + Hand Cream + Neck Cream',   skus: ['751889384926', '00860014497216', '860005339778'] });
testCases.push({ label: 'Shaving Gel + Gravité + Deodorant',      skus: ['00860012469772', '860005339785', '860012469710'] });
testCases.push({ label: 'Body Wash + Shampoo + Hair Revival Kit', skus: ['636665869678', '636665869661', '860005339730'] });
// Mixed qty combos
testCases.push({ label: '2x Beard Oil + 2x Lip Balm',        skus: [{ sku: '860005339723', qty: 2 }, { sku: '00860012469789', qty: 2 }] });
testCases.push({ label: '2x Hand Cream + Face Cream',         skus: [{ sku: '00860014497216', qty: 2 }, '751889384926'] });
testCases.push({ label: '3x Eye Cream',                       skus: [{ sku: '00860012469796', qty: 3 }] });
testCases.push({ label: '4x Hair Vitamin Gummies',            skus: [{ sku: '860005339761', qty: 4 }] });
testCases.push({ label: 'Starter Bundle + extra Face Cream',  skus: ['9162025', '751889384926'] });

// ── Run tests ─────────────────────────────────────────────────────────────────
let passed = 0, failed = 0;
const failures = [];

console.log(`\nRunning ${testCases.length} test cases...\n`);
console.log(`${'Test case'.padEnd(50)} ${'JS'.padEnd(16)} ${'PHP'.padEnd(16)} Match`);
console.log('-'.repeat(92));

for (const tc of testCases) {
  const js  = jsPack(tc.skus);
  const php = phpRun(tc.skus);
  const ok  = js === php;

  if (ok) passed++; else { failed++; failures.push(tc.label); }

  const flag = ok ? '✓' : '✗ MISMATCH';
  console.log(`${tc.label.padEnd(50)} ${js.padEnd(16)} ${php.padEnd(16)} ${flag}`);
}

// Cleanup temp file
try { unlinkSync(path.join(ROOT, 'scripts/_tmp_test.php')); } catch {}

console.log('\n' + '='.repeat(92));
console.log(`Results: ${passed} passed, ${failed} failed`);

if (failures.length) {
  console.log('\nFailed cases:');
  failures.forEach(f => console.log('  ✗', f));
  process.exit(1);
} else {
  console.log('\n✓ PHP and JS produce identical results for all test cases.');
}
