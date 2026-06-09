<?php
/**
 * box_selector.php
 *
 * Receives a list of SKUs (+ optional quantities) and returns the best
 * shipping box using the exact same 3D bin-packing algorithm as the JS app
 * (a PHP port of binpackingjs/3d).
 *
 * Request (GET or POST JSON):
 *   { "skus": ["860005339723", "636665869647"] }
 *   { "skus": [{"sku":"860005339723","qty":2}, {"sku":"636665869647","qty":1}] }
 *
 * Response:
 *   { "result": "small_shipper" | "large_shipper" | "bigger_shipper",
 *     "message": "...",
 *     "fitted_items": 3,
 *     "total_items": 3 }
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');

// ─────────────────────────────────────────────────────────────────────────────
// 1.  Hardcoded data (products + boxes) — last updated 2026-06-08
// ─────────────────────────────────────────────────────────────────────────────
$BOXES = [
    [
        'id'         => 'small-shipper',
        'name'       => 'Small Shipper',
        'dimensions' => ['length' => 6.1024, 'width' => 6.1024, 'height' => 2.5591],
    ],
    [
        'id'         => 'large-shipper',
        'name'       => 'Large Shipper',
        'dimensions' => ['length' => 8.4646, 'width' => 6.6929, 'height' => 3.1496],
    ],
];

$PRODUCTS = [
    // ── Individual products ──────────────────────────────────────────────────
    ['id'=>7,       'title'=>'Particle Face Cream',               'sku'=>'751889384926',    'dimensions'=>['length'=>6.1,  'width'=>2.56, 'height'=>2.56], 'unit_weight_lbs'=>0.2875],
    ['id'=>2299802, 'title'=>'Particle 43 Anti-Aging Shaving Gel','sku'=>'00860012469772',  'dimensions'=>['length'=>6.0,  'width'=>2.1,  'height'=>2.1],  'unit_weight_lbs'=>0.5417],
    ['id'=>3175815, 'title'=>'Particle Instant Eye Firming Cream','sku'=>'00860012469796',  'dimensions'=>['length'=>4.1,  'width'=>2.2,  'height'=>2.2],  'unit_weight_lbs'=>0.1669],
    ['id'=>3546870, 'title'=>'Particle Face Shield',              'sku'=>'860010338483',    'dimensions'=>['length'=>6.1,  'width'=>1.38, 'height'=>1.38], 'unit_weight_lbs'=>0.2875],
    ['id'=>100362,  'title'=>'Particle Face Wash',                'sku'=>'636665869647',    'dimensions'=>['length'=>6.61, 'width'=>1.97, 'height'=>1.97], 'unit_weight_lbs'=>0.4875],
    ['id'=>100370,  'title'=>'Particle Face Mask',                'sku'=>'636665869654',    'dimensions'=>['length'=>3.66, 'width'=>2.8,  'height'=>2.8],  'unit_weight_lbs'=>0.6937],
    ['id'=>3611263, 'title'=>'Particle Lip Balm',                 'sku'=>'00860012469789',  'dimensions'=>['length'=>3.0,  'width'=>0.8,  'height'=>0.8],  'unit_weight_lbs'=>0.0583],
    ['id'=>1646173, 'title'=>'Particle Gravité',                  'sku'=>'860005339785',    'dimensions'=>['length'=>5.6,  'width'=>5.0,  'height'=>2.5],  'unit_weight_lbs'=>0.9313],
    ['id'=>3276357, 'title'=>'Particle Varros',                   'sku'=>'00860012469765',  'dimensions'=>['length'=>5.5,  'width'=>2.0,  'height'=>3.5],  'unit_weight_lbs'=>1.0],
    ['id'=>3008280, 'title'=>'Particle Hand Cream',               'sku'=>'00860014497216',  'dimensions'=>['length'=>6.0,  'width'=>2.3,  'height'=>2.3],  'unit_weight_lbs'=>0.4167],
    ['id'=>2475444, 'title'=>'Particle Gravité Deodorant',        'sku'=>'860012469710',    'dimensions'=>['length'=>6.2,  'width'=>2.0,  'height'=>2.0],  'unit_weight_lbs'=>0.176],
    ['id'=>1450671, 'title'=>'Particle Ab Firming Cream',         'sku'=>'860010338421',    'dimensions'=>['length'=>5.75, 'width'=>2.75, 'height'=>2.75], 'unit_weight_lbs'=>0.3563],
    ['id'=>1495139, 'title'=>'Particle Neck Cream',               'sku'=>'860005339778',    'dimensions'=>['length'=>6.1,  'width'=>2.62, 'height'=>2.62], 'unit_weight_lbs'=>0.2375],
    ['id'=>216919,  'title'=>'Particle Body Wash',                'sku'=>'636665869678',    'dimensions'=>['length'=>6.81, 'width'=>3.15, 'height'=>1.97], 'unit_weight_lbs'=>1.0375],
    ['id'=>1860895, 'title'=>'Particle Anti-Gray Serum',          'sku'=>'860012469703',    'dimensions'=>['length'=>5.3,  'width'=>1.4,  'height'=>1.4],  'unit_weight_lbs'=>0.2875],
    ['id'=>570671,  'title'=>'Particle Hair Revival Kit',         'sku'=>'860005339730',    'dimensions'=>['length'=>5.91, 'width'=>6.69, 'height'=>2.7],  'unit_weight_lbs'=>0.425],
    ['id'=>216928,  'title'=>'Particle Hair Thickening Shampoo',  'sku'=>'636665869661',    'dimensions'=>['length'=>6.81, 'width'=>3.15, 'height'=>1.97], 'unit_weight_lbs'=>1.0875],
    ['id'=>616215,  'title'=>'Particle Beard Oil',                'sku'=>'860005339723',    'dimensions'=>['length'=>4.13, 'width'=>2.48, 'height'=>2.48], 'unit_weight_lbs'=>0.2188],
    ['id'=>2293541, 'title'=>'Particle Infinite Male',            'sku'=>'860012469727',    'dimensions'=>['length'=>4.3,  'width'=>2.0,  'height'=>2.0],  'unit_weight_lbs'=>0.1819],
    ['id'=>1077388, 'title'=>'Particle Skin Vitamin Gummies',     'sku'=>'860005339747',    'dimensions'=>['length'=>4.6,  'width'=>2.4,  'height'=>2.4],  'unit_weight_lbs'=>0.2101],
    ['id'=>1068419, 'title'=>'Particle Hair Vitamin Gummies',     'sku'=>'860005339761',    'dimensions'=>['length'=>4.6,  'width'=>2.4,  'height'=>2.4],  'unit_weight_lbs'=>0.2101],
    ['id'=>3713630, 'title'=>'Particle Scalp Massager',           'sku'=>'9162027',         'dimensions'=>['length'=>3.0,  'width'=>3.5,  'height'=>3.0],  'unit_weight_lbs'=>0.1584],
    ['id'=>3713631, 'title'=>'Particle Comb',                     'sku'=>'70113000',        'dimensions'=>['length'=>0.1,  'width'=>7.2,  'height'=>1.5],  'unit_weight_lbs'=>1.0],
    ['id'=>3713632, 'title'=>'Particle Nose Trimmer',             'sku'=>'70114000',        'dimensions'=>['length'=>1.3,  'width'=>2.5,  'height'=>2.0],  'unit_weight_lbs'=>1.0],
    ['id'=>3713633, 'title'=>'Particle Gravité Tester 1.5ml',    'sku'=>'70117000',        'dimensions'=>['length'=>0.3,  'width'=>4.0,  'height'=>2.3],  'unit_weight_lbs'=>1.0],
    ['id'=>3713634, 'title'=>'Particle Shaving Cream Stand',      'sku'=>'00860012469758',  'dimensions'=>['length'=>1.5,  'width'=>8.0,  'height'=>4.0],  'unit_weight_lbs'=>1.0],
    // ── Bundles ──────────────────────────────────────────────────────────────
    ['id'=>2941634, 'title'=>'Particle Lady Killer Kit',          'sku'=>'77000011',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'860005339785','quantity'=>1],['sku'=>'860012469710','quantity'=>1],['sku'=>'636665869661','quantity'=>1]]],
    ['id'=>1813624, 'title'=>'Starter Bundle',                    'sku'=>'9162025',         'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'636665869647','quantity'=>1],['sku'=>'860005339778','quantity'=>1]]],
    ['id'=>250223,  'title'=>'Essential Bundle',                  'sku'=>'123456',          'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'636665869654','quantity'=>1],['sku'=>'636665869647','quantity'=>1]]],
    ['id'=>2769533, 'title'=>'Particle Gravité Bundle',           'sku'=>'2769533',         'components'=>[['sku'=>'860012469710','quantity'=>1],['sku'=>'860005339785','quantity'=>1]]],
    ['id'=>250209,  'title'=>'Advanced Bundle',                   'sku'=>'223456',          'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'636665869654','quantity'=>1],['sku'=>'636665869647','quantity'=>1],['sku'=>'636665869661','quantity'=>1],['sku'=>'636665869678','quantity'=>1]]],
    ['id'=>616306,  'title'=>'Power Shower Set',                  'sku'=>'9162021',         'components'=>[['sku'=>'636665869661','quantity'=>1],['sku'=>'636665869678','quantity'=>1]]],
    ['id'=>1607485, 'title'=>'Hair Growth Bundle',                'sku'=>'816202112',       'components'=>[['sku'=>'636665869661','quantity'=>1],['sku'=>'860005339730','quantity'=>1],['sku'=>'860005339761','quantity'=>1]]],
    ['id'=>2769100, 'title'=>"Particle Golfer's Bundle",          'sku'=>'2769100',         'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'860010338483','quantity'=>1]]],
    ['id'=>3279775, 'title'=>"Particle Father's Day Gift Bundle", 'sku'=>'77000013',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'636665869661','quantity'=>1],['sku'=>'00860012469772','quantity'=>1],['sku'=>'860005339785','quantity'=>1]]],
    ['id'=>3311073, 'title'=>'Bold Moves Bundle',                 'sku'=>'860014695551',    'components'=>[['sku'=>'860005339785','quantity'=>1],['sku'=>'00860012469765','quantity'=>1]]],
    ['id'=>3536797, 'title'=>"Men's Gift Bundle",                 'sku'=>'77000015',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'00860012469772','quantity'=>1],['sku'=>'860012469710','quantity'=>1]]],
    ['id'=>3575372, 'title'=>'Dark Spot Remover Set',             'sku'=>'77000017',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'00860014497216','quantity'=>1]]],
    ['id'=>3713629, 'title'=>'Head Turner Set',                   'sku'=>'77000013',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'860005339785','quantity'=>1]]],
    ['id'=>3575379, 'title'=>'The Smooth Skin Set',               'sku'=>'77000016',        'components'=>[['sku'=>'751889384926','quantity'=>1],['sku'=>'00860012469772','quantity'=>1]]],
];

// ─────────────────────────────────────────────────────────────────────────────
// 2.  Parse request
// ─────────────────────────────────────────────────────────────────────────────
$raw = file_get_contents('php://input');
$body = $raw ? json_decode($raw, true) : [];

if (!$body && isset($_GET['skus'])) {
    $body = ['skus' => explode(',', $_GET['skus'])];
}

if (empty($body['skus'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing "skus" parameter']);
    exit;
}

// Normalise input to [{sku, qty}]
$requestedLines = [];
foreach ($body['skus'] as $entry) {
    if (is_string($entry)) {
        $requestedLines[] = ['sku' => trim($entry), 'qty' => 1];
    } elseif (is_array($entry)) {
        $requestedLines[] = [
            'sku' => trim($entry['sku'] ?? ''),
            'qty' => (int)($entry['qty'] ?? $entry['quantity'] ?? 1),
        ];
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// 3.  Build product & bundle lookups
// ─────────────────────────────────────────────────────────────────────────────
$productBySku = [];
foreach ($PRODUCTS as $p) {
    $productBySku[$p['sku']] = $p;
}

/**
 * Expand one order line into flat [{product, qty}] pairs.
 * Bundles are exploded into their components (same logic as App.vue).
 */
