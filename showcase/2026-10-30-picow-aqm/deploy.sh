# deploy.sh  — flash firmware and upload files to Pico W via mpremote
# Usage:  bash deploy.sh
# Requires: mpremote (pip install mpremote)

set -e
PORT=${PICO_PORT:-/dev/ttyACM0}   # change to COMx on Windows

echo "==> Uploading config and main …"
mpremote connect $PORT mkdir lib 2>/dev/null || true
mpremote connect $PORT cp config.py :config.py
mpremote connect $PORT cp main.py   :main.py

echo "==> Uploading sensor/driver libs …"
mpremote connect $PORT cp lib/scd40.py    :lib/scd40.py
mpremote connect $PORT cp lib/sgp30.py    :lib/sgp30.py
mpremote connect $PORT cp lib/pms5003.py  :lib/pms5003.py
mpremote connect $PORT cp lib/ssd1306.py  :lib/ssd1306.py
mpremote connect $PORT cp lib/mqtt.py     :lib/mqtt.py

echo "==> Resetting Pico W …"
mpremote connect $PORT reset

echo "Done!  Monitor output:"
mpremote connect $PORT repl
