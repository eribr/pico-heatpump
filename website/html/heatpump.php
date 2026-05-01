<?php
session_start();

$config_path = '/home/erik/pico-heatpump/website/config.json';

$api_base_url = "";
$api_password = "";
$message = "";

// 1. Ladda inställningar från fil
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

// 2. Hantera Utloggning
if (isset($_GET['logout'])) {
    session_destroy();
    header("Location: " . $_SERVER['PHP_SELF']);
    exit;
}

// 3. Hantera Inloggning
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['login_password'])) {
    if ($_POST['login_password'] === $api_password) {
        $_SESSION['authenticated'] = true;
    } else {
        $message = "<div class='error'>Error: Incorrect password!</div>";
    }
}

// 4. Visa inloggningssida om inte inloggad
if (!isset($_SESSION['authenticated']) || $_SESSION['authenticated'] !== true): ?>
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

/**
 * 5. API-logik (Körs endast om inloggad)
 */
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['endpoint'])) {
    $endpoint = $_POST['endpoint'];
    $value = $_POST['value'];
    
    $url = "$api_base_url/$endpoint/$value";
    
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PUT");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);

    curl_setopt($ch, CURLOPT_USERPWD, ":" . $api_password);
    
    $response = curl_exec($ch);
    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($http_code === 200) {
        $message = "<div class='success'>Command sent: " . ucfirst($endpoint) . " set to $value</div>";
    } else {
        $message = "<div class='error'>API Fel ($http_code): Kunde inte nå värmepumpen.</div>";
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
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h1 { font-size: 1.5rem; color: #333; text-align: center; margin-top: 0; }
        .section { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        .label { font-weight: bold; margin-bottom: 10px; display: block; color: #666; text-transform: uppercase; font-size: 0.8rem; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { padding: 14px; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; font-size: 16px; transition: opacity 0.2s; }
        .btn-on { background: #2ecc71; color: white; }
        .btn-off { background: #e74c3c; color: white; }
        .btn-temp { background: #3498db; color: white; }
        .btn-fan { background: #f39c12; color: white; grid-column: span 2; }
        button:hover { opacity: 0.8; }
        .success { color: #27ae60; background: #eafaf1; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-weight: bold; }
        .error { color: #c0392b; background: #fdedec; padding: 12px; border-radius: 8px; text-align: center; margin-bottom: 15px; font-weight: bold; }
        select { width: 100%; padding: 12px; border-radius: 8px; border: 1px solid #ddd; font-size: 16px; appearance: none; background: #fff; }
        .logout-link { display: block; text-align: center; margin-top: 20px; color: #999; text-decoration: none; font-size: 0.9rem; }
    </style>
</head>
<body>

<div class="card">
    <h1>Nibe Control</h1>
    
    <?php echo $message; ?>

    <!-- POWER -->
    <div class="section">
        <span class="label">Power</span>
        <div class="btn-group">
            <form method="POST"><input type="hidden" name="endpoint" value="power"><input type="hidden" name="value" value="on"><button type="submit" class="btn-on">Start</button></form>
            <form method="POST"><input type="hidden" name="endpoint" value="power"><input type="hidden" name="value" value="off"><button type="submit" class="btn-off">Stop</button></form>
        </div>
    </div>

    <!-- TEMPERATURE -->
    <div class="section">
        <span class="label">Target Temperature</span>
        <form method="POST" style="display: flex; gap: 10px;">
            <input type="hidden" name="endpoint" value="temp">
            <select name="value">
                <?php for($i=15; $i<=30; $i++): ?>
                    <option value="<?php echo $i; ?>" <?php echo ($i==22) ? 'selected' : ''; ?>><?php echo $i; ?>°C</option>
                <?php endfor; ?>
            </select>
            <button type="submit" class="btn-temp">Set</button>
        </form>
    </div>

    <!-- FAN -->
    <div class="section">
        <span class="label">Fan Speed</span>
        <div class="btn-group">
            <form method="POST" style="width: 100%; grid-column: span 2;">
                <input type="hidden" name="endpoint" value="fan">
                <input type="hidden" name="value" value="auto">
                <button type="submit" class="btn-fan">Activate AUTO Fan</button>
            </form>
        </div>
    </div>

    <a href="?logout=1" class="logout-link">Log out from panel</a>
</div>

</body>
</html>