function expandLine(array $line, array $productBySku): array {
    $sku = $line['sku'];
    $qty = $line['qty'];

    if (!isset($productBySku[$sku])) return [];

    $p = $productBySku[$sku];

    // Bundle: recurse into components
    if (!empty($p['components'])) {
        $result = [];
        foreach ($p['components'] as $comp) {
            $subLines = expandLine(
                ['sku' => $comp['sku'], 'qty' => ($comp['quantity'] ?? 1) * $qty],
                $productBySku
            );
            foreach ($subLines as $sl) {
                $result[] = $sl;
            }
        }
        return $result;
    }

    // Individual product — must have dimensions
    if (empty($p['dimensions'])) return [];

    return [['product' => $p, 'qty' => $qty]];
}

// Merge duplicates (same SKU from different bundles)
$mergedLines = [];
foreach ($requestedLines as $line) {
    foreach (expandLine($line, $productBySku) as $expanded) {
        $s = $expanded['product']['sku'];
        if (isset($mergedLines[$s])) {
            $mergedLines[$s]['qty'] += $expanded['qty'];
        } else {
            $mergedLines[$s] = $expanded;
        }
    }
}

// Expand quantities into individual item list
$items = [];
foreach ($mergedLines as $ml) {
    $p   = $ml['product'];
    $d   = $p['dimensions'];
    $qty = $ml['qty'];
    for ($i = 0; $i < $qty; $i++) {
        $items[] = [
            'name'   => $p['title'] . '__' . count($items),
            // JS packItems.ts maps: width=length, height=height, depth=width
            'width'  => (float)$d['length'],
            'height' => (float)$d['height'],
            'depth'  => (float)$d['width'],
            'weight' => (float)($p['unit_weight_lbs'] ?? 1),
        ];
    }
}

