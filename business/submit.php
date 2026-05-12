<?php
// Business Feature Form Handler for SiteGround
// Saves submissions and sends notification email

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'message' => 'Method not allowed']);
    exit;
}

// Get POST data
$data = json_decode(file_get_contents('php://input'), true);

if (!$data) {
    $data = $_POST;
}

// Validate required fields
$required = ['business_name', 'contact_name', 'email'];
foreach ($required as $field) {
    if (empty($data[$field])) {
        http_response_code(400);
        echo json_encode(['success' => false, 'message' => "Missing required field: $field"]);
        exit;
    }
}

// Sanitize inputs
$business_name = htmlspecialchars(trim($data['business_name']));
$contact_name = htmlspecialchars(trim($data['contact_name']));
$email = filter_var(trim($data['email']), FILTER_SANITIZE_EMAIL);
$phone = htmlspecialchars(trim($data['phone'] ?? ''));
$city_interest = htmlspecialchars(trim($data['city_interest'] ?? ''));
$message = htmlspecialchars(trim($data['message'] ?? ''));
$source_url = htmlspecialchars(trim($data['source_url'] ?? 'Unknown'));

// Validate email
if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'message' => 'Invalid email address']);
    exit;
}

// Prepare submission data
$submission = [
    'timestamp' => date('Y-m-d H:i:s'),
    'business_name' => $business_name,
    'contact_name' => $contact_name,
    'email' => $email,
    'phone' => $phone,
    'city_interest' => $city_interest,
    'message' => $message,
    'source_url' => $source_url,
    'ip_address' => $_SERVER['REMOTE_ADDR'] ?? 'Unknown'
];

// Save to file (as CSV for easy access)
$csv_file = __DIR__ . '/submissions.csv';
$csv_line = implode(',', [
    $submission['timestamp'],
    $submission['business_name'],
    $submission['contact_name'],
    $submission['email'],
    $submission['phone'],
    $submission['city_interest'],
    str_replace([",", "\n", "\r"], [";", " ", " "], $submission['message']),
    $submission['source_url']
]) . "\n";

// Create file with headers if doesn't exist
if (!file_exists($csv_file)) {
    $headers = "Timestamp,Business Name,Contact Name,Email,Phone,City,Message,Source URL\n";
    file_put_contents($csv_file, $headers);
}

// Append submission
file_put_contents($csv_file, $csv_line, FILE_APPEND | LOCK_EX);

// Send notification email (if configured)
$to = 'features@dfwasocialbuzz.com'; // Change this to your email
$subject = "New Business Feature Request: $business_name";
$email_body = "New business feature submission:\n\n";
$email_body .= "Business: $business_name\n";
$email_body .= "Contact: $contact_name\n";
$email_body .= "Email: $email\n";
$email_body .= "Phone: $phone\n";
$email_body .= "City: $city_interest\n";
$email_body .= "Message: $message\n";
$email_body .= "Source: $source_url\n";
$email_body .= "Time: {$submission['timestamp']}\n";

$headers_email = "From: noreply@dfwasocialbuzz.com\r\n";
$headers_email .= "Reply-To: $email\r\n";

// Try to send email (may not work on all hosts without proper SMTP config)
@mail($to, $subject, $email_body, $headers_email);

// Return success
http_response_code(200);
echo json_encode([
    'success' => true,
    'message' => 'Thank you! We will be in touch within 24 hours.',
    'data' => [
        'business_name' => $business_name,
        'email' => $email
    ]
]);
?>