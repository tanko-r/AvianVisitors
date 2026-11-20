<?php
declare(strict_types=1);
require_once __DIR__ . '/admin-auth.php';
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
// Also permit direct tailnet access. This is deliberately scoped to the
// purchased reference player, not a change to admin or microphone gates.
function reference_tailnet_request(array $server): bool {
    $remote = (string)($server['REMOTE_ADDR'] ?? '');
    $host = preg_replace('/:\d+$/', '', (string)($server['HTTP_HOST'] ?? ''));
    foreach ([$remote, $host] as $address) {
        $ip = @inet_pton($address);
        if ($ip === false || strlen($ip) !== 4 || ord($ip[0]) !== 100 || ord($ip[1]) < 64 || ord($ip[1]) > 127) return false;
    }
    // FastCGI supplies these fields itself; reject extra/spoofed proxy fields.
    if (array_key_exists('AVIAN_DIRECT_LOCAL', $server)) {
        $scheme = !empty($server['HTTPS']) && $server['HTTPS'] !== 'off' ? 'https' : 'http';
        if (($server['HTTP_X_FORWARDED_FOR'] ?? '') !== $remote
            || ($server['HTTP_X_FORWARDED_HOST'] ?? '') !== ($server['HTTP_HOST'] ?? '')
            || ($server['HTTP_X_FORWARDED_PROTO'] ?? '') !== $scheme) return false;
        unset($server['HTTP_X_FORWARDED_FOR'], $server['HTTP_X_FORWARDED_HOST'], $server['HTTP_X_FORWARDED_PROTO']);
    }
    return !avian_has_forwarding_headers($server);
}
if (!avian_is_direct_local_request($_SERVER) && !reference_tailnet_request($_SERVER)) avian_api_fail(403, 'home-network or direct Tailscale access required');
if (!in_array($_SERVER['REQUEST_METHOD'] ?? '', ['GET', 'HEAD'], true)) avian_api_fail(405, 'GET required');
$name = $_GET['name'] ?? '';
if (!is_string($name) || strlen($name) > 200) avian_api_fail(400, 'invalid species');
$key = preg_replace('/[^a-z0-9]/', '', strtolower($name));
$root = '/var/lib/avian-visitors/typical-birdsong';
$index = json_decode(@file_get_contents($root . '/index.json') ?: '{}', true);
$kind = $_GET['type'] ?? 'song';
if (!is_string($kind) || !in_array($kind, ['song', 'call'], true)) avian_api_fail(400, 'invalid sound type');
$tracks = $index[$key] ?? [];
if (($_GET['play'] ?? '') !== '1') {
    header('Content-Type: application/json');
    $out = [];
    foreach (['song', 'call'] as $type) {
        $out[$type] = isset($tracks[$type]) ? ['available' => true, 'description' => $tracks[$type]['description'], 'source' => $tracks[$type]['source']] : ['available' => false];
    }
    echo json_encode(['examples' => $out]); exit;
}
$track = $tracks[$kind] ?? null;
if (!$track || !preg_match('/\A[a-f0-9]{24}\.mp3\z/', $track['file'] ?? '')) avian_api_fail(404, 'no example available');
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
