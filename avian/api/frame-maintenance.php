<?php
// A fresh, domain-separated proof of this Pi's current WLAN address.
declare(strict_types=1);
require_once __DIR__ . '/admin-auth.php';
header('Cache-Control: no-store');
header('Content-Type: application/json');
if (!avian_is_direct_local_request($_SERVER)) avian_api_fail(403, 'local access required');
$nonce = $_GET['nonce'] ?? '';
if (!is_string($nonce) || !preg_match('/\A[a-f0-9]{32}\z/', $nonce)) avian_api_fail(400, 'invalid nonce');
$lines = [];
exec('/usr/sbin/ip -4 -o addr show dev wlan0 scope global', $lines, $status);
if ($status !== 0 || !preg_match_all('/\binet ([0-9.]+)\//', implode('\n', $lines), $m)) avian_api_fail(503, 'WLAN unavailable');
$destination = (string)($_SERVER['SERVER_ADDR'] ?? '');
$address = in_array($destination, $m[1], true) ? $destination : $m[1][0];
if (!avian_private_address($address)) avian_api_fail(503, 'invalid WLAN address');
$key = @file_get_contents('/etc/avian-frame-maintenance/signing.pem');
$payload = "avian-frame-maintenance-v1\n$nonce\n$address";
if (!$key || !openssl_sign($payload, $signature, $key, OPENSSL_ALGO_SHA256)) avian_api_fail(503, 'proof unavailable');
echo json_encode(['address' => $address, 'nonce' => $nonce, 'signature' => base64_encode($signature)]);