if (empty($items)) {
    http_response_code(400);
    echo json_encode(['error' => 'No products found for the given SKUs']);
    exit;
}

// ─────────────────────────────────────────────────────────────────────────────
// 4.  3D bin-packing (PHP port of binpackingjs/3d)
// ─────────────────────────────────────────────────────────────────────────────
const PADDING = 0.03;

// Rotation types (same enum values as binpackingjs)
const RT_WHD = 0;
const RT_HWD = 1;
const RT_HDW = 2;
const RT_DHW = 3;
const RT_DWH = 4;
const RT_WDH = 5;
const ALL_ROTATIONS = [RT_WHD, RT_HWD, RT_HDW, RT_DHW, RT_DWH, RT_WDH];

// Axis indices
const AX_W = 0; // Width
const AX_H = 1; // Height
const AX_D = 2; // Depth

function getDimension(float $w, float $h, float $d, int $rot): array {
    switch ($rot) {
        case RT_WHD: return [$w, $h, $d];
        case RT_HWD: return [$h, $w, $d];
        case RT_HDW: return [$h, $d, $w];
        case RT_DHW: return [$d, $h, $w];
        case RT_DWH: return [$d, $w, $h];
        case RT_WDH: return [$w, $d, $h];
    }
    return [$w, $h, $d];
}

