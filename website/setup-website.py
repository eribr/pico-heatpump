#!/usr/bin/env python3
"""
Heatpump Website Setup - Python Version
Alternative setup script for cross-platform compatibility
"""

import os
import sys
import subprocess
import json
import getpass
import hashlib
from pathlib import Path

class WebsiteSetup:
    def __init__(self):
        self.domain = os.getenv('DOMAIN', 'my.hidden.backend.com')
        self.pico_host = os.getenv('PICO_HOST', 'localhost')
        self.pico_port = os.getenv('PICO_PORT', 80)
        self.pico_username = os.getenv('PICO_USERNAME', 'admin')
        self.pico_password = os.getenv('PICO_PASSWORD', 'password123')
        
        self.cert_dir = '/etc/ssl/heatpump'
        self.config_dir = '/etc/heatpump'
        self.web_root = '/var/www/heatpump'
        self.apache_config = '/etc/apache2/sites-available/heatpump.conf'
        self.htpasswd_file = '/etc/heatpump/.htpasswd'
        
        self.script_dir = Path(__file__).parent
        
        # Website credentials (to be set during setup)
        self.web_username = None
        self.web_password = None
    
    def get_web_credentials(self):
        """Prompt for website username and password"""
        print("\n🔐 Website Authentication")
        print("Set a username and password to protect the website\n")
        
        # Get username
        while True:
            username = input("Website username (default: admin): ").strip()
            if not username:
                username = "admin"
            if len(username) >= 3:
                break
            print("❌ Username must be at least 3 characters")
        
        # Get password
        while True:
            password = getpass.getpass("Website password: ")
            if not password:
                print("❌ Password cannot be empty")
                continue
            password_verify = getpass.getpass("Confirm password: ")
            if password == password_verify:
                break
            print("❌ Passwords do not match")
        
        self.web_username = username
        self.web_password = password
        print(f"✓ Credentials set: {username}")
    
    def create_htpasswd(self):
        """Create .htpasswd file with website credentials"""
        print("\n🔑 Creating authentication file...")
        
        # Use htpasswd command if available
        result = subprocess.run(
            f"htpasswd -bc {self.htpasswd_file} {self.web_username} {self.web_password}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            self.run_command(f'chown www-data:www-data {self.htpasswd_file}', 'Setting htpasswd permissions')
            self.run_command(f'chmod 640 {self.htpasswd_file}', 'Securing htpasswd file')
            print(f"✓ Authentication file created")
            return
        
        # Fallback: Create using Python if htpasswd not available
        print("⚠ htpasswd command not found, installing...")
        self.run_command('apt-get install -y -qq apache2-utils', 'Installing apache2-utils')
        
        result = subprocess.run(
            f"htpasswd -bc {self.htpasswd_file} {self.web_username} {self.web_password}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ Failed to create .htpasswd: {result.stderr}")
            sys.exit(1)
        
        self.run_command(f'chown www-data:www-data {self.htpasswd_file}', 'Setting htpasswd permissions')
        self.run_command(f'chmod 640 {self.htpasswd_file}', 'Securing htpasswd file')
        print(f"✓ Authentication file created")
    
    def run_command(self, cmd, description):
        """Run shell command"""
        print(f"⏳ {description}...")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Error: {result.stderr}")
            sys.exit(1)
        print(f"✓ {description}")
        return result.stdout
    
    def check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            print("❌ Error: This script must be run as root (use: sudo python3 setup-website.py)")
            sys.exit(1)
    
    def install_dependencies(self):
        """Install required packages"""
        print("\n📦 Installing dependencies...")
        self.run_command('apt-get update -qq', 'Updating package list')
        self.run_command('apt-get install -y -qq apache2 php libapache2-mod-php openssl curl apache2-utils',
                        'Installing packages')
    
    def enable_apache_modules(self):
        """Enable required Apache modules"""
        print("\n🔧 Enabling Apache modules...")
        for module in ['ssl', 'rewrite', 'headers']:
            self.run_command(f'a2enmod {module}', f'Enabling {module} module')
    
    def create_directories(self):
        """Create required directories"""
        print("\n📁 Creating directories...")
        for dirpath in [self.cert_dir, self.config_dir, self.web_root,
                       f'{self.web_root}/js', f'{self.web_root}/css']:
            Path(dirpath).mkdir(parents=True, exist_ok=True)
            print(f"✓ Created {dirpath}")
    
    def generate_certificate(self):
        """Generate self-signed SSL certificate"""
        print("\n🔐 Generating SSL certificate...")
        cert_path = f'{self.cert_dir}/cert.pem'
        key_path = f'{self.cert_dir}/key.pem'
        
        if Path(cert_path).exists() and Path(key_path).exists():
            print("✓ SSL certificate already exists")
            return
        
        cmd = (f"openssl req -x509 -newkey rsa:4096 -keyout {key_path} "
               f"-out {cert_path} -days 365 -nodes "
               f"-subj '/C=SE/ST=Sweden/L=Sweden/O=Heatpump/CN={self.domain}'")
        self.run_command(cmd, 'Creating SSL certificate')
        self.run_command(f'chmod 600 {key_path}', 'Setting certificate permissions')
    
    def create_config_file(self):
        """Create PHP configuration file"""
        print("\n⚙️  Creating configuration file...")
        config_content = f"""<?php
/**
 * Pico API Configuration
 * Stored outside web root for security
 */

// Pico Heat Pump API Configuration
define('PICO_API_HOST', getenv('PICO_HOST') ?: '{self.pico_host}');
define('PICO_API_PORT', getenv('PICO_PORT') ?: {self.pico_port});
define('PICO_API_USERNAME', getenv('PICO_USERNAME') ?: '{self.pico_username}');
define('PICO_API_PASSWORD', getenv('PICO_PASSWORD') ?: '{self.pico_password}');

// Construct full API URL
define('PICO_API_BASE', 'http://' . PICO_API_HOST . ':' . PICO_API_PORT . '/api');

// Logging
define('LOG_DIR', '/var/log/heatpump');
if (!is_dir(LOG_DIR)) {{
    mkdir(LOG_DIR, 0770, true);
}}

// Error reporting
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', LOG_DIR . '/php-error.log');

?>
"""
        config_file = f'{self.config_dir}/pico-api.conf.php'
        Path(config_file).write_text(config_content)
        os.chmod(config_file, 0o640)
        self.run_command(f'chown root:www-data {config_file}', 'Setting config permissions')
        print(f"✓ Configuration created at {config_file}")
    
    def setup_web_files(self):
        """Copy web files from HTML directory"""
        print("\n🌐 Setting up web files...")
        
        # Copy HTML files
        html_dir = self.script_dir / 'html'
        if (html_dir / 'index.html').exists():
            self.run_command(f'cp {html_dir}/index.html {self.web_root}/',
                           'Copying HTML files')
        
        # Copy CSS
        css_dir = html_dir / 'css'
        if css_dir.exists():
            self.run_command(f'cp -r {css_dir}/* {self.web_root}/css/ 2>/dev/null || true',
                           'Copying CSS files')
        
        # Copy JS
        js_dir = html_dir / 'js'
        if js_dir.exists():
            self.run_command(f'cp -r {js_dir}/* {self.web_root}/js/ 2>/dev/null || true',
                           'Copying JavaScript files')
    
    def create_php_bridge(self):
        """Create PHP API bridge"""
        print("\n🌉 Creating PHP API bridge...")
        # Read from existing heatpump-api.php in html directory if it exists
        html_dir = self.script_dir / 'html'
        php_file = html_dir / 'heatpump-api.php'
        
        if php_file.exists():
            content = php_file.read_text()
        else:
            # Use inline PHP content
            content = self._get_php_bridge_content()
        
        bridge_file = f'{self.web_root}/heatpump-api.php'
        Path(bridge_file).write_text(content)
        os.chmod(bridge_file, 0o755)
        self.run_command(f'chown www-data:www-data {bridge_file}', 'Setting bridge permissions')
        print(f"✓ PHP bridge created at {bridge_file}")
    
    def _get_php_bridge_content(self):
        """Get PHP bridge content"""
        return """<?php
/**
 * Heatpump API Bridge
 * Bridges requests from frontend to Pico heat pump API
 */

require_once '/etc/heatpump/pico-api.conf.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: https://' . $_SERVER['HTTP_HOST']);
header('Access-Control-Allow-Methods: GET, PUT, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path = str_replace('/heatpump-api.php', '', $path);

error_log("API Request: {$_SERVER['REQUEST_METHOD']} {$path}");

try {
    if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        handleGet($path);
    } elseif ($_SERVER['REQUEST_METHOD'] === 'PUT') {
        handlePut($path);
    } else {
        throw new Exception('Method not allowed', 405);
    }
} catch (Exception $e) {
    http_response_code($e->getCode() ?: 500);
    echo json_encode(['error' => $e->getMessage()]);
}

function handleGet($path) {
    $url = PICO_API_BASE . $path;
    $response = makeRequest('GET', $url);
    http_response_code(200);
    echo $response;
}

function handlePut($path) {
    $url = PICO_API_BASE . $path;
    $response = makeRequest('PUT', $url);
    http_response_code(200);
    echo $response;
}

function makeRequest($method, $url) {
    $ch = curl_init();
    
    $options = array(
        CURLOPT_URL => $url,
        CURLOPT_CUSTOMREQUEST => $method,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 10,
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_USERPWD => PICO_API_USERNAME . ':' . PICO_API_PASSWORD,
        CURLOPT_HTTPHEADER => array(
            'Content-Type: application/json',
            'Accept: application/json'
        )
    );
    
    curl_setopt_array($ch, $options);
    
    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    
    if (curl_errno($ch)) {
        throw new Exception('Connection failed: ' . curl_error($ch), 503);
    }
    
    curl_close($ch);
    
    if ($httpCode >= 400) {
        throw new Exception("API error (HTTP $httpCode)", $httpCode);
    }
    
    return $response ?: '{}';
}

?>
"""
    
    def create_apache_config(self):
        """Create Apache configuration"""
        print("\n🆎 Creating Apache configuration...")
        
        config_content = f"""<VirtualHost *:443>
    ServerName {self.domain}
    ServerAdmin admin@heatpump.local
    DocumentRoot {self.web_root}
    
    SSLEngine on
    SSLCertificateFile {self.cert_dir}/cert.pem
    SSLCertificateKeyFile {self.cert_dir}/key.pem
    SSLProtocol -all +TLSv1.2 +TLSv1.3
    SSLCipherSuite HIGH:!aNULL:!MD5
    
    Header always set X-Frame-Options "DENY"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains"
    
    <FilesMatch \.php$>
        SetHandler application/x-httpd-php
    </FilesMatch>
    
    <IfModule mod_rewrite.c>
        RewriteEngine On
        RewriteBase /
        RewriteRule ^heatpump/(.*)$ /heatpump-api.php?path=$1 [QSA,L]
    </IfModule>
    
    <Directory {self.web_root}>
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        
        # HTTP Basic Authentication
        AuthType Basic
        AuthName "Heatpump Control"
        AuthUserFile {self.htpasswd_file}
        Require valid-user
    </Directory>
    
    ErrorLog /var/log/apache2/heatpump-error.log
    CustomLog /var/log/apache2/heatpump-access.log combined
    LogLevel warn
</VirtualHost>

<VirtualHost *:80>
    ServerName {self.domain}
    Redirect permanent / https://{self.domain}/
</VirtualHost>
"""
        
        config_file = Path(self.apache_config)
        config_file.write_text(config_content)
        print(f"✓ Apache config created at {self.apache_config}")
        
        # Enable site
        self.run_command('a2ensite heatpump.conf', 'Enabling heatpump site')
    
    def configure_apache(self):
        """Test and restart Apache"""
        print("\n🚀 Configuring Apache...")
        
        # Test configuration
        result = subprocess.run('apache2ctl configtest', shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Invalid Apache configuration: {result.stderr}")
            sys.exit(1)
        
        print("✓ Apache configuration valid")
        
        # Restart Apache
        self.run_command('systemctl restart apache2', 'Restarting Apache')
    
    def setup(self):
        """Run complete setup"""
        print("\n" + "="*60)
        print("  Heatpump Website Setup")
        print("="*60)
        
        self.check_root()
        self.install_dependencies()
        self.enable_apache_modules()
        self.create_directories()
        self.get_web_credentials()
        self.generate_certificate()
        self.create_config_file()
        self.create_htpasswd()
        self.setup_web_files()
        self.create_php_bridge()
        self.create_apache_config()
        self.configure_apache()
        
        self._print_summary()
    
    def _print_summary(self):
        """Print setup summary"""
        print("\n" + "="*60)
        print("✓ Setup Complete!")
        print("="*60)
        print(f"\nWebsite URL: https://{self.domain}/")
        print(f"\n🔐 Authentication:")
        print(f"  Username: {self.web_username}")
        print(f"  Password: {'*' * len(self.web_password)}")
        print(f"  .htpasswd: {self.htpasswd_file}")
        print(f"\nConfiguration Files:")
        print(f"  Pico API: {self.config_dir}/pico-api.conf.php")
        print(f"  Apache: {self.apache_config}")
        print(f"  SSL Certs: {self.cert_dir}/")
        print(f"\nPico API Configuration:")
        print(f"  Host: {self.pico_host}")
        print(f"  Port: {self.pico_port}")
        print(f"  Username: {self.pico_username}")
        print(f"\nLogs:")
        print(f"  Apache: /var/log/apache2/heatpump-*.log")
        print(f"  PHP: /var/log/heatpump/php-error.log")

if __name__ == '__main__':
    setup = WebsiteSetup()
    setup.setup()
