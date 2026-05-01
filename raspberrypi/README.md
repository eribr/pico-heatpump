## Nibe Server
Create a config.json like
```
{
    "api_password": "your-password-here"
}

```

Run the REST server with
```
sudo pigpiod
python3 nibe_server.py
```

Call on it with
```
# Set temperature to 22
curl -X PUT http://localhost:5000/api/temp/22 -u :your_secret_password_here

# Turn Power Off
curl -X PUT http://localhost:5000/api/power/off -u :your_secret_password_here
```

## Step-by-Step Connection

* **Identify the BC547:** Hold the transistor with the flat side facing you. The pins are (from left to right): **1. Collector**, **2. Base**, **3. Emitter**.
* **Base (Middle):** Connect the 10 kΩ resistor between **GPIO 17** (Physical Pin 11) and the middle pin of the transistor.
* **Emitter (Right):** Connect this pin directly to a **GND** pin (e.g., Physical Pin 6 or 9).
* **Collector (Left):** Connect this to the short leg (**Cathode**) of the IR LED.
* **Power & IR LED:**
    * Connect the long leg (**Anode**) of the IR LED to your parallel-connected 220 Ω resistors.
    * Connect the other end of the resistors to **5V** (Physical Pin 2).