function getDecimalPlaces(float $value): int {
    if (!is_finite($value)) return 0;
    $str = (string)$value;
    $dot = strpos($str, '.');
    if ($dot === false) return 0;
    $epos = strpos($str, 'E-');
    if ($epos === false) $epos = strpos($str, 'e-');
    if ($epos !== false) {
        $mantissa = strlen(substr($str, $dot + 1, $epos - $dot - 1));
        $exp = (int)substr($str, $epos + 2);
        return $mantissa + $exp;
    }
    return strlen($str) - $dot - 1;
}

function computeFactor(array $values): float {
    $max = 0;
    foreach ($values as $v) {
        $d = getDecimalPlaces((float)$v);
        if ($d > $max) $max = $d;
    }
    if ($max === 0) return 1;
    if ($max > 10) $max = 10;
    return pow(10, $max);
}

function fi(float $v, float $factor): int {
    return (int)round($v * $factor);
}

function rectIntersect(
    array $p1, array $d1,
    array $p2, array $d2,
    int $ax, int $ay
): bool {
    $cx1 = $p1[$ax] + $d1[$ax] / 2;
    $cy1 = $p1[$ay] + $d1[$ay] / 2;
    $cx2 = $p2[$ax] + $d2[$ax] / 2;
    $cy2 = $p2[$ay] + $d2[$ay] / 2;

    $ix = max($cx1, $cx2) - min($cx1, $cx2);
    $iy = max($cy1, $cy2) - min($cy1, $cy2);

    return $ix < ($d1[$ax] + $d2[$ax]) / 2
        && $iy < ($d1[$ay] + $d2[$ay]) / 2;
}

