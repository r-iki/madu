import json
import asyncio
import os
import sys
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from sensors.models import SpectralReading
from django.utils.timezone import now
from asgiref.sync import sync_to_async
from datetime import datetime
from pytz import timezone

# Fallback untuk lingkungan produksi yang tidak mendukung serial
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    # Mock serial class untuk lingkungan yang tidak mendukung serial
    class MockSerialConnection:
        """Mock Serial Connection for environments where pyserial is not available"""
        def __init__(self, port=None, baudrate=None, **kwargs):
            self.port = port
            self.baudrate = baudrate
            self.is_open = True
            self._in_waiting_data = []
            self._in_waiting = 0
        
        @property
        def in_waiting(self):
            return self._in_waiting
        
        def write(self, data):
            """Mock write method"""
            print(f"[MOCK SERIAL] Writing to serial: {data}")
            # Simulate response for some commands
            if b"get_info" in data:
                self._add_to_waiting('{"ip":"192.168.1.100","signal":-70,"device_name":"MockESP32"}')
            return len(data)
        
        def readline(self):
            """Mock readline method"""
            if self._in_waiting_data:
                data = self._in_waiting_data.pop(0)
                self._in_waiting = len(self._in_waiting_data)
                return data.encode('utf-8')
            return b""
        
        def close(self):
            """Mock close method"""
            self.is_open = False
            self._in_waiting = 0
            self._in_waiting_data = []
            print("[MOCK SERIAL] Connection closed")
        
        def _add_to_waiting(self, data):
            """Add data to waiting queue"""
            if isinstance(data, str):
                self._in_waiting_data.append(data)
                self._in_waiting = len(self._in_waiting_data)
                
    class MockSerialTools:
        """Mock Serial Tools for environments where pyserial is not available"""
        class ListPortInfo:
            def __init__(self, device, description):
                self.device = device
                self.description = description
                
        class Comports:
            @staticmethod
            def comports():
                """Return mock list of available ports"""
                return [MockSerialTools.ListPortInfo("COM1", "Mock USB Serial Device")]
                
    # Mock the serial module
    serial = type('serial', (), {
        'Serial': MockSerialConnection,
        'tools': MockSerialTools,
        'serialutil': type('serialutil', (), {'SerialException': Exception})
    })


