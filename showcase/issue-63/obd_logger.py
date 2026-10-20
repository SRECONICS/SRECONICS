#!/usr/bin/env python3
"""Poll OBD-II via python-OBD every 500 ms and log to SQLite."""
import obd, sqlite3, time, datetime

DB = "trips.db"

def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY,
            ts TEXT,
            rpm REAL,
            speed REAL,
            coolant_temp REAL,
            throttle REAL,
            dtc TEXT
        )
    """)
    conn.commit()

def main():
    conn   = sqlite3.connect(DB)
    init_db(conn)
    car    = obd.OBD()                     # auto-connects to ELM327
    cmds   = [obd.commands.RPM, obd.commands.SPEED,
              obd.commands.COOLANT_TEMP, obd.commands.THROTTLE_POS]
    print("Logging — press Ctrl+C to stop")
    try:
        while True:
            row = {"ts": datetime.datetime.utcnow().isoformat()}
            for cmd in cmds:
                r = car.query(cmd)
                row[cmd.name.lower()] = r.value.magnitude if not r.is_null() else None
            dtc_r = car.query(obd.commands.GET_DTC)
            row["dtc"] = str(dtc_r.value) if not dtc_r.is_null() else ""
            conn.execute(
                "INSERT INTO telemetry(ts,rpm,speed,coolant_temp,throttle,dtc)"
                " VALUES(:ts,:rpm,:speed,:coolant_temp,:throttle_pos,:dtc)", row)
            conn.commit()
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()

if __name__ == "__main__":
    main()