function itemsIntersect(array $p1, array $d1, array $p2, array $d2): bool {
    return rectIntersect($p1, $d1, $p2, $d2, AX_W, AX_H)
        && rectIntersect($p1, $d1, $p2, $d2, AX_H, AX_D)
        && rectIntersect($p1, $d1, $p2, $d2, AX_W, AX_D);
}

function scoreRotation(array $bin, int $iw, int $ih, int $id, int $rot): float {
    $d = getDimension($iw, $ih, $id, $rot);
    if ($bin['w'] < $d[0] || $bin['h'] < $d[1] || $bin['d'] < $d[2]) return 0.0;
    $we = floor($bin['w'] / $d[0]) * $d[0] / $bin['w'];
    $he = floor($bin['h'] / $d[1]) * $d[1] / $bin['h'];
    $de = floor($bin['d'] / $d[2]) * $d[2] / $bin['d'];
    return $we * $he * $de;
}

function getBestRotationOrder(array $bin, int $iw, int $ih, int $id, array $allowedRots): array {
    $scored = [];
    foreach ($allowedRots as $r) {
        $scored[] = ['rot' => $r, 'score' => scoreRotation($bin, $iw, $ih, $id, $r)];
    }
    usort($scored, fn($a, $b) => $b['score'] <=> $a['score']);
    return array_column($scored, 'rot');
}

/**
 * Try to place item in bin at given position.
 * On success, appends to $bin['items'] and returns the packed record.
 * Returns null if no valid placement found.
 */
function putItem(array &$bin, array $item, array $pos, array $allowedRots): ?array {
    $rots = getBestRotationOrder($bin, $item['w'], $item['h'], $item['d'], $allowedRots);

    foreach ($rots as $rot) {
        $d = getDimension($item['w'], $item['h'], $item['d'], $rot);

        if ($bin['w'] < $pos[0] + $d[0] ||
            $bin['h'] < $pos[1] + $d[1] ||
            $bin['d'] < $pos[2] + $d[2]) {
            continue;
        }

        $fits = true;
        foreach ($bin['items'] as $existing) {
            if (itemsIntersect($pos, $d, $existing['pos'], $existing['dim'])) {
                $fits = false;
                break;
            }
        }

        if ($fits) {
            $packed = [
                'name'   => $item['name'],
                'pos'    => $pos,
                'dim'    => $d,
                'rot'    => $rot,
                'w'      => $item['w'],
                'h'      => $item['h'],
                'd'      => $item['d'],
                'weight' => $item['weight'],
            ];
            $bin['items'][] = $packed;  // push to bin (mirrors JS MutableBin3D.putItem)
            return $packed;
        }
    }
    return null;
}

