# Standard library imports (with fallbacks)
try:
    import socket
except ImportError:
    try:
        import usocket as socket
    except ImportError:
        socket = None

# MicroPython-specific imports
try:
    import ujson
    import ubinascii
    MICROPYTHON = True
except ImportError:
    import json as ujson  # Fallback to standard json
    import base64 as ubinascii  # Fallback to standard base64
    MICROPYTHON = False

from models.nibe import NibeHeatpumpIR, POWER_ON, POWER_OFF, MODE_AUTO, MODE_HEAT, MODE_COOL, MODE_DRY, MODE_FAN
from models.nibe import FAN_AUTO, FAN_4, FAN_3, FAN_2, FAN_SILENT
from models.nibe import VDIR_AUTO, VDIR_SWING, VDIR_UP, VDIR_MUP, VDIR_MIDDLE, VDIR_MDOWN, VDIR_DOWN

def parse_http_request(request):
    """Parse HTTP request and extract method, path, headers, and body"""
    lines = request.split('\r\n')
    if not lines:
        return None, None, {}, None

    # Parse request line
    request_line = lines[0].split()
    if len(request_line) < 2:
        return None, None, {}, None

    method = request_line[0]
    path = request_line[1]

    # Parse headers
    headers = {}
    i = 1
    while i < len(lines) and lines[i]:
        if ':' in lines[i]:
            key, value = lines[i].split(':', 1)
            headers[key.strip().lower()] = value.strip()
        i += 1

    # Get body (everything after empty line)
    body = None
    if i < len(lines) - 1:
        body = '\r\n'.join(lines[i+1:])

    return method, path, headers, body

def check_auth(headers, username, password):
    """Check HTTP Basic Authentication"""
    if 'authorization' not in headers:
        return False

    auth_header = headers['authorization']
    if not auth_header.startswith('Basic '):
        return False

    try:
        # Decode base64 credentials
        credentials = ubinascii.a2b_base64(auth_header[6:]).decode('utf-8')
        auth_username, auth_password = credentials.split(':', 1)
        return auth_username == username and auth_password == password
    except:
        return False

def send_json_response(sock, status_code, status_text, data):
    """Send JSON response"""
    response = ujson.dumps(data)
    sock.send(b'HTTP/1.1 ' + str(status_code).encode() + b' ' + status_text.encode() + b'\r\n')
    sock.send(b'Content-Type: application/json\r\n')
    sock.send(b'Content-Length: ' + str(len(response)).encode() + b'\r\n')
    sock.send(b'Access-Control-Allow-Origin: *\r\n')
    sock.send(b'Access-Control-Allow-Methods: GET, PUT, OPTIONS\r\n')
    sock.send(b'Access-Control-Allow-Headers: Authorization, Content-Type\r\n')
    sock.send(b'\r\n')
    sock.send(response.encode())

def send_error_response(sock, status_code, status_text, message):
    """Send error response"""
    send_json_response(sock, status_code, status_text, {'error': message})

