# Model-specific configuration for Nibe heatpump IR

MODEL = "nibe"
INFO = '{"mdl":"nibe","dn":"Nibe","mT":10,"xT":32,"fs":5}'

# IR command constants
POWER_ON = 0x01
POWER_OFF = 0x00

# Operating modes (model mappings)
MODE_AUTO = 0x00
MODE_HEAT = 0x01
MODE_COOL = 0x02
MODE_DRY = 0x03
MODE_FAN = 0x04

# Fan speed settings (model mappings)
FAN_AUTO = 0x00
FAN_4 = 0x01
FAN_3 = 0x02
FAN_2 = 0x03
FAN_SILENT = 0x04

# Vertical direction settings (model mappings)
VDIR_AUTO = 0x00
VDIR_SWING = 0x01
VDIR_UP = 0x02
VDIR_MUP = 0x03
VDIR_MIDDLE = 0x04
VDIR_MDOWN = 0x05
VDIR_DOWN = 0x06

# Nibe-specific IR timings and protocol values (microseconds)
NIBE_HDR_MARK = 9000
NIBE_HDR_SPACE = 4500
NIBE_BIT_MARK = 560
NIBE_ZERO_SPACE = 1690
NIBE_ONE_SPACE = 560
NIBE_MSG_SPACE = 4500

# Temperature range (allowed by model)
TEMP_MIN = 10
TEMP_MAX = 32


class NibeHeatpumpIR:
	def __init__(self):
		self.model = MODEL
		try:
			# INFO may be provided as JSON string in this module
			self.info = INFO
		except NameError:
			self.info = {"mdl": MODEL}

	def send(self, ir_driver, power_mode_cmd, operating_mode_cmd, fan_speed_cmd, temperature_cmd, swing_v_cmd, swing_h_cmd, turbo_mode_cmd=False, ifeel_mode_cmd=False):
		# Single-entry convenience method — forwards to send_full
		self.send_full(ir_driver, power_mode_cmd, operating_mode_cmd, fan_speed_cmd, temperature_cmd, swing_v_cmd, swing_h_cmd, turbo_mode_cmd, ifeel_mode_cmd)

	def send_full(self, ir_driver, power_mode_cmd, operating_mode_cmd, fan_speed_cmd, temperature_cmd, swing_v_cmd, swing_h_cmd, turbo_mode_cmd, ifeel_mode_cmd):
		# Accept either numeric constants or string names for the commands
		power_mode = 1 if power_mode_cmd == POWER_ON or power_mode_cmd == "POWER_ON" or power_mode_cmd == 1 else 0
		operating_mode = self.get_operating_mode(operating_mode_cmd)
		fan_speed = self.get_fan_speed(fan_speed_cmd)
		temperature = self.get_temperature(temperature_cmd)
		swing_v = self.get_swing_v(swing_v_cmd)

		self.send_nibe(ir_driver, power_mode, operating_mode, fan_speed, temperature, swing_v, 1 if ifeel_mode_cmd else 0, 1 if turbo_mode_cmd else 0)

	def get_operating_mode(self, cmd):
		# If numeric, assume already mapped
		if isinstance(cmd, int):
			return cmd
		modes = {
			"MODE_AUTO": MODE_AUTO,
			"MODE_HEAT": MODE_HEAT,
			"MODE_COOL": MODE_COOL,
			"MODE_DRY": MODE_DRY,
			"MODE_FAN": MODE_FAN
		}
		return modes.get(cmd, 0)

	def get_fan_speed(self, cmd):
		if isinstance(cmd, int):
			return cmd
		speeds = {
			"FAN_AUTO": FAN_AUTO,
			"FAN_4": FAN_4,
			"FAN_3": FAN_3,
			"FAN_2": FAN_2,
			"FAN_SILENT": FAN_SILENT
		}
		return speeds.get(cmd, 0)

	def get_temperature(self, cmd):
		# Expect a human temperature value in degrees (e.g. 10..32). Encode as (temp - 4)
		if isinstance(cmd, int) and TEMP_MIN <= cmd <= TEMP_MAX:
			return cmd - 4
		raise ValueError("temperature out of range: {}".format(cmd))

	def get_swing_v(self, cmd):
		if isinstance(cmd, int):
			return cmd
		swing_positions = {
			"VDIR_AUTO": VDIR_AUTO,
			"VDIR_SWING": VDIR_SWING,
			"VDIR_UP": VDIR_UP,
			"VDIR_MUP": VDIR_MUP,
			"VDIR_MIDDLE": VDIR_MIDDLE,
			"VDIR_MDOWN": VDIR_MDOWN,
			"VDIR_DOWN": VDIR_DOWN
		}
		return swing_positions.get(cmd, 0)

	def send_nibe(self, ir_driver, power_mode, operating_mode, fan_speed, temperature, swing_v, ifeel_mode, turbo_mode):
		# Build the 12-byte Nibe template and send via provided IR driver
		nibe_template = bytearray([0x35, 0xAF, 0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00])

		nibe_template[2] |= (operating_mode << 2) | (temperature >> 3)
		nibe_template[3] |= ((temperature & 0x07) << 5) | (fan_speed << 3)
		nibe_template[4] |= (swing_v << 3)

		current_time = self.get_current_time()
		nibe_template[7] |= (current_time >> 6)
		nibe_template[8] |= (current_time & 0x3F) << 2

		nibe_template[9] |= (ifeel_mode << 0) | (power_mode << 2) | (turbo_mode << 4)

		checksum = self.calculate_checksum(nibe_template)
		nibe_template[11] = checksum

		#ir_driver.set_frequency(38)
		ir_driver.send_ir(nibe_template)

	def get_current_time(self):
		import time
		now = time.localtime()
		# MicroPython returns a tuple, not a struct_time object.
		# Accept both forms for compatibility.
		if hasattr(now, "tm_hour"):
			hour = now.tm_hour
			minute = now.tm_min
		else:
			hour = now[3]
			minute = now[4]
		return (hour * 60 + minute) & 0x7FF

	def calculate_checksum(self, template):
		checksum = 0
		for i in range(11):
			checksum += template[i]
		return checksum & 0xFF