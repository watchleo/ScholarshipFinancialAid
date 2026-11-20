<?php
declare(strict_types=1);

// Run from the project directory: php -S 127.0.0.1:8080 php-api/index.php
header('Content-Type: application/json; charset=utf-8');

function fail(int $status, string $code, string $message): void
{
    http_response_code($status);
    echo json_encode(['error' => ['code' => $code, 'message' => $message]]);
    exit;
}

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];
$summary = $path === '/api/application-status-counts';
$lists = ['/api/students', '/api/terms', '/api/financial-aids', '/api/evaluators'];
$isResource = preg_match('~^/api/(scholarships|applications)(/[a-zA-Z0-9_-]+)?$~D', $path);
if (!$summary && !$isResource && !in_array($path, $lists, true)) {
    fail(404, 'not_found', 'Unknown PHP API endpoint.');
}

$methods = $path === '/api/applications' ? ['GET', 'POST'] : ['GET'];
if (!in_array($method, $methods, true)) {
    header('Allow: ' . implode(', ', $methods));
    fail(405, 'method_not_allowed', 'This endpoint supports ' . implode(' and ', $methods) . '.');
}

// Send the caller's key to FastAPI, which authenticates access to the shared data.
$headers = ['Accept: application/json', 'Connection: close'];
if (isset($_SERVER['HTTP_X_API_KEY'])) {
    $headers[] = 'X-API-Key: ' . $_SERVER['HTTP_X_API_KEY'];
}
$options = [
    'method' => $method,
    'ignore_errors' => true,    // Return the original validation and authentication errors.
    'follow_location' => 0,
    'timeout' => 5,
];
if ($method === 'POST') {
    $headers[] = 'Content-Type: ' . ($_SERVER['CONTENT_TYPE'] ?? 'application/octet-stream');
    $options['content'] = file_get_contents('php://input');
}
$options['header'] = $headers;

$baseUrl = getenv('FASTAPI_BASE_URL') ?: 'http://127.0.0.1:5000';
$upstream = rtrim($baseUrl, '/') . ($summary ? '/api/applications' : $path);
$query = $_SERVER['QUERY_STRING'] ?? '';
if ($query !== '') {
    $upstream .= '?' . $query;
}
$stream = @fopen($upstream, 'rb', false, stream_context_create(['http' => $options]));
if ($stream === false) {
    fail(502, 'upstream_unavailable', 'Cannot reach FastAPI. Check FASTAPI_BASE_URL and start the Python server.');
}
$body = stream_get_contents($stream);
$metadata = stream_get_meta_data($stream);
fclose($stream);
$statusLine = $metadata['wrapper_data'][0] ?? '';
if ($body === false || $metadata['timed_out'] || !preg_match('~^HTTP/\S+ (\d{3})\b~', $statusLine, $match)) {
    fail(502, 'upstream_unavailable', 'FastAPI returned an incomplete response.');
}

$status = (int) $match[1];
foreach ($metadata['wrapper_data'] as $responseHeader) {
    if (stripos($responseHeader, 'WWW-Authenticate:') === 0) {
        header($responseHeader);
    }
}
http_response_code($status);
if (!$summary || $status !== 200) {
    echo $body;
    exit;
}

// This report is calculated by PHP using live application records.
$applications = json_decode($body, true)['data'] ?? null;
if (!is_array($applications)) {
    fail(502, 'invalid_response', 'FastAPI did not return a list of applications.');
}
$counts = ['Pending' => 0, 'Approved' => 0, 'Rejected' => 0];
foreach ($applications as $application) {
    $status = $application['Status'] ?? '';
    if (!array_key_exists($status, $counts)) {
        fail(502, 'invalid_response', 'FastAPI returned an unknown application status.');
    }
    $counts[$status]++;
}
echo json_encode(['total' => count($applications), 'by_status' => $counts]);
