<?php
$config_path = '/home/erik/pico-heatpump/website/config.json';

$api_base_url = "";
$api_password = "";
$message = "";

// Läs in config
if (file_exists($config_path)) {
    $config_content = file_get_contents($config_path);
    $config_data = json_decode($config_content, true);
    
    if (isset($config_data['api_password'])) {
        $api_password = $config_data['api_password'];
    }
    if (isset($config_data['api_base_url'])) {
        $api_base_url = $config_data['api_base_url'];
    }
} else {
    $message = "<div class='error'>System error: Config file not found.</div>";
}

// Hantera knapptryckningar (samma logik som tidigare)
if ($_SERVER['REQUEST_METHOD'] === 'POST' && !empty($api_password)) {
    $endpoint = $_POST['endpoint'] ?? '';
    $value = $_POST['value'] ?? '';
    
    if ($endpoint && $value) {
        $url = "$api_base_url/$endpoint/$value";
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "PUT");
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_USERPWD, ":" . $api_password);
        
        $response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($http_code === 200) {
            $message = "<div class='success'>Command sent: $endpoint -> $value</div>";
        } else {
            $message = "<div class='error'>API Error ($http_code): Command failed.</div>";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nibe Heatpump Control</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f9; display: flex; justify-content: center; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
        h1 { font-size: 1.5rem; color: #333; text-align: center; }
        .section { margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        .label { font-weight: bold; margin-bottom: 10px; display: block; color: #666; }
        .btn-group { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
        button { padding: 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; transition: opacity 0.2s; }
        .btn-on { background: #2ecc71; color: white; }
        .btn-off { background: #e74c3c; color: white; }
        .btn-temp { background: #3498db; color: white; }
        .btn-fan { background: #f39c12; color: white; grid-column: span 2; }
        button:hover { opacity: 0.8; }
        .success { color: #27ae60; background: #eafaf1; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px; }
        .error { color: #c0392b; background: #fdedec; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 10px; }
        select { width: 100%; padding: 10px; margin-bottom: 10px; border-radius: 6px; border: 1px solid #ccc; }
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
            <form method="POST"><input type="hidden" name="endpoint" value="power"><input type="hidden" name="value" value="on"><button type="submit" class="btn-on">ON</button></form>
            <form method="POST"><input type="hidden" name="endpoint" value="power"><input type="hidden" name="value" value="off"><button type="submit" class="btn-off">OFF</button></form>
        </div>
    </div>

    <!-- TEMPERATURE -->
    <div class="section">
        <span class="label">Set Temperature</span>
        <form method="POST" style="display: flex; gap: 10px;">
            <input type="hidden" name="endpoint" value="temp">
            <select name="value">
                <?php for($i=15; $i<=30; $i++): ?>
                    <option value="<?php echo $i; ?>" <?php echo ($i==21) ? 'selected' : ''; ?>><?php echo $i; ?>°C</option>
                <?php endfor; ?>
            </select>
            <button type="submit" class="btn-temp" style="flex-shrink: 0;">Update</button>
        </form>
    </div>

    <!-- FAN -->
    <div class="section">
        <span class="label">Fan Speed</span>
        <div class="btn-group">
            <form method="POST" style="width: 100%; grid-column: span 2;">
                <input type="hidden" name="endpoint" value="fan">
                <input type="hidden" name="value" value="auto">
                <button type="submit" class="btn-fan">Set Fan AUTO</button>
            </form>
        </div>
    </div>
</div>

</body>
</html>
