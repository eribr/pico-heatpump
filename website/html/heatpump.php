<?php
session_start();

$config_path = '/home/erik/pico-heatpump/website/config.json';
$api_base_url = "";
$api_password = "";
$message = "";
$cache_path = __DIR__ . '/../cache/heatpump_state_cache.json';
$cache_ttl_seconds = 600;

$state = [
    'power' => 'on',
    'mode' => 'HEAT',
    'temp' => 22,
    'fan' => 'AUTO',
    'ifeel' => false,
];

function ensure_cache_dir($path) {
    $dir = dirname($path);
    if (!is_dir($dir)) {
        mkdir($dir, 0775, true);
    }
}

function read_state_cache($cache_path, $ttl_seconds) {
    if (!file_exists($cache_path)) {
        return null;
    }

    $age = time() - filemtime($cache_path);
    if ($age > $ttl_seconds) {
        return null;
    }

    $json = @file_get_contents($cache_path);
    if ($json === false) {
        return null;
    }

    $data = json_decode($json, true);
    if (!is_array($data)) {
        return null;
    }

    return $data;
}

function write_state_cache($cache_path, $state) {
    ensure_cache_dir($cache_path);
    $json = json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    if ($json === false) {
        return;
    }
    @file_put_contents($cache_path, $json);
}

function fetch_state_from_api($api_base_url, $api_password) {
    $url = $api_base_url . '/state';
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_USERPWD, ':' . $api_password);
    curl_setopt($ch, CURLOPT_HTTPGET, true);

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200 || $response === false) {
        return null;
    }

    $data = json_decode($response, true);
    if (!is_array($data) || !isset($data['state']) || !is_array($data['state'])) {
        return null;
    }

    return $data['state'];
}

function send_state_to_api($api_base_url, $api_password, $payload) {
    $url = $api_base_url . '/set';
    $json = json_encode($payload);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, 'POST');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    curl_setopt($ch, CURLOPT_USERPWD, ':' . $api_password);
    curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $json);

    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code !== 200 || $response === false) {
        return ['ok' => false, 'http_code' => $http_code, 'body' => $response];
    }

    $data = json_decode($response, true);
    return ['ok' => true, 'data' => $data];
}

// 1. Load settings from file
if (file_exists($config_path)) {
    $config_json = file_get_contents($config_path);
    $config_data = json_decode($config_json, true);

    if (isset($config_data['api_password'])) {
        $api_password = $config_data['api_password'];
    } else {
        die("Error: 'api_password' is missing in config.json.");
    }

    if (isset($config_data['api_base_url'])) {
        $api_base_url = rtrim($config_data['api_base_url'], '/');
    }
} else {
    die("Error: Config file not found at $config_path.");
}

// 2. Handle logout
if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: " . $_SERVER['PHP_SELF']);
    exit;
}

// 3. Handle login
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login_password'])) {
    if ($_POST['login_password'] === $api_password) {
        $_SESSION['authenticated'] = true;
    } else {
        $message = "<div class='error'>Error: Incorrect password!</div>";
    }
}

// 4. Show login page if not authenticated
if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true):
    ?>
    <!DOCTYPE html>
    <html lang="sv">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Inloggning - Nibe Control</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: #f4f4f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); width: 90%; max-width: 320px; text-align: center; }
            input[type="password"] { width: 100%; padding: 12px; margin: 15px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 16px; }
            .error { color: #e74c3c; margin-bottom: 10px; font-size: 0.9rem; font-weight: bold; }
            h1 { font-size: 1.4rem; color: #333; margin-top: 0; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h1>Nibe Heatpump</h1>
            <?php echo $message; ?>
            <form method="POST">
                <input type="password" name="login_password" placeholder="Password" autofocus>
                <button type="submit">Log in</button>
            </form>
        </div>
    </body>
    </html>
    <?php
    exit;
endif;

// 5. Load current state from local cache, falling back to API only occasionally
$cached_state = read_state_cache($cache_path, $cache_ttl_seconds);
if (is_array($cached_state)) {
    $state = $cached_state;
} else {
    $api_state = fetch_state_from_api($api_base_url, $api_password);
    if (is_array($api_state)) {
        $state = $api_state;
        write_state_cache($cache_path, $state);
    }
}

// 6. Handle SET request for the whole state object
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['set_state'])) {
    $payload = [];

    $payload['power'] = $_POST['power'] ?? null;
    $payload['mode'] = $_POST['mode'] ?? null;
    $payload['temp'] = $_POST['temp'] ?? null;
    $payload['fan'] = $_POST['fan'] ?? null;
    $payload['ifeel'] = isset($_POST['ifeel']) ? true : false;

    // Keep only explicitly provided values; for a checkbox false is still a real value.
    $payload = array_filter($payload, function ($value) {
        return $value !== null && $value !== '';
    }, ARRAY_FILTER_USE_BOTH);

    $result = send_state_to_api($api_base_url, $api_password, $payload);
    if ($result['ok']) {
        $new_state = $result['data']['state'] ?? $state;
        $state = $new_state;
        write_state_cache($cache_path, $state);
        $message = "<div class='success'>Settings updated successfully.</div>";
    } else {
        $message = "<div class='error'>API error: update failed.</div>";
    }
}
?>

