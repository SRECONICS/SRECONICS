#!/usr/bin/env python3
"""
lorawan_stack.py — Minimal LoRaWAN MAC layer for RAK2245/SX1302
OTAA join, confirmed uplinks, ADR support
"""

import struct
import time
import binascii
from typing import Optional, Tuple
import spidev


class LoRaWANStack:
    def __init__(self, dev_eui: str, app_eui: str, app_key: str, region: str = "EU868"):
        self.dev_eui = binascii.unhexlify(dev_eui.replace(":", ""))
        self.app_eui = binascii.unhexlify(app_eui.replace(":", ""))
        self.app_key = binascii.unhexlify(app_key.replace(":", ""))
        self.region = region
        
        # Session keys (set after join)
        self.nwk_skey: Optional[bytes] = None
        self.app_skey: Optional[bytes] = None
        self.dev_addr: Optional[bytes] = None
        
        # Frame counters
        self.fcnt_up = 0
        self.fcnt_down = 0
        
        # SPI to SX1302 via RAK2245
        self.spi = spidev.SpiDev()
        self.spi.open(0, 0)  # CE0
        self.spi.max_speed_hz = 2_000_000
        self.spi.mode = 0b00
        
        # Channel plans
        self.channels = self._get_channel_plan(region)
        self.current_channel = 0
        
        # ADR state
        self.adr_enabled = True
        self.margin = 15  # dB
        self.nb_trans = 1

    def _get_channel_plan(self, region: str):
        if region == "EU868":
            return [868100000, 868300000, 868500000, 867100000, 867300000, 867500000, 867700000, 867900000]
        elif region == "US915":
            return [902300000 + i * 200000 for i in range(64)]
        else:
            return [868100000, 868300000, 868500000]

    def join_otaa(self, max_retries: int = 5) -> bool:
        """Perform OTAA join procedure."""
        print(f"Starting OTAA join on {self.region}...")
        
        for attempt in range(max_retries):
            # Build Join Request
            join_req = self._build_join_request()
            
            # Send on default join channels
            for ch_freq in self.channels[:3]:
                self._set_frequency(ch_freq)
                self._send_raw(join_req)
                
                # Wait for Join Accept
                accept = self._wait_for_join_accept(timeout=5)
                if accept:
                    self._process_join_accept(accept)
                    print(f"Join successful! DevAddr: {self.dev_addr.hex().upper()}")
                    return True
            
            print(f"Join attempt {attempt + 1} failed, retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff
        
        return False

    def _build_join_request(self) -> bytes:
        """Build LoRaWAN Join Request (MHDR=0x00)."""
        # MHDR (0x00) + AppEUI + DevEUI + DevNonce
        dev_nonce = struct.pack('<H', int(time.time()) & 0xFFFF)
        msg = b'\x00' + self.app_eui + self.dev_eui + dev_nonce
        
        # MIC = aes128_cmac(AppKey, msg)
        mic = self._aes128_cmac(self.app_key, msg)
        return msg + mic

    def _wait_for_join_accept(self, timeout: int) -> Optional[bytes]:
        """Listen for Join Accept on RX1/RX2 windows."""
        # Simplified: in real implementation, configure SX1302 for RX
        # This is a placeholder for the actual radio driver
        time.sleep(1)
        return None  # Placeholder

    def _process_join_accept(self, join_accept: bytes):
        """Derive session keys from Join Accept."""
        # Decrypt Join Accept with AppKey
        # JoinAccept = AppNonce(3) + NetID(3) + DevAddr(4) + DLSettings(1) + RxDelay(1) + CFList(16) + MIC(4)
        # Decrypted = AES128_Decrypt(AppKey, JoinAccept[1:])  # skip MHDR
        # This is a placeholder - real implementation needs AES
        self.dev_addr = join_accept[6:10]
        self.nwk_skey = b'\x00' * 16  # Placeholder
        self.app_skey = b'\x00' * 16  # Placeholder

    def send(self, payload: bytes, confirmed: bool = True, port: int = 1) -> bool:
        """Send uplink data frame."""
        if not self.dev_addr:
            raise RuntimeError("Not joined - call join_otaa() first")
        
        # Build PHYPayload
        mhdr = 0x40 if confirmed else 0x60  # Confirmed/Unconfirmed Data Up
        fhdr = self._build_fhdr(port)
        fport = bytes([port]) if payload else b''
        
        # Encrypt FRMPayload
        encrypted = self._encrypt_frm_payload(payload, self.fcnt_up, self.app_skey)
        
        msg = bytes([mhdr]) + fhdr + fport + encrypted
        mic = self._calculate_mic(msg, self.nwk_skey, 'up', self.dev_addr, self.fcnt_up)
        phy_payload = msg + mic
        
        # Transmit
        freq = self.channels[self.current_channel]
        self._set_frequency(freq)
        self._set_datarate(self._get_current_dr())
        self._send_raw(phy_payload)
        
        self.fcnt_up += 1
        self.current_channel = (self.current_channel + 1) % len(self.channels)
        
        # Handle confirmed uplink retry
        if confirmed:
            ack = self._wait_for_ack()
            if not ack:
                print("No ACK received, will retry on next cycle")
        
        return True

    def _build_fhdr(self, port: int) -> bytes:
        """Build Frame Header."""
        fctrl = 0x00
        if self.adr_enabled:
            fctrl |= 0x80  # ADR bit
        if port == 0:
            fctrl |= 0x10  # FOptsLen (MAC commands)
        
        return self.dev_addr + bytes([fctrl]) + struct.pack('<H', self.fcnt_up)

    def _encrypt_frm_payload(self, payload: bytes, fcnt: int, key: bytes) -> bytes:
        """AES-CTR encrypt FRMPayload."""
        # Placeholder - real implementation uses AES-CTR with key, devaddr, fcnt, dir=0
        return payload

    def _calculate_mic(self, msg: bytes, key: bytes, direction: str, dev_addr: bytes, fcnt: int) -> bytes:
        """Calculate CMAC MIC."""
        # B0 = 0x49 + 4*0 + dir(1) + devaddr(4) + fcnt(4) + 0 + len(msg)
        # Placeholder
        return b'\x00\x00\x00\x00'

    def _aes128_cmac(self, key: bytes, msg: bytes) -> bytes:
        """AES-128 CMAC."""
        # Placeholder
        return b'\x00\x00\x00\x00'

    def _set_frequency(self, freq_hz: int):
        """Configure SX1302 frequency via SPI."""
        # SX1302 register writes
        pass

    def _set_datarate(self, dr: int):
        """Set LoRa datarate (SF/BW)."""
        pass

    def _get_current_dr(self) -> int:
        return 5  # SF7/125kHz default

    def _send_raw(self, data: bytes):
        """Raw SPI transmit to SX1302."""
        # Write to SX1302 TX FIFO
        pass

    def _wait_for_ack(self, timeout: int = 3) -> bool:
        """Wait for ACK in RX1 window."""
        time.sleep(1)
        return False  # Placeholder


if __name__ == "__main__":
    # Quick test
    stack = LoRaWANStack(
        dev_eui="00:11:22:33:44:55:66:77",
        app_eui="77:66:55:44:33:22:11:00",
        app_key="00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF"
    )
    print("LoRaWAN stack initialized (test mode)")