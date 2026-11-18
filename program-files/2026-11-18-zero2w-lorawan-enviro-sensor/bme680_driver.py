#!/usr/bin/env python3
"""
bme680_driver.py — I²C driver for BME680 environmental sensor
Compensated readings for temperature, humidity, pressure, and gas resistance (VOC/IAQ)
"""

import time
import struct
from smbus2 import SMBus


class BME680:
    """BME680 driver with full compensation formulas from Bosch datasheet."""
    
    # Registers
    REG_CHIP_ID = 0xD0
    REG_RESET = 0xE0
    REG_CTRL_GAS_0 = 0x70
    REG_CTRL_GAS_1 = 0x71
    REG_CTRL_HUM = 0x72
    REG_CTRL_MEAS = 0x74
    REG_CONFIG = 0x75
    REG_GAS_WAIT_0 = 0x64
    REG_RES_HEAT_0 = 0x5A
    REG_IDAC_HEAT_0 = 0x50
    REG_GAS_R_LSB = 0x2B
    REG_RES_HEAT_VAL = 0x00
    REG_RES_HEAT_RANGE = 0x02
    REG_RANGE_SW_ERR = 0x04
    
    # Calibration registers
    CALIB_START = 0x8A
    CALIB_END = 0xA1
    
    CHIP_ID = 0x61
    
    # Oversampling settings
    OS_NONE = 0
    OS_1X = 1
    OS_2X = 2
    OS_4X = 3
    OS_8X = 4
    OS_16X = 5
    
    # Filter settings
    FILTER_OFF = 0
    FILTER_2 = 1
    FILTER_4 = 2
    FILTER_8 = 3
    FILTER_16 = 4
    FILTER_32 = 5
    FILTER_64 = 6
    FILTER_128 = 7
    
    def __init__(self, i2c_bus: int = 1, address: int = 0x77):
        self.bus = SMBus(i2c_bus)
        self.address = address
        self._calib = {}
        self._t_fine = 0
        
        self._init_sensor()
        self._read_calibration()
        
        # Gas heater profile (300°C for 100ms)
        self.set_gas_heater(300, 100)
    
    def _init_sensor(self):
        """Initialize and verify sensor."""
        chip_id = self.bus.read_byte_data(self.address, self.REG_CHIP_ID)
        if chip_id != self.CHIP_ID:
            raise RuntimeError(f"BME680 not found at 0x{self.address:02X} (ID: 0x{chip_id:02X})")
        
        # Soft reset
        self.bus.write_byte_data(self.address, self.REG_RESET, 0xB6)
        time.sleep(0.01)
        
        # Configure: humidity OS 2x, temp OS 8x, pressure OS 4x, filter 3
        self.bus.write_byte_data(self.address, self.REG_CTRL_HUM, self.OS_2X)
        self.bus.write_byte_data(self.address, self.REG_CTRL_MEAS, 
                                 (self.OS_8X << 5) | (self.OS_4X << 2) | 1)  # Mode 1 = forced
        self.bus.write_byte_data(self.address, self.REG_CONFIG, (self.FILTER_3 << 2))
        
        # Enable gas measurement
        self.bus.write_byte_data(self.address, self.REG_CTRL_GAS_1, 0x00)  # Run gas
        self.bus.write_byte_data(self.address, self.REG_CTRL_GAS_0, 0x10)  # NB conversion = 1
    
    def _read_calibration(self):
        """Read all calibration coefficients from sensor."""
        # Read calibration data (0x8A-0xA1 = 24 bytes, plus more)
        data = self.bus.read_i2c_block_data(self.address, self.CALIB_START, 25)
        
        # Temperature calibration
        self._calib['par_t1'] = struct.unpack('<H', bytes(data[33:35]))[0]
        self._calib['par_t2'] = struct.unpack('<h', bytes(data[35:37]))[0]
        self._calib['par_t3'] = struct.unpack('b', bytes([data[37]]))[0]
        
        # Pressure calibration
        self._calib['par_p1'] = struct.unpack('<H', bytes(data[0:2]))[0]
        self._calib['par_p2'] = struct.unpack('<h', bytes(data[2:4]))[0]
        self._calib['par_p3'] = struct.unpack('b', bytes([data[4]]))[0]
        self._calib['par_p4'] = struct.unpack('<h', bytes(data[5:7]))[0]
        self._calib['par_p5'] = struct.unpack('<h', bytes(data[7:9]))[0]
        self._calib['par_p6'] = struct.unpack('b', bytes([data[9]]))[0]
        self._calib['par_p7'] = struct.unpack('b', bytes([data[10]]))[0]
        self._calib['par_p8'] = struct.unpack('<h', bytes(data[11:13]))[0]
        self._calib['par_p9'] = struct.unpack('<h', bytes(data[13:15]))[0]
        self._calib['par_p10'] = struct.unpack('b', bytes([data[15]]))[0]
        
        # Humidity calibration
        self._calib['par_h1'] = (data[17] << 4) | (data[16] & 0x0F)
        self._calib['par_h2'] = (data[18] << 4) | (data[16] >> 4)
        self._calib['par_h3'] = struct.unpack('b', bytes([data[19]]))[0]
        self._calib['par_h4'] = struct.unpack('b', bytes([data[20]]))[0]
        self._calib['par_h5'] = struct.unpack('b', bytes([data[21]]))[0]
        self._calib['par_h6'] = struct.unpack('b', bytes([data[22]]))[0]
        self._calib['par_h7'] = struct.unpack('b', bytes([data[23]]))[0]
        
        # Gas calibration
        self._calib['par_gh1'] = struct.unpack('b', bytes([data[31]]))[0]
        self._calib['par_gh2'] = struct.unpack('<h', bytes(data[29:31]))[0]
        self._calib['par_gh3'] = struct.unpack('b', bytes([data[30]]))[0]
        
        # Heat range/val
        self._calib['res_heat_range'] = (self.bus.read_byte_data(self.address, self.REG_RES_HEAT_RANGE) >> 4) & 0x03
        self._calib['res_heat_val'] = struct.unpack('b', 
            bytes([self.bus.read_byte_data(self.address, self.REG_RES_HEAT_VAL)]))[0]
        self._calib['range_sw_err'] = struct.unpack('b', 
            bytes([self.bus.read_byte_data(self.address, self.REG_RANGE_SW_ERR)]))[0]
    
    def set_gas_heater(self, temp_c: int, duration_ms: int):
        """Configure gas heater temperature and duration."""
        # Calculate register values (simplified)
        # Duration: 0-4032ms in steps
        dur_reg = min(255, max(0, int(duration_ms / 15.625)))
        self.bus.write_byte_data(self.address, self.REG_GAS_WAIT_0, dur_reg)
        
        # Temperature: complex calculation, simplified here
        # For 300°C approx:
        temp_reg = min(255, max(0, int((temp_c - 25) * 2.5)))
        self.bus.write_byte_data(self.address, self.REG_RES_HEAT_0, temp_reg)
    
    def read_all(self) -> dict:
        """Trigger measurement and return all compensated readings."""
        # Trigger forced mode measurement
        ctrl_meas = self.bus.read_byte_data(self.address, self.REG_CTRL_MEAS)
        self.bus.write_byte_data(self.address, self.REG_CTRL_MEAS, ctrl_meas | 0x01)
        
        # Wait for measurement (typical ~50ms for this config)
        time.sleep(0.06)
        
        # Read raw data (registers 0x1D-0x2B = 15 bytes)
        data = self.bus.read_i2c_block_data(self.address, 0x1D, 15)
        
        # Parse raw values
        adc_press = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        adc_temp = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        adc_hum = (data[6] << 8) | data[7]
        gas_r_lsb = data[13]
        gas_r_msb = data[14]
        gas_range = (data[12] >> 4) & 0x0F
        gas_valid = (data[12] >> 3) & 0x01
        heat_stable = (data[12] >> 2) & 0x01
        
        # Compensate
        temperature = self._compensate_temperature(adc_temp)
        pressure = self._compensate_pressure(adc_press)
        humidity = self._compensate_humidity(adc_hum)
        
        result = {
            "temperature": temperature,      # °C
            "pressure": pressure,            # hPa
            "humidity": humidity,            # %RH
        }
        
        if gas_valid and heat_stable:
            gas_resistance = self._compensate_gas(gas_r_msb, gas_r_lsb, gas_range)
            result["gas_resistance"] = gas_resistance  # Ohms
            result["iaq_score"] = self._calculate_iaq(gas_resistance, humidity)
        else:
            result["gas_resistance"] = None
            result["iaq_score"] = None
        
        return result
    
    def _compensate_temperature(self, adc_temp: int) -> float:
        """Compensate temperature reading."""
        var1 = (adc_temp / 16384.0 - self._calib['par_t1'] / 1024.0) * self._calib['par_t2']
        var2 = ((adc_temp / 131072.0 - self._calib['par_t1'] / 8192.0) ** 2) * self._calib['par_t3'] * 16
        self._t_fine = var1 + var2
        return self._t_fine / 5120.0
    
    def _compensate_pressure(self, adc_press: int) -> float:
        """Compensate pressure reading."""
        t_fine = self._t_fine
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self._calib['par_p6'] / 131072.0
        var2 += var1 * self._calib['par_p5'] * 2.0
        var2 = var2 / 4.0 + self._calib['par_p4'] * 65536.0
        var1 = (self._calib['par_p3'] * var1 * var1 / 16384.0 + self._calib['par_p2'] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self._calib['par_p1']
        
        if var1 == 0:
            return 0.0
        
        pressure = 1048576.0 - adc_press
        pressure = (pressure - var2 / 4096.0) * 6250.0 / var1
        var1 = self._calib['par_p9'] * pressure * pressure / 2147483648.0
        var2 = pressure * self._calib['par_p8'] / 32768.0
        var3 = (pressure / 256.0) ** 3 * self._calib['par_p10'] / 131072.0
        pressure = pressure + (var1 + var2 + var3 + self._calib['par_p7'] * 128.0) / 16.0
        
        return pressure / 100.0  # Convert to hPa
    
    def _compensate_humidity(self, adc_hum: int) -> float:
        """Compensate humidity reading."""
        temp = self._t_fine / 5120.0
        var1 = adc_hum - (self._calib['par_h1'] * 16.0 + self._calib['par_h3'] / 2.0 * temp)
        var2 = var1 * (self._calib['par_h2'] / 262144.0 * (1.0 + self._calib['par_h4'] / 16384.0 * temp + 
                                                           self._calib['par_h5'] / 1048576.0 * temp * temp))
        var3 = self._calib['par_h6'] / 16384.0
        var4 = self._calib['par_h7'] / 2097152.0
        humidity = var2 + (var3 + var4 * temp) * var2
        
        if humidity > 100.0:
            humidity = 100.0
        elif humidity < 0.0:
            humidity = 0.0
        
        return humidity
    
    def _compensate_gas(self, msb: int, lsb: int, gas_range: int) -> float:
        """Compensate gas resistance reading."""
        adc_gas = (msb << 2) | (lsb >> 6)
        const = self._lookup_gas_range(gas_range)
        var1 = (1340 + (5 * self._calib['range_sw_err'])) * const
        gas_res = var1 * (1 << 15) / (adc_gas + 1)
        return gas_res
    
    def _lookup_gas_range(self, gas_range: int) -> float:
        """Lookup table for gas range multiplier."""
        ranges = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 
                  2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0, 256.0]
        return ranges[gas_range] if gas_range < len(ranges) else 1.0
    
    def _calculate_iaq(self, gas_res: float, humidity: float) -> float:
        """Calculate IAQ score (0-500, lower is better)."""
        # Simplified IAQ based on gas resistance and humidity
        # Typical: 50k-500k Ohms = good, <10k = poor
        if gas_res is None:
            return 250.0
        
        gas_score = min(500, max(0, 500 * (1 - min(1, gas_res / 500000))))
        hum_score = abs(humidity - 40) * 2  # Penalty for deviation from 40% RH
        return min(500, gas_score + hum_score)


if __name__ == "__main__":
    sensor = BME680(i2c_bus=1, address=0x77)
    print("BME680 initialized")
    
    for _ in range(3):
        readings = sensor.read_all()
        print(f"Temp: {readings['temperature']:.2f}°C  "
              f"Humidity: {readings['humidity']:.1f}%  "
              f"Pressure: {readings['pressure']:.1f} hPa  "
              f"Gas: {readings.get('gas_resistance', 'N/A')} Ω  "
              f"IAQ: {readings.get('iaq_score', 'N/A')}")
        time.sleep(1)