<!DOCTYPE html>
<html lang="sv">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nibe Heatpump Control</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #f4f4f9; display: flex; justify-content: center; padding: 20px; margin: 0; }
        .card { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 420px; }
        h1 { font-size: 1.5rem; color: #333; text-align: center; margin-top: 0; }
        .section { margin-bottom: 22px; padding-bottom: 16px; border-bottom: 1px solid #eee; }
        .label { font-weight: bold; margin-bottom: 10px; display: block; color: #666; text-transform: uppercase; font-size: 0.8rem; }
        .field-row { display: flex; align-items: center; gap: 10px; }
        select, input[type="checkbox"] { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; font-size: 16px; }
        .checkbox-wrap { display: flex; align-items: center; gap: 10px; padding: 12px; border: 1px solid #ddd; border-radius: 8px; }
        .checkbox-wrap input[type="checkbox"] { width: auto; height: 18px; margin: 0; }
        .btn-set { width: 100%; padding: 14px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; background: #3498db; color: white; }
        .success { color: #27ae60; background: #eafaf1; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-weight: bold; }
        .error { color: #c0392b; background: #fdedec; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-weight: bold; }
        .logout-link { display: block; text-align: center; margin-top: 20px; color: #999; text-decoration: none; font-size: 0.9rem; }
        .small-note { font-size: 0.8rem; color: #777; margin-top: 8px; }
    </style>
</head>
<body>

<div class="card">
    <h1>Nibe Control</h1>

    <?php echo $message; ?>

    <form method="POST">
        <input type="hidden" name="set_state" value="1">

        <div class="section">
            <label class="label" for="power">Power</label>
            <select id="power" name="power">
                <option value="on" <?php echo ($state['power'] === 'on') ? 'selected' : ''; ?>>On</option>
                <option value="off" <?php echo ($state['power'] === 'off') ? 'selected' : ''; ?>>Off</option>
            </select>
        </div>

        <div class="section">
            <label class="label" for="mode">Mode</label>
            <select id="mode" name="mode">
                <option value="HEAT" <?php echo ($state['mode'] === 'HEAT') ? 'selected' : ''; ?>>HEAT</option>
                <option value="COOL" <?php echo ($state['mode'] === 'COOL') ? 'selected' : ''; ?>>COOL</option>
                <option value="FAN" <?php echo ($state['mode'] === 'FAN') ? 'selected' : ''; ?>>FAN</option>
            </select>
        </div>

        <div class="section">
            <label class="label" for="temp">Temperature</label>
            <select id="temp" name="temp">
                <?php for ($i = 15; $i <= 30; $i++): ?>
                    <option value="<?php echo $i; ?>" <?php echo ((int)$state['temp'] === $i) ? 'selected' : ''; ?>><?php echo $i; ?>°C</option>
                <?php endfor; ?>
            </select>
        </div>

        <div class="section">
            <label class="label" for="fan">Fan</label>
            <select id="fan" name="fan">
                <option value="AUTO" <?php echo ($state['fan'] === 'AUTO') ? 'selected' : ''; ?>>AUTO</option>
                <option value="1" <?php echo ($state['fan'] === '1') ? 'selected' : ''; ?>>1</option>
                <option value="2" <?php echo ($state['fan'] === '2') ? 'selected' : ''; ?>>2</option>
                <option value="3" <?php echo ($state['fan'] === '3') ? 'selected' : ''; ?>>3</option>
            </select>
        </div>

        <div class="section">
            <label class="label" for="ifeel">iFeel</label>
            <div class="checkbox-wrap">
                <input id="ifeel" type="checkbox" name="ifeel" value="1" <?php echo (!empty($state['ifeel'])) ? 'checked' : ''; ?>>
                <label for="ifeel">Enabled</label>
            </div>
        </div>

        <button type="submit" class="btn-set">Set</button>
        <div class="small-note">State is cached locally for 10 minutes to reduce slow API round-trips.</div>
    </form>

    <a href="?logout=1" class="logout-link">Log out from panel</a>
</div>

</body>
</html>
