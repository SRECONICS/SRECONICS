#!/usr/bin/env python3
"""Read NMEA sentences from a NEO-6M USB GPS and store to SQLite."""
import serial, sqlite3, datetime, re, time

GPS_PORT = "/dev/ttyUSB1"   # change if needed
DB       = "trips.db"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS gps_track (
            id INTEGER PRIMARY KEY,
            ts TEXT,
            lat REAL,
            lon REAL,
            speed_knots REAL,
            heading REAL
        )
    """)
    conn.commit()

def parse_gprmc(sentence):
    """Parse $GPRMC NMEA sentence → dict or None."""
    parts = sentence.split(",")
    if len(parts) < 10 or parts[2] != "A":
        return None
    def dm_to_dec(val, hemi):
        d, m = int(val[:2 if hemi in "NS" else 3]), float(val[2 if hemi in "NS" else 3:])
        dec = d + m / 60
        return -dec if hemi in "SW" else dec
    return {
        "ts":    datetime.datetime.utcnow().isoformat(),
        "lat":   dm_to_dec(parts[3], parts[4]),
        "lon":   dm_to_dec(parts[5], parts[6]),
        "speed_knots": float(parts[7]) if parts[7] else 0.0,
        "heading":     float(parts[8]) if parts[8] else 0.0,
    }

def main():
    conn = sqlite3.connect(DB)
    init_db(conn)
    gps  = serial.Serial(GPS_PORT, 9600, timeout=1)
    print("GPS logger running…")
    try:
        while True:
            line = gps.readline().decode("ascii", errors="ignore").strip()
            if line.startswith("$GPRMC"):
                fix = parse_gprmc(line)
                if fix:
                    conn.execute(
                        "INSERT INTO gps_track(ts,lat,lon,speed_knots,heading)"
                        " VALUES(:ts,:lat,:lon,:speed_knots,:heading)", fix)
                    conn.commit()
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        gps.close()

if __name__ == "__main__":
    main()