class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("sensor_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("sensor_group", self.channel_name)

    async def receive(self, text_data):
        try:
            # Parse data yang diterima dari ESP32
            data = json.loads(text_data)

            # Simpan data ke database secara async
            spectral_reading = await self.save_spectral_reading(data)

            # Konversi timestamp ke zona waktu Jakarta
            jakarta_tz = timezone('Asia/Jakarta')
            timestamp_jakarta = spectral_reading.timestamp.astimezone(jakarta_tz)

            # Broadcast data ke frontend setelah tersimpan
            await self.channel_layer.group_send(
                "sensor_group",
                {
                    "type": "sensor.update",
                    "data": {
                        "id": spectral_reading.id,
                        "name": spectral_reading.name,
                        "kode": spectral_reading.kode,  # Tambahkan kode
                        "timestamp": timestamp_jakarta.isoformat(),  # Gunakan timestamp dalam zona waktu Jakarta
                        "uv_410": spectral_reading.uv_410,
                        "uv_435": spectral_reading.uv_435,
                        "uv_460": spectral_reading.uv_460,
                        "uv_485": spectral_reading.uv_485,
                        "uv_510": spectral_reading.uv_510,
                        "uv_535": spectral_reading.uv_535,
                        "vis_560": spectral_reading.vis_560,
                        "vis_585": spectral_reading.vis_585,
                        "vis_645": spectral_reading.vis_645,
                        "vis_705": spectral_reading.vis_705,
                        "vis_900": spectral_reading.vis_900,
                        "vis_940": spectral_reading.vis_940,
                        "nir_610": spectral_reading.nir_610,
                        "nir_680": spectral_reading.nir_680,
                        "nir_730": spectral_reading.nir_730,
                        "nir_760": spectral_reading.nir_760,
                        "nir_810": spectral_reading.nir_810,
                        "nir_860": spectral_reading.nir_860,
                        "temperature": spectral_reading.temperature,
                    },
                },
            )

            # Kirim respons sukses ke ESP32
            await self.send(text_data=json.dumps({
                "status": "success",
                "message": "Data berhasil diterima dan disimpan.",
                "id": spectral_reading.id,
                "name": spectral_reading.name,
                "timestamp": timestamp_jakarta.isoformat()
            }))

        except Exception as e:
            # Kirim respons error ke ESP32 jika terjadi kesalahan
            await self.send(text_data=json.dumps({
                "status": "error",
                "message": str(e)
            }))

    async def sensor_update(self, event):
        """Mengirimkan update ke frontend."""
        await self.send(text_data=json.dumps(event["data"]))

    @sync_to_async
    def save_spectral_reading(self, data):
        """Menyimpan data ke database dalam thread sinkron."""
        from pytz import timezone

        # Gunakan waktu saat ini jika timestamp tidak diberikan
        jakarta_tz = timezone('Asia/Jakarta')
        timestamp = data.get("timestamp", None)
        if not timestamp:  # Jika timestamp tidak ada atau None
            timestamp = now().astimezone(jakarta_tz)  # Gunakan waktu saat ini dalam zona waktu Jakarta
        else:
            try:
                # Konversi timestamp dari string ke datetime jika diberikan
                timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                timestamp = jakarta_tz.localize(timestamp)  # Pastikan timestamp sesuai dengan zona waktu Jakarta
            except ValueError:
                # Jika format tidak valid, gunakan waktu saat ini
                timestamp = now().astimezone(jakarta_tz)

        return SpectralReading.objects.create(
            name=data.get("name", "Unknown"),
            uv_410=data.get("uv_410", 0),
            uv_435=data.get("uv_435", 0),
            uv_460=data.get("uv_460", 0),
            uv_485=data.get("uv_485", 0),
            uv_510=data.get("uv_510", 0),
            uv_535=data.get("uv_535", 0),
            vis_560=data.get("vis_560", 0),
            vis_585=data.get("vis_585", 0),
            vis_645=data.get("vis_645", 0),
            vis_705=data.get("vis_705", 0),
            vis_900=data.get("vis_900", 0),
            vis_940=data.get("vis_940", 0),
            nir_610=data.get("nir_610", 0),
            nir_680=data.get("nir_680", 0),
            nir_730=data.get("nir_730", 0),
            nir_760=data.get("nir_760", 0),
            nir_810=data.get("nir_810", 0),
            nir_860=data.get("nir_860", 0),
            temperature=data.get("temperature", 0),
            timestamp=timestamp,  # Gunakan timestamp yang sudah diproses
        )


class SensorControlConsumer(AsyncWebsocketConsumer):
    esp32_connected = False
    esp32_serial = None
    serial_task = None
    
    # Shared class variable for all instances
    IN_PRODUCTION = os.environ.get('DJANGO_SETTINGS_MODULE', '') == 'core.settings.production'
    
    async def connect(self):
        await self.accept()
        self.room_name = "sensor_control"
        await self.channel_layer.group_add(self.room_name, self.channel_name)

    async def disconnect(self, close_code):
        # Clean up serial connection if active
        if self.serial_task and not self.serial_task.done():
            self.serial_task.cancel()
            
        if self.esp32_serial and self.esp32_serial.is_open:
            self.esp32_serial.close()
            self.esp32_connected = False
            
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        command = data.get("command")

        if command == "connect_esp32":
            await self.connect_to_esp32()
            
        elif command == "disconnect_esp32":
            await self.disconnect_from_esp32()
            
        elif command == "get_esp32_status":
            await self.send_esp32_status()
            
        elif command == "set_wifi":
            ssid = data.get("ssid")
            password = data.get("password", "")
            await self.set_wifi(ssid, password)
            
        elif command == "set_device_config":
            device_name = data.get("device_name")
            delay_time = data.get("delay_time")
            duration = data.get("duration")
            iterations = data.get("iterations")
            await self.set_device_config(device_name, delay_time, duration, iterations)
            
        elif command == "start_measurement":
            await self.start_measurement()

        elif command == "set_integration_time":
            integration_time = data.get("integration_time")
            await self.send_command_to_esp32(f"set_integration_time:{integration_time}")
            await self.send(text_data=json.dumps({"status": f"Integration time set to {integration_time} ms"}))

        elif command == "set_gain":
            gain = data.get("gain")
            await self.send_command_to_esp32(f"set_gain:{gain}")
            await self.send(text_data=json.dumps({"status": f"Gain set to {gain}x"}))

        elif command == "set_mode":
            mode = data.get("mode")
            await self.send_command_to_esp32(f"set_mode:{mode}")
            await self.send(text_data=json.dumps({"status": f"Measurement mode set to {mode}"}))

        elif command == "set_led":
            led_type = data.get("led_type")
            state = data.get("state")
            brightness = data.get("brightness")
            await self.send_command_to_esp32(f"set_led:{led_type},{state},{brightness}")
            await self.send(text_data=json.dumps({"status": f"{led_type} LED set to {state} with brightness {brightness}%"}))
            
        elif command == "send_raw_command":
            raw_command = data.get("raw_command")
            if raw_command:
                await self.send_command_to_esp32(raw_command)
                await self.send(text_data=json.dumps({"status": f"Command sent: {raw_command}"}))
            else:
                await self.send(text_data=json.dumps({"status": f"Error: Empty command"}))

    async def connect_to_esp32(self):
        """Connect to ESP32 via serial port"""
        if self.esp32_connected:
            await self.send(text_data=json.dumps({
                "status": "ESP32 already connected",
                "type": "connection_status",
                "connected": True
            }))
            return
            
        # Handle differently in production environment
        if self.IN_PRODUCTION or not SERIAL_AVAILABLE:
            await self.send(text_data=json.dumps({
                "status": "Using simulated ESP32 connection in cloud environment",
                "type": "connection_status",
                "connected": True,
                "ip": "127.0.0.1 (simulated)",
                "signal": "-60 (simulated)",
                "port": "SIMULATED"
            }))
            
            self.esp32_serial = MockSerialConnection("SIMULATED", 115200)
            self.esp32_connected = True
            
            # Start a task to simulate reading from serial
            if self.serial_task and not self.serial_task.done():
                self.serial_task.cancel()
                
            self.serial_task = asyncio.create_task(self.read_serial())
            return
        
        # Normal flow for local environment
        try:
            # Find available ports
            ports = await sync_to_async(list)(serial.tools.list_ports.comports())
            esp32_port = None
            
            for port in ports:
                if "USB" in port.description or "CH340" in port.description or "CP210x" in port.description:
                    esp32_port = port.device
                    break

            if not esp32_port:
                await self.send(text_data=json.dumps({
                    "status": "ESP32 not found. Connect device and try again.",
                    "type": "connection_status",
                    "connected": False
                }))
                return
                
            self.esp32_serial = serial.Serial(esp32_port, 115200, timeout=1)
            self.esp32_connected = True
            
            # Start a task to read from serial in background
            if self.serial_task and not self.serial_task.done():
                self.serial_task.cancel()
                
            self.serial_task = asyncio.create_task(self.read_serial())
            
            await self.send(text_data=json.dumps({
                "status": f"Connected to ESP32 on {esp32_port}",
                "type": "connection_status",
                "connected": True,
                "port": esp32_port,
                "ip": "Retrieving...",
                "signal": "Retrieving..."
            }))
            
            # Get device information
            await self.send_command_to_esp32("get_info")
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                "status": f"Error connecting to ESP32: {str(e)}",
                "type": "connection_status",
                "connected": False
            }))
            self.esp32_connected = False
            
    async def disconnect_from_esp32(self):
        """Disconnect from ESP32"""
        if not self.esp32_connected:
            await self.send(text_data=json.dumps({
                "status": "ESP32 not connected",
                "type": "connection_status",
                "connected": False
            }))
            return
            
        try:
            if self.serial_task and not self.serial_task.done():
                self.serial_task.cancel()
                
            if self.esp32_serial and self.esp32_serial.is_open:
                self.esp32_serial.close()
                
            self.esp32_connected = False
            
            await self.send(text_data=json.dumps({
                "status": "Disconnected from ESP32",
                "type": "connection_status",
                "connected": False
            }))
            
        except Exception as e:
            await self.send(text_data=json.dumps({
                "status": f"Error disconnecting from ESP32: {str(e)}",
                "type": "connection_status",
                "connected": self.esp32_connected
            }))
            
    async def send_esp32_status(self):
        """Send current ESP32 connection status"""
        await self.send(text_data=json.dumps({
            "status": "ESP32 status",
            "type": "connection_status",
            "connected": self.esp32_connected
        }))
        
    async def set_wifi(self, ssid, password):
        """Configure WiFi on ESP32"""
        if not self.esp32_connected:
            await self.send(text_data=json.dumps({
                "status": "ESP32 not connected. Connect first.",
            }))
            return
            
        await self.send_command_to_esp32(f"set_wifi:{ssid},{password}")
        await self.send(text_data=json.dumps({
            "status": f"WiFi settings sent to ESP32: SSID={ssid}"
        }))
        
    async def set_device_config(self, device_name, delay_time, duration, iterations):
        """Configure device settings on ESP32"""
        if not self.esp32_connected:
            await self.send(text_data=json.dumps({
                "status": "ESP32 not connected. Connect first.",
            }))
            return
            
        config_command = f"set_config:{device_name},{delay_time},{duration},{iterations}"
        await self.send_command_to_esp32(config_command)
        await self.send(text_data=json.dumps({
            "status": f"Device configuration sent to ESP32"
        }))
        
    async def start_measurement(self):
        """Start measurement on ESP32"""
        if not self.esp32_connected:
            await self.send(text_data=json.dumps({
                "status": "ESP32 not connected. Connect first.",
            }))
            return
            
        await self.send_command_to_esp32("start")
        await self.send(text_data=json.dumps({
            "status": f"Start command sent to ESP32"
        }))
        
    async def send_command_to_esp32(self, command):
        """Send a command to ESP32 via serial"""
        if not self.esp32_connected or not self.esp32_serial or not self.esp32_serial.is_open:
            await self.send(text_data=json.dumps({
                "status": "ESP32 not connected. Cannot send command.",
            }))
            return False
            
        try:
            self.esp32_serial.write((command + "\n").encode())
            return True
        except Exception as e:
            await self.send(text_data=json.dumps({
                "status": f"Error sending command to ESP32: {str(e)}",
            }))
            return False
            
    async def read_serial(self):
        """Read data from ESP32 serial in background"""
        if not self.esp32_connected or not self.esp32_serial:
            return
            
        try:
            while self.esp32_connected and self.esp32_serial.is_open:
                if self.esp32_serial.in_waiting > 0:
                    line = self.esp32_serial.readline().decode('utf-8', errors='replace').strip()
                    
                    if line:
                        # Check if it's a status message
                        if line.startswith("STATUS:"):
                            status_data = line.replace("STATUS:", "").strip()
                            try:
                                status = json.loads(status_data)
                                # Update connection info
                                if "ip" in status and "signal" in status:
                                    await self.send(text_data=json.dumps({
                                        "type": "connection_status",
                                        "connected": True,
                                        "ip": status["ip"],
                                        "signal": status["signal"]
                                    }))
                            except json.JSONDecodeError:
                                pass
                                
                        # Send all data to serial monitor
                        await self.send(text_data=json.dumps({
                            "type": "serial_data",
                            "message": line
                        }))
                        
                await asyncio.sleep(0.1)  # Small delay to prevent CPU hogging
                
        except asyncio.CancelledError:
            # Task was cancelled, clean up
            pass
        except Exception as e:
            await self.send(text_data=json.dumps({
                "status": f"Error reading from ESP32: {str(e)}",
                "type": "serial_data",
                "message": f"ERROR: {str(e)}"
            }))
            
            self.esp32_connected = False
            await self.send(text_data=json.dumps({
                "type": "connection_status",
                "connected": False
            }))