function weighItem(array $bin, float $weight): bool {
    if ($bin['maxWeight'] === 0) return false;
    $packed = array_sum(array_column($bin['items'] ?? [], 'weight'));
    return $packed + $weight <= $bin['maxWeight'];
}

/**
 * Pack items into bin. Returns array of unpacked items.
 */
function packToBin(array &$bins, int $binIdx, array $items): array {
    $b = &$bins[$binIdx];
    $firstItem = $items[0];

    if (!weighItem($b, $firstItem['weight'])) {
        // Try a bigger bin
        for ($i = 0; $i < count($bins); $i++) {
            if ($bins[$i]['vol'] > $b['vol']) {
                return packToBin($bins, $i, $items);
            }
        }
        return $items;
    }

    // putItem appends to $b['items'] on success — do NOT push again
    $packed = putItem($b, $firstItem, [0, 0, 0], ALL_ROTATIONS);
    if (!$packed) {
        for ($i = 0; $i < count($bins); $i++) {
            if ($bins[$i]['vol'] > $b['vol']) {
                return packToBin($bins, $i, $items);
            }
        }
        return $items;
    }

    $unpacked = [];
    for ($i = 1; $i < count($items); $i++) {
        $item   = $items[$i];
        $fitted = false;

        if (weighItem($b, $item['weight'])) {
            for ($pt = 0; $pt < 3; $pt++) {
                foreach ($b['items'] as $ib) {
                    switch ($pt) {
                        case AX_W: $pv = [$ib['pos'][0] + $ib['dim'][0], $ib['pos'][1], $ib['pos'][2]]; break;
                        case AX_H: $pv = [$ib['pos'][0], $ib['pos'][1] + $ib['dim'][1], $ib['pos'][2]]; break;
                        default:   $pv = [$ib['pos'][0], $ib['pos'][1], $ib['pos'][2] + $ib['dim'][2]]; break;
                    }
                    // putItem appends to $b['items'] on success — do NOT push again
                    if (putItem($b, $item, $pv, ALL_ROTATIONS)) {
                        $fitted = true;
                        break 2;
                    }
                }
            }
        }

        if (!$fitted) $unpacked[] = $item;
    }

    return $unpacked;
}

/**
 * Main pack3D function — identical logic to binpackingjs pack3D.
 * Returns ['packedBins' => [...], 'unfitItems' => [...]]
 */
