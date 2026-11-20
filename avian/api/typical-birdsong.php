<?php
declare(strict_types=1);
require_once __DIR__ . '/admin-auth.php';
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
if (!avian_is_direct_local_request($_SERVER)) avian_api_fail(403, 'home-network access required');
if (!in_array($_SERVER['REQUEST_METHOD'] ?? '', ['GET', 'HEAD'], true)) avian_api_fail(405, 'GET required');
$name = $_GET['name'] ?? '';
if (!is_string($name) || strlen($name) > 200) avian_api_fail(400, 'invalid species');
$key = preg_replace('/[^a-z0-9]/', '', strtolower($name));
$root = '/var/lib/avian-visitors/typical-birdsong';
$index = json_decode(@file_get_contents($root . '/index.json') ?: '{}', true);
$track = $index[$key] ?? null;
if (!$track || !preg_match('/\A[a-f0-9]{24}\.mp3\z/', $track['file'] ?? '')) avian_api_fail(404, 'no example available');
if (($_GET['play'] ?? '') !== '1') {
    header('Content-Type: application/json');
    echo json_encode(['available' => true, 'description' => $track['description'], 'source' => $track['source']]);
    exit;
}
$path = $root . '/' . $track['file'];
if (!is_file($path) || is_link($path)) avian_api_fail(404, 'no example available');
$size = filesize($path);
$start = 0; $end = $size - 1;
if (isset($_SERVER['HTTP_RANGE'])) {
    if (!preg_match('/\Abytes=(\d*)-(\d*)\z/', $_SERVER['HTTP_RANGE'], $m) || ($m[1] === '' && $m[2] === '')) {
        header("Content-Range: bytes */$size"); http_response_code(416); exit;
    }
    if ($m[1] === '') $start = max(0, $size - (int)$m[2]);
    else { $start = (int)$m[1]; if ($m[2] !== '') $end = min($end, (int)$m[2]); }
    if ($start > $end || $start >= $size) { header("Content-Range: bytes */$size"); http_response_code(416); exit; }
    http_response_code(206);
    header("Content-Range: bytes $start-$end/$size");
}
header('Content-Type: audio/mpeg');
header('Cache-Control: private, max-age=3600');
header('Accept-Ranges: bytes');
header('Content-Length: ' . ($end - $start + 1));
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'HEAD') exit;
$file = fopen($path, 'rb'); fseek($file, $start);
$left = $end - $start + 1;
while ($left > 0 && !feof($file)) { $chunk = fread($file, min(65536, $left)); echo $chunk; $left -= strlen($chunk); }
fclose($file);
