#!/usr/bin/env python3
"""
power_mgmt.py — Power management for Zero 2 W LoRaWAN sensor node
DS3231 RTC alarm wake-up, GPIO interrupt routing, battery voltage monitoring
"""

import time
import struct
from smbus2 import SMBus
import RPi.GPIO as GPIO


class PowerManager:
    def __init__(self, rtc_bus: int = 1, rtc_addr: int = 0x68, wake_gpio: int = 4,
                 bat_adc_channel: int = 0, bat_divider_ratio: float = 2.0):
        self.rtc_bus = SMBus(rtc_bus)
        self.rtc_addr = rtc_addr
        self.wake_gpio = wake_gpio
        self.bat_adc_channel = bat_adc_channel
        self.bat_divider_ratio = bat_divider_ratio
        
        # Initialize GPIO for wake interrupt
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.wake_gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Initialize RTC
        self._init_rtc()
        
        # ADC for battery (using internal ADC via spidev or external MCP3008)
        # Placeholder for ADC setup
        self._adc_initialized = False
    
    def _init_rtc(self):
        """Initialize DS3231 RTC."""
        # Check if RTC is running
        status = self.rtc_bus.read_byte_data(self.rtc_addr, 0x0F)
        if status & 0x80:  # OSF flag - oscillator stopped
            print("RTC oscillator stopped, setting time...")
            self.set_time(int(time.time()))
        
        # Clear alarm flags
        self.rtc_bus.write_byte_data(self.rtc_addr, 0x0F, 0x00)
        
        # Configure control register: enable alarm 1 interrupt, INTCN=1
        ctrl = self.rtc_bus.read_byte_data(self.rtc_addr, 0x0E)
        ctrl |= 0x05  # A1IE=1, INTCN=1
        self.rtc_bus.write_byte_data(self.rtc_addr, 0x0E, ctrl)
    
    def set_time(self, unix_time: int):
        """Set RTC time from Unix timestamp."""
        tm = time.gmtime(unix_time)
        # DS3231 registers: 00=sec, 01=min, 02=hour, 03=day, 04=date, 05=month, 06=year
        data = [
            self._dec2bcd(tm.tm_sec),
            self._dec2bcd(tm.tm_min),
            self._dec2bcd(tm.tm_hour),
            self._dec2bcd(tm.tm_wday + 1),  # 1-7
            self._dec2bcd(tm.tm_mday),
            self._dec2bcd(tm.tm_mon),
            self._dec2bcd(tm.tm_year - 2000)
        ]
        self.rtc_bus.write_i2c_block_data(self.rtc_addr, 0x00, data)
    
    def get_time(self) -> int:
        """Get current time as Unix timestamp."""
        data = self.rtc_bus.read_i2c_block_data(self.rtc_addr, 0x00, 7)
        tm = time.struct_time((
            2000 + self._bcd2dec(data[6]),
            self._bcd2dec(data[5]),
            self._bcd2dec(data[4]),
            self._bcd2dec(data[2]),
            self._bcd2dec(data[1]),
            self._bcd2dec(data[0]),
            0, 0, 0
        ))
        return int(time.mktime(tm))
    
    def set_alarm(self, seconds_from_now: int):
        """Set Alarm 1 to trigger after specified seconds."""
        wake_time = self.get_time() + seconds_from_now
        tm = time.gmtime(wake_time)
        
        # Alarm 1 registers: 0x07=sec, 0x08=min, 0x09=hour, 0x0A=date/day
        # Match on minutes, hours, date (every day)
        alarm_data = [
            self._dec2bcd(tm.tm_sec) | 0x80,  # A1M1=1 (mask seconds)
            self._dec2bcd(tm.tm_min),          # Match minutes
            self._dec2bcd(tm.tm_hour),         # Match hours
            self._dec2bcd(tm.tm_mday) | 0x40   # Match date, A1M4=0
        ]
        self.rtc_bus.write_i2c_block_data(self.rtc_addr, 0x07, alarm_data)
        
        # Enable alarm 1 interrupt
        ctrl = self.rtc_bus.read_byte_data(self.rtc_addr, 0x0E)
        ctrl |= 0x01  # A1IE
        self.rtc_bus.write_byte_data(self.rtc_addr, 0x0E, ctrl)
        
        print(f"Alarm set for {time.strftime('%H:%M:%S', tm)} UTC")
    
    def clear_alarm(self):
        """Clear alarm flag."""
        status = self.rtc_bus.read_byte_data(self.rtc_addr, 0x0F)
        status &= ~0x01  # Clear A1F
        self.rtc_bus.write_byte_data(self.rtc_addr, 0x0F, status)
    
    def deep_sleep(self, seconds: int):
        """Enter deep sleep until RTC alarm triggers."""
        if seconds <= 0:
            return
        
        print(f"Entering deep sleep for {seconds} seconds...")
        
        # Set alarm
        self.set_alarm(seconds)
        
        # Clear any pending alarm flag
        self.clear_alarm()
        
        # Configure GPIO interrupt for wake
        # Note: On Pi Zero 2 W, GPIO state is maintained during sleep
        # The DS3231 INT/SQW pin (active low) connects to GPIO4
        # When alarm triggers, it pulls GPIO4 low
        
        # For true deep sleep, we'd need to power off the Pi
        # This implementation uses a light sleep with CPU halted
        # Real deep sleep requires external power control (MOSFET + RTC)
        
        # Simulated sleep for development
        # In production: use dtoverlay=gpio-poweroff or external circuit
        time.sleep(min(seconds, 10))  # Cap at 10s for testing
        
        # Clear alarm after wake
        self.clear_alarm()
    
    def read_battery_voltage(self) -> float:
        """Read battery voltage via ADC."""
        # Placeholder: implement ADC reading
        # For MCP3008 on SPI:
        # import spidev
        # spi = spidev.SpiDev()
        # spi.open(0, 1)
        # resp = spi.xfer2([1, (8 + self.bat_adc_channel) << 4, 0])
        # adc_val = ((resp[1] & 3) << 8) | resp[2]
        # voltage = (adc_val / 1023.0) * 3.3 * self.bat_divider_ratio
        
        # Simulated reading for development
        import random
        return 3.7 + random.uniform(-0.1, 0.2)
    
    def read_battery_mv(self) -> int:
        """Read battery voltage in millivolts."""
        return int(self.read_battery_voltage() * 1000)
    
    def is_battery_low(self, threshold_v: float = 3.3) -> bool:
        """Check if battery is below threshold."""
        return self.read_battery_voltage() < threshold_v
    
    def get_rtc_temperature(self) -> float:
        """Read RTC internal temperature (±3°C accuracy)."""
        msb = self.rtc_bus.read_byte_data(self.rtc_addr, 0x11)
        lsb = self.rtc_bus.read_byte_data(self.rtc_addr, 0x12)
        return msb + (lsb >> 6) * 0.25
    
    @staticmethod
    def _dec2bcd(val: int) -> int:
        return ((val // 10) << 4) | (val % 10)
    
    @staticmethod
    def _bcd2dec(val: int) -> int:
        return ((val >> 4) * 10) + (val & 0x0F)
    
    def cleanup(self):
        """Cleanup GPIO."""
        GPIO.cleanup()


class Watchdog:
    """Hardware watchdog via GPIO (requires external circuit) or software watchdog."""
    
    def __init__(self, timeout_sec: int = 60, gpio_pin: int = None):
        self.timeout = timeout_sec
        self.gpio_pin = gpio_pin
        self.last_kick = time.time()
        self.enabled = False
        
        if gpio_pin:
            GPIO.setup(gpio_pin, GPIO.OUT)
            GPIO.output(gpio_pin, GPIO.HIGH)
    
    def enable(self):
        self.enabled = True
        self.last_kick = time.time()
    
    def disable(self):
        self.enabled = False
        if self.gpio_pin:
            GPIO.output(self.gpio_pin, GPIO.LOW)
    
    def kick(self):
        """Reset watchdog timer."""
        self.last_kick = time.time()
        if self.gpio_pin:
            # Pulse the watchdog pin
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(0.01)
            GPIO.output(self.gpio_pin, GPIO.HIGH)
    
    def check(self) -> bool:
        """Check if watchdog has expired. Returns True if expired."""
        if not self.enabled:
            return False
        return (time.time() - self.last_kick) > self.timeout


if __name__ == "__main__":
    pm = PowerManager()
    print(f"RTC Time: {time.ctime(pm.get_time())}")
    print(f"RTC Temp: {pm.get_rtc_temperature():.1f}°C")
    print(f"Battery: {pm.read_battery_voltage():.2f} V")
    
    # Test alarm
    pm.set_alarm(5)
    pm.deep_sleep(5)
    print("Woke up!")