def handle_request(sock, request, ir_driver, nibe_ir, config):
    """Handle HTTP request"""
    method, path, headers, body = parse_http_request(request)

    if method is None:
        send_error_response(sock, 400, 'Bad Request', 'Invalid request')
        return

    # Handle CORS preflight requests
    if method == 'OPTIONS':
        sock.send(b'HTTP/1.1 200 OK\r\n')
        sock.send(b'Access-Control-Allow-Origin: *\r\n')
        sock.send(b'Access-Control-Allow-Methods: GET, PUT, OPTIONS\r\n')
        sock.send(b'Access-Control-Allow-Headers: Authorization, Content-Type\r\n')
        sock.send(b'\r\n')
        return

    # Check authentication for non-GET requests
    if method != 'GET':
        if not check_auth(headers, config['auth']['username'], config['auth']['password']):
            sock.send(b'HTTP/1.1 401 Unauthorized\r\n')
            sock.send(b'WWW-Authenticate: Basic realm="Heat Pump Control"\r\n')
            sock.send(b'Content-Type: application/json\r\n')
            sock.send(b'\r\n')
            sock.send(b'{"error": "Authentication required"}')
            return

    # Route requests
    if path == '/api/status':
        if method == 'GET':
            send_json_response(sock, 200, 'OK', {
                'status': 'online',
                'model': 'Nibe Heat Pump',
                'server': 'Pico Heat Pump Controller'
            })
        else:
            send_error_response(sock, 405, 'Method Not Allowed', 'Method not allowed for this endpoint')

    elif path.startswith('/api/power/'):
        if method != 'PUT':
            send_error_response(sock, 405, 'Method Not Allowed', 'Use PUT method')
            return

        action = path.split('/')[-1]
        if action == 'on':
            nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, FAN_AUTO, 21, VDIR_AUTO, VDIR_AUTO)
            send_json_response(sock, 200, 'OK', {'power': 'on', 'message': 'Heat pump turned on'})
        elif action == 'off':
            nibe_ir.send(ir_driver, POWER_OFF, MODE_HEAT, FAN_AUTO, 21, VDIR_AUTO, VDIR_AUTO)
            send_json_response(sock, 200, 'OK', {'power': 'off', 'message': 'Heat pump turned off'})
        else:
            send_error_response(sock, 400, 'Bad Request', 'Invalid power action')

    elif path.startswith('/api/mode/'):
        if method != 'PUT':
            send_error_response(sock, 405, 'Method Not Allowed', 'Use PUT method')
            return

        mode_str = path.split('/')[-1].upper()
        mode_map = {
            'AUTO': MODE_AUTO,
            'HEAT': MODE_HEAT,
            'COOL': MODE_COOL,
            'DRY': MODE_DRY,
            'FAN': MODE_FAN
        }

        if mode_str in mode_map:
            nibe_ir.send(ir_driver, POWER_ON, mode_map[mode_str], FAN_AUTO, 21, VDIR_AUTO, VDIR_AUTO)
            send_json_response(sock, 200, 'OK', {'mode': mode_str.lower(), 'message': f'Mode set to {mode_str.lower()}'})
        else:
            send_error_response(sock, 400, 'Bad Request', 'Invalid mode')

    elif path.startswith('/api/fan/'):
        if method != 'PUT':
            send_error_response(sock, 405, 'Method Not Allowed', 'Use PUT method')
            return

        fan_str = path.split('/')[-1].upper()
        fan_map = {
            'AUTO': FAN_AUTO,
            '4': FAN_4,
            '3': FAN_3,
            '2': FAN_2,
            'SILENT': FAN_SILENT
        }

        if fan_str in fan_map:
            nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, fan_map[fan_str], 21, VDIR_AUTO, VDIR_AUTO)
            send_json_response(sock, 200, 'OK', {'fan': fan_str.lower(), 'message': f'Fan speed set to {fan_str.lower()}'})
        else:
            send_error_response(sock, 400, 'Bad Request', 'Invalid fan speed')

    elif path.startswith('/api/temp/'):
        if method != 'PUT':
            send_error_response(sock, 405, 'Method Not Allowed', 'Use PUT method')
            return

        try:
            temp = int(path.split('/')[-1])
            if 10 <= temp <= 32:
                nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, FAN_AUTO, temp, VDIR_AUTO, VDIR_AUTO)
                send_json_response(sock, 200, 'OK', {'temperature': temp, 'message': f'Temperature set to {temp}°C'})
            else:
                send_error_response(sock, 400, 'Bad Request', 'Temperature must be between 10-32°C')
        except ValueError:
            send_error_response(sock, 400, 'Bad Request', 'Invalid temperature')

    elif path.startswith('/api/swing/'):
        if method != 'PUT':
            send_error_response(sock, 405, 'Method Not Allowed', 'Use PUT method')
            return

        swing_str = path.split('/')[-1].upper()
        swing_map = {
            'AUTO': VDIR_AUTO,
            'SWING': VDIR_SWING,
            'UP': VDIR_UP,
            'MUP': VDIR_MUP,
            'MIDDLE': VDIR_MIDDLE,
            'MDOWN': VDIR_MDOWN,
            'DOWN': VDIR_DOWN
        }

        if swing_str in swing_map:
            nibe_ir.send(ir_driver, POWER_ON, MODE_HEAT, FAN_AUTO, 21, swing_map[swing_str], VDIR_AUTO)
            send_json_response(sock, 200, 'OK', {'swing': swing_str.lower(), 'message': f'Swing set to {swing_str.lower()}'})
        else:
            send_error_response(sock, 400, 'Bad Request', 'Invalid swing direction')

    else:
        send_error_response(sock, 404, 'Not Found', 'Endpoint not found')

def run_server(config, ir_driver, nibe_ir):
    """Run the web server"""
    if socket is None:
        print("Error: Socket module not available. Cannot start web server.")
        return

    # Create socket
    addr = socket.getaddrinfo('0.0.0.0', config['server']['port'])[0][-1]
    server_socket = socket.socket()
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(addr)
    server_socket.listen(1)

    print(f'Server listening on port {config["server"]["port"]}')

    try:
        while True:
            client_sock, client_addr = server_socket.accept()
            print(f'Client connected from {client_addr}')

            try:
                # Receive request
                request = client_sock.recv(1024).decode('utf-8')
                if request:
                    handle_request(client_sock, request, ir_driver, nibe_ir, config)
            except Exception as e:
                print(f'Error handling request: {e}')
                try:
                    send_error_response(client_sock, 500, 'Internal Server Error', 'Server error')
                except:
                    pass
            finally:
                client_sock.close()

    except KeyboardInterrupt:
        print('Server stopped')
    finally:
        server_socket.close()