function pack3D(array $rawBins, array $rawItems): array {
    // Collect all values for factor computation
    $allVals = [];
    foreach ($rawBins  as $b) array_push($allVals, $b['width'], $b['height'], $b['depth'], $b['maxWeight']);
    foreach ($rawItems as $i) array_push($allVals, $i['width'], $i['height'], $i['depth'], $i['weight']);
    $factor = computeFactor($allVals);

    // Normalize bins (to integers) and sort by volume ascending
    $bins = [];
    foreach ($rawBins as $b) {
        $nw = fi($b['width'],     $factor);
        $nh = fi($b['height'],    $factor);
        $nd = fi($b['depth'],     $factor);
        $nW = fi($b['maxWeight'], $factor);
        $bins[] = [
            'name'      => $b['name'],
            'w'         => $nw, 'h' => $nh, 'd' => $nd,
            'maxWeight' => $nW,
            'vol'       => $nw * $nh * $nd,
            'items'     => [],
        ];
    }
    usort($bins, fn($a, $b) => $a['vol'] <=> $b['vol']);

    // Normalize items and sort by volume descending
    $items = [];
    foreach ($rawItems as $it) {
        $nw = fi($it['width'],  $factor);
        $nh = fi($it['height'], $factor);
        $nd = fi($it['depth'],  $factor);
        $nW = fi($it['weight'], $factor);
        $items[] = [
            'name'   => $it['name'],
            'w'      => $nw, 'h' => $nh, 'd' => $nd,
            'weight' => $nW,
            'vol'    => $nw * $nh * $nd,
        ];
    }
    usort($items, fn($a, $b) => $b['vol'] <=> $a['vol']);

    $unfitItems = [];

    while (!empty($items)) {
        $first = $items[0];

        // findFittedBin: find first bin that can hold this item (test only, don't modify real bins)
        $fitBinIdx = null;
        foreach ($bins as $bi => $b) {
            if (!weighItem($b, $first['weight'])) continue;
            $testBin = $b;  // copy — putItem modifies $testBin, not $bins[$bi]
            if (putItem($testBin, $first, [0, 0, 0], ALL_ROTATIONS)) {
                $fitBinIdx = $bi;
                break;
            }
        }

        if ($fitBinIdx === null) {
            $unfitItems[] = array_shift($items);
            continue;
        }

        $items = packToBin($bins, $fitBinIdx, $items);
    }

    return ['bins' => $bins, 'unfitItems' => $unfitItems];
}

// ─────────────────────────────────────────────────────────────────────────────
// 5.  Try each box individually (smallest → largest), same as the JS app
// ─────────────────────────────────────────────────────────────────────────────

// SKUs that use the dedicated single-item box when ordered alone.
const SINGLE_BOX_SKUS = ['860005339785', '751889384926']; // Gravité, Face Cream

$totalItems = count($items);
$boxResult  = null;
$message    = '';

// single_shipping_box: exactly one unit of Gravité or Face Cream
// array_keys() casts numeric-looking strings to int — strval() restores them
$singleSkus = array_map('strval', array_keys($mergedLines));
$firstLine  = reset($mergedLines);  // first (and possibly only) merged line
if (
    $totalItems === 1 &&
    count($singleSkus) === 1 &&
    in_array($singleSkus[0], SINGLE_BOX_SKUS, true) &&
    $firstLine['qty'] === 1
) {
    $boxResult = 'single_shipping_box';
    $message   = "1 item fits in Single Shipping Box.";
}

if (!$boxResult) {
    foreach ($BOXES as $box) {
        $d   = $box['dimensions'];
        $bin = [[
            'name'      => $box['id'],
            // Same mapping as paddedBox() in packItems.ts.
            // round(..., 4) prevents float subtraction artifacts from inflating
            // the factor vs what JS computes.
        'width'     => round((float)$d['length'] + PADDING, 4),
        'height'    => round((float)$d['height'] + PADDING, 4),
        'depth'     => round((float)$d['width']  + PADDING, 4),
            'maxWeight' => 99999,
        ]];

        $result     = pack3D($bin, $items);
        $unfitCount = count($result['unfitItems']);

        if ($unfitCount === 0) {
            $id        = $box['id'];
            $boxResult = $id === 'small-shipper' ? 'single_branded_shipping_box' : 'regular_shipping_box';
            $label     = $id === 'small-shipper' ? 'Single Branded Shipping Box' : 'Regular Shipping Box';
            $message   = "All $totalItems item(s) fit in $label.";
            break;
        }
    }
}

if (!$boxResult) {
    $boxResult = 'bigger_shipping_box';
    $message   = "$totalItems item(s) do not fit in any available box.";
}
$fittedCount = ($boxResult !== 'bigger_shipping_box') ? $totalItems : 0;
$unfitCount  = $totalItems - $fittedCount;

echo json_encode([
    'result'        => $boxResult,
    'message'       => $message,
    'fitted_items'  => $fittedCount,
    'total_items'   => $totalItems,
    'unfit_items'   => $unfitCount,
], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
