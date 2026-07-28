"""
Static content model for the daily project-posting pipeline.

BOARD_ROTATION defines the 6-day cycle order. Each board carries a curated
pool of CORE_IDEAS (realistic projects that fit its actual capabilities) and
shares a common pool of TWISTS (feature variations). The generator combines
one core idea with one twist to produce a project post, which multiplies the
number of unique posts per board well beyond the curated idea count while
keeping every combination technically coherent.
"""

# Twists are generic feature modifiers applied on top of a core idea. Each
# twist appends a short description sentence, may add components/tags, and
# appends a short suffix to the title.
TWISTS = [
    {
        "id": "cloud-dashboard",
        "title_suffix": "Cloud Dashboard Edition",
        "sentence": "Telemetry is pushed to a cloud dashboard (Grafana/ThingSpeak-style) so the system can be monitored and tuned remotely.",
        "extra_components": ["Cloud MQTT broker / HTTP endpoint"],
        "extra_tags": ["cloud"],
    },
    {
        "id": "offline-first",
        "title_suffix": "Offline-First Edition",
        "sentence": "All logic runs locally with no cloud dependency, so it keeps working through internet outages or in network-dead zones.",
        "extra_components": ["Local storage (SD card / flash)"],
        "extra_tags": ["edge computing"],
    },
    {
        "id": "solar-powered",
        "title_suffix": "Solar-Powered Edition",
        "sentence": "A small solar panel and LiPo charge controller keep it running unattended for weeks, which matters for anything mounted outdoors.",
        "extra_components": ["Solar panel + LiPo charge controller"],
        "extra_tags": ["sustainable tech"],
    },
    {
        "id": "mesh-networked",
        "title_suffix": "Mesh-Networked Edition",
        "sentence": "Multiple units talk to each other over a lightweight mesh link, so coverage scales by adding nodes instead of rewiring anything.",
        "extra_components": ["Mesh radio link (ESP-NOW / nRF24 / BLE mesh)"],
        "extra_tags": ["wireless sensing"],
    },
    {
        "id": "voice-alert",
        "title_suffix": "Voice-Alert Edition",
        "sentence": "Status changes trigger a spoken alert through a small speaker, which is a lot harder to miss than a dashboard notification.",
        "extra_components": ["Small speaker / audio amp module"],
        "extra_tags": ["accessibility"],
    },
    {
        "id": "mobile-app",
        "title_suffix": "Mobile App Edition",
        "sentence": "A companion phone app talks to the board over BLE/WiFi for live status and manual override, no laptop required.",
        "extra_components": ["BLE/WiFi companion app link"],
        "extra_tags": ["mobile integration"],
    },
    {
        "id": "predictive-maintenance",
        "title_suffix": "Predictive Maintenance Edition",
        "sentence": "A lightweight trend check on recent readings flags drift before it becomes a failure, instead of only reacting after something breaks.",
        "extra_components": ["Rolling-average / threshold trend logic"],
        "extra_tags": ["predictive maintenance"],
    },
    {
        "id": "multi-sensor-fusion",
        "title_suffix": "Multi-Sensor Fusion Edition",
        "sentence": "A second sensing modality is fused with the primary signal, cutting down false triggers that a single sensor alone would miss.",
        "extra_components": ["Secondary sensor for cross-validation"],
        "extra_tags": ["sensor fusion"],
    },
    {
        "id": "fail-safe",
        "title_suffix": "Fail-Safe Edition",
        "sentence": "A watchdog timer and a defined power-loss behavior make sure the system fails to a safe state instead of hanging silently.",
        "extra_components": ["Watchdog timer / backup power path"],
        "extra_tags": ["reliability engineering"],
    },
    {
        "id": "data-logger",
        "title_suffix": "Data Logger Edition",
        "sentence": "Every reading is timestamped and logged locally, giving a historical trend view instead of just a live snapshot.",
        "extra_components": ["Real-time clock (RTC) + logging storage"],
        "extra_tags": ["data logging"],
    },
]

BOARDS = [
    {
        "key": "pico_w",
        "name": "Raspberry Pi Pico W",
        "tier": "Microcontroller (RP2040, dual-core Cortex-M0+, WiFi + BLE)",
        "board_tag": "microcontrollers",
        "accent": "#8ED6FF",
        "self_refs": ["Pico W"],
        "core_ideas": [
            {
                "title": "Wireless Soil Moisture & Irrigation Trigger",
                "focus": "A capacitive soil moisture probe feeds the Pico W's ADC, and once readings drop below a calibrated threshold it fires a relay-driven pump for a set duration. Readings are pushed to an MQTT topic every few minutes over the built-in WiFi radio. It's useful for anyone tired of either overwatering potted plants or forgetting them entirely, especially over a long weekend.",
                "components": ["Capacitive soil moisture sensor", "5V relay module", "Small DC water pump", "Pico W (RP2040)"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "BLE Beacon Indoor Asset Tracker",
                "focus": "The Pico W broadcasts a periodic BLE advertisement carrying an ID and battery level, and a handful of stationary receiver nodes log signal strength to estimate which room the tagged object is in. Deep sleep between broadcasts stretches battery life to months on a coin cell. It's a low-cost alternative to commercial BLE tags for tracking tools, bags, or lab equipment around a building.",
                "components": ["Pico W (RP2040)", "Coin cell battery holder", "BLE receiver nodes (3+)"],
                "tags": ["IoT", "wireless sensing"],
            },
            {
                "title": "Smart Doorbell with PIR + WiFi Push Alert",
                "focus": "A PIR sensor wakes the Pico W from deep sleep when someone approaches the door, a piezo buzzer chimes locally, and an HTTP request fires a push notification via a free notification service. Because the whole thing sleeps between events, it runs comfortably off a small battery pack. It's a cheap way to get doorbell alerts on a phone without buying into a subscription camera ecosystem.",
                "components": ["PIR motion sensor", "Piezo buzzer", "Pico W (RP2040)", "LiPo battery + charge circuit"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Solar Weather Station Node",
                "focus": "A BME280 handles temperature/humidity/pressure while a tipping-bucket rain gauge and a reed-switch anemometer cover precipitation and wind speed, all polled on a duty cycle to save power. Data batches upload over WiFi once an hour before the board drops back to deep sleep. It gives a hobbyist a genuinely useful hyperlocal weather feed instead of relying on the nearest airport station.",
                "components": ["BME280 sensor", "Tipping-bucket rain gauge", "Reed-switch anemometer", "Pico W (RP2040)"],
                "tags": ["IoT", "environmental monitoring"],
            },
            {
                "title": "WiFi-Synced Ambient LED Status Display",
                "focus": "The Pico W polls a weather API or a home-automation status endpoint over WiFi and drives a WS2812 LED strip through its PIO block to render color-coded ambient info (rain incoming, meeting in progress, air quality). Using PIO instead of bit-banging keeps the CPU free for networking. It's a genuinely useful ambient-computing display for a desk or hallway.",
                "components": ["WS2812 addressable LED strip", "Pico W (RP2040)", "5V power supply"],
                "tags": ["home automation", "IoT"],
            },
            {
                "title": "Contactless Sanitizer Dispenser with Usage Logging",
                "focus": "An ultrasonic distance sensor detects a hand under the nozzle and triggers a small pump for a fixed dose, while the Pico W logs each dispense event with a timestamp over WiFi. It's aimed at shared spaces (labs, classrooms) where touch-free dispensing and usage auditing both matter. The whole build fits in a 3D-printed housing the size of a coffee mug.",
                "components": ["Ultrasonic distance sensor (HC-SR04)", "Small DC dosing pump", "Pico W (RP2040)"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Vibration-Based Predictive Maintenance Sensor",
                "focus": "An accelerometer sampled at a few hundred Hz feeds a lightweight on-device magnitude/variance check (a full FFT is overkill on RP2040, but a rolling-window energy estimate works well) to flag abnormal vibration on a motor or pump. Alerts fire over WiFi before a bearing fully fails. It's a practical entry point into condition-based monitoring without needing a PLC or industrial sensor budget.",
                "components": ["3-axis accelerometer (MPU6050/ADXL345)", "Pico W (RP2040)", "Mounting bracket"],
                "tags": ["IoT", "predictive maintenance"],
            },
            {
                "title": "Occupancy Counter for Shared Spaces",
                "focus": "Paired PIR and ultrasonic sensors at a doorway distinguish entry from exit direction, letting the Pico W maintain a live occupancy count for a meeting room or makerspace. The count is exposed over WiFi as a small JSON endpoint any dashboard can poll. It solves the very real 'is this room actually free' problem cheaply.",
                "components": ["2x PIR motion sensors", "Ultrasonic distance sensor", "Pico W (RP2040)"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Smart Plug with Current Sensing",
                "focus": "An INA219 current/power sensor sits between a relay and the load, letting the Pico W both switch an appliance and log exactly how much power it draws over time via WiFi. This turns a dumb relay into something that can catch a fridge drawing more current than it should, or confirm a load actually turned off. It's a genuinely useful building block for home energy audits.",
                "components": ["INA219 current/power sensor", "5V relay module", "Pico W (RP2040)"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Aquarium/Hydroponics Environment Monitor",
                "focus": "Waterproof DS18B20 temperature probes and a pH sensor module are polled continuously, with the Pico W pushing readings over WiFi and firing an alert if either drifts outside a safe band. For anyone running an aquarium or a hydroponics setup, catching a heater failure or pH swing within minutes instead of a day later can save the whole tank or crop. It's a small board doing a job that otherwise means checking manually every few hours.",
                "components": ["Waterproof DS18B20 temp probe", "Analog pH sensor module", "Pico W (RP2040)"],
                "tags": ["IoT", "environmental monitoring"],
            },
            {
                "title": "Line-Following Robot Base Controller",
                "focus": "A 5-channel IR reflectance array feeds a simple PID loop running on one Pico W core while the other handles WiFi telemetry, driving a two-motor chassis through an H-bridge driver. Splitting control and networking across the two RP2040 cores keeps the motor loop jitter-free even while streaming status. It's a solid, well-instrumented base for a robotics club's first line-follower.",
                "components": ["5-channel IR reflectance array", "Dual-motor H-bridge driver", "2x DC gear motors", "Pico W (RP2040)"],
                "tags": ["robotics", "IoT"],
            },
            {
                "title": "Wireless Door/Window Security Sensor Node",
                "focus": "A reed switch on each door/window reports open/close state to the Pico W, which forwards state changes over WiFi to a central hub with minimal latency and near-zero idle power draw thanks to deep sleep between events. Battery life comfortably exceeds a year on a single 18650 cell. It's a DIY alternative to commercial security sensors that dodges any subscription fee.",
                "components": ["Reed switch (magnetic contact sensor)", "18650 battery + holder", "Pico W (RP2040)"],
                "tags": ["IoT", "home automation"],
            },
        ],
    },
    {
        "key": "pi_zero2w",
        "name": "Raspberry Pi Zero 2 W",
        "tier": "Quad-core Linux SBC (WiFi + BT, camera connector, small form factor)",
        "board_tag": "single-board-computers",
        "accent": "#C51A4A",
        "self_refs": ["Pi Zero 2 W"],
        "core_ideas": [
            {
                "title": "Pet Feeding & Monitoring Camera",
                "focus": "A camera module streams live video to a small web dashboard while a servo-driven hopper dispenses a measured portion of food on a schedule or on remote trigger. Because the Zero 2 W has enough headroom to run a lightweight web server and encode a video stream simultaneously, the whole feeder plus monitor fits on one board. It's a practical build for checking on a pet during a long day at work.",
                "components": ["Raspberry Pi Camera Module", "Servo-driven food hopper", "Pi Zero 2 W"],
                "tags": ["IoT", "computer vision"],
            },
            {
                "title": "Doorbell Camera with Familiar-Face Alerting",
                "focus": "A PIR sensor wakes the camera pipeline only when motion is detected, and a lightweight face-embedding comparison distinguishes 'known household member' from 'unknown visitor' before sending a push notification. Running the check only on motion (instead of continuously) keeps CPU load and heat manageable on the Zero 2 W. It gives a genuinely useful heads-up without the always-on cloud processing of commercial doorbell cameras.",
                "components": ["Raspberry Pi Camera Module", "PIR motion sensor", "Pi Zero 2 W"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Mini Network Backup Node",
                "focus": "A USB drive attached to the Zero 2 W runs a Samba share and a scheduled rsync job that mirrors a folder from every machine on the home network overnight. It's not fast, but it's silent, low-power, and always on, which makes it a genuinely reliable always-there backup target rather than a NAS that gets left off. Good project for learning real Linux service management (systemd timers, Samba config) on constrained hardware.",
                "components": ["USB flash drive / small SSD", "USB-to-SD or USB hub", "Pi Zero 2 W"],
                "tags": ["home automation"],
            },
            {
                "title": "Time-Lapse Garden Growth Camera",
                "focus": "The camera module captures a still frame on a cron schedule (e.g. every 15 minutes during daylight) and stitches the day's frames into a time-lapse clip automatically overnight. Weatherproofing the enclosure is half the build. It turns a season of plant growth into a shareable clip without a dedicated time-lapse camera.",
                "components": ["Raspberry Pi Camera Module", "Weatherproof enclosure", "Pi Zero 2 W"],
                "tags": ["computer vision", "IoT"],
            },
            {
                "title": "Wildlife Camera Trap",
                "focus": "A PIR sensor triggers a burst capture from the camera module, and the Zero 2 W tags each capture with a timestamp before saving to SD (or pushing over WiFi if in range). Deep sleep between triggers and a battery pack let it run unattended in a yard or on a trail for days. It's a fraction of the cost of a commercial trail camera with full control over capture logic.",
                "components": ["Raspberry Pi Camera Module", "PIR motion sensor", "Battery pack", "Pi Zero 2 W"],
                "tags": ["computer vision", "environmental monitoring"],
            },
            {
                "title": "Room Sound-Level & Baby Monitor",
                "focus": "A microphone module continuously measures ambient sound level, and the Zero 2 W streams audio (and optionally video) only when the level crosses a threshold, notifying a parent's phone. Streaming on-demand rather than continuously saves both bandwidth and battery if running off a power bank. It's a privacy-respecting alternative to always-on commercial baby monitors since nothing leaves the house.",
                "components": ["I2S/USB microphone module", "Raspberry Pi Camera Module (optional)", "Pi Zero 2 W"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Smart Mirror Info Display",
                "focus": "A two-way mirror sits over a small display driven by the Zero 2 W, showing time, weather, and calendar info pulled over WiFi, while the camera module can detect 'someone standing in front of the mirror' to wake the display from a blank/idle state. It's a classic hobbyist build, but the Zero 2 W's small footprint makes it much easier to fit behind a thin mirror frame than a full-size Pi.",
                "components": ["Small HDMI display", "Two-way acrylic mirror", "Raspberry Pi Camera Module", "Pi Zero 2 W"],
                "tags": ["home automation", "computer vision"],
            },
            {
                "title": "Package Delivery Detection Camera",
                "focus": "Motion at the doorstep triggers a snapshot, and a simple frame-difference check (comparing against a reference 'empty porch' image) flags when a new object has appeared, sending an alert with the photo attached. It avoids the false positives of pure motion detection (passing cars, moving shadows) without needing a full object-detection model. Genuinely useful for catching porch theft or just knowing a package arrived.",
                "components": ["Raspberry Pi Camera Module", "PIR motion sensor", "Pi Zero 2 W"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Portable WiFi Network Scanner",
                "focus": "The Zero 2 W's WiFi radio in monitor mode passively logs nearby access points and can flag an unexpected SSID spoofing a known network (a classic rogue-AP / evil-twin indicator), displaying results on a small OLED. It's a compact, battery-friendly tool for basic wireless awareness during authorized network audits or just understanding what's actually broadcasting nearby. Built for educational and authorized-testing use only.",
                "components": ["Small OLED display (I2C)", "Pi Zero 2 W (onboard WiFi)", "Battery pack"],
                "tags": ["IoT"],
            },
            {
                "title": "Gate/Driveway OCR Access Log",
                "focus": "The camera captures a frame when a vehicle triggers a driveway sensor, and an OCR pass extracts the plate text to check against a small allow-list before logging the event with a timestamp. It's built as a personal access log/notifier rather than a security gate, since OCR accuracy varies with lighting. Still a genuinely fun way to combine a camera, a sensor, and text recognition into a single working pipeline.",
                "components": ["Raspberry Pi Camera Module", "Driveway motion/pressure sensor", "Pi Zero 2 W"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Solar Trail-Counter for Hiking Groups",
                "focus": "A PIR-triggered camera logs a low-res thumbnail and timestamp each time someone passes a trail marker, with a small solar panel and battery keeping it running for a season without a battery swap. Data syncs over WiFi whenever the unit is in range of a hotspot at the trailhead. It gives a hiking club real foot-traffic data instead of guesswork.",
                "components": ["Raspberry Pi Camera Module", "PIR motion sensor", "Solar panel + battery", "Pi Zero 2 W"],
                "tags": ["computer vision", "environmental monitoring"],
            },
            {
                "title": "Retro Handheld Emulation Console",
                "focus": "A small display, a button matrix, and a battery pack turn the Zero 2 W into a pocket-sized retro console running lightweight emulators, with the quad-core CPU giving enough headroom for older 8/16-bit era systems. It's one of the most approachable ways to learn Linux input handling (GPIO buttons mapped to a joypad driver) while building something genuinely fun to use. A great low-stakes first hardware project for a robotics or maker club member.",
                "components": ["Small HDMI/SPI display", "Button matrix / game controller HAT", "Battery pack", "Pi Zero 2 W"],
                "tags": ["robotics"],
            },
        ],
    },
    {
        "key": "pi3",
        "name": "Raspberry Pi 3",
        "tier": "Quad-core Linux SBC (WiFi + Bluetooth, general-purpose home automation / robotics hub)",
        "board_tag": "single-board-computers",
        "accent": "#75A928",
        "self_refs": ["Raspberry Pi 3"],
        "core_ideas": [
            {
                "title": "Central Home Automation Hub",
                "focus": "A Zigbee USB dongle plugged into the Pi 3 lets it talk directly to cheap Zigbee sensors and smart plugs, with an MQTT broker running locally to tie everything together without depending on any vendor's cloud. This is the classic 'take back your smart home from the cloud' build, and the Pi 3 has exactly enough headroom to run the broker plus a rules engine comfortably. It's genuinely more reliable than most consumer hubs because there's no vendor server to go down.",
                "components": ["Zigbee USB dongle", "MQTT broker (Mosquitto)", "Zigbee smart plugs/sensors", "Raspberry Pi 3"],
                "tags": ["home automation", "IoT"],
            },
            {
                "title": "Offline Voice-Controlled Room Assistant",
                "focus": "A USB microphone array feeds an on-device wake-word engine, and once triggered, simple intents (\"turn on the lights\", \"what's the temperature\") get parsed locally and dispatched to MQTT-connected devices, with a small speaker confirming the action. Keeping wake-word and intent parsing fully offline sidesteps the privacy concerns of cloud voice assistants. It's a satisfying project because you hear it actually respond to your own voice, on hardware you control end to end.",
                "components": ["USB microphone array", "Small speaker + amp", "MQTT-connected smart plugs", "Raspberry Pi 3"],
                "tags": ["home automation", "accessibility"],
            },
            {
                "title": "Multi-Zone Irrigation Controller",
                "focus": "The Pi 3 drives a bank of relays controlling separate irrigation valves, and cross-references a free weather API so it skips a scheduled watering if rain already fell or is forecast. Each zone gets its own schedule, tuned to what's actually planted there rather than one blanket timer. It saves real water and plant health versus a basic mechanical irrigation timer.",
                "components": ["8-channel relay module", "Solenoid irrigation valves", "Raspberry Pi 3"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "RFID Access Control Door Lock",
                "focus": "An RFID reader at the door checks presented tags against a small local database before driving an electric strike through a relay, and every attempt (successful or not) gets logged with a timestamp. Running the check locally means the lock keeps working even if the home network is down. It's a genuinely solid intro to access-control systems: reader hardware, a database, and an actuator all in one afternoon build.",
                "components": ["RFID reader (RC522/PN532)", "Electric door strike + relay", "Raspberry Pi 3"],
                "tags": ["home automation", "IoT"],
            },
            {
                "title": "Home Energy Monitoring Dashboard",
                "focus": "Non-invasive CT clamp sensors around the main incoming lines let the Pi 3 measure whole-home power draw without touching any wiring, feeding a local dashboard that breaks usage into rough per-circuit estimates. Because it's completely local, there's no per-device subscription like commercial energy monitors charge. Seeing where power actually goes tends to change behavior fast, which is the whole point.",
                "components": ["CT clamp current sensors", "ADC breakout (ADS1115)", "Raspberry Pi 3"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Line-Following & Obstacle-Avoiding Robot",
                "focus": "An IR reflectance array handles line-following while an ultrasonic sensor overrides steering to dodge unexpected obstacles, with the Pi 3's extra headroom (versus a bare microcontroller) leaving room to log runs and stream a status feed over WiFi. It's a step up from a Pico-based line follower because the Pi 3 can run real logging and even a lightweight camera-based check alongside the core control loop. A strong club-level robotics platform.",
                "components": ["IR reflectance array", "Ultrasonic distance sensor", "Motor driver + DC motors", "Raspberry Pi 3"],
                "tags": ["robotics"],
            },
            {
                "title": "Smart Mailbox Notifier",
                "focus": "A reed switch on the mailbox flap and a small camera combine to detect and photograph new mail, pushing a notification with the snapshot the moment the flap opens. Running on the Pi 3 (rather than a bare microcontroller) makes it trivial to also run a small web endpoint showing the last few captures. Solves the very real 'did the mail come yet' problem without walking outside.",
                "components": ["Reed switch", "Raspberry Pi Camera Module", "Battery pack", "Raspberry Pi 3"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "LAN-Only Room Intercom",
                "focus": "Multiple Pi 3 units on the same LAN each run a small audio server, letting a push-to-talk button on one broadcast to a speaker on another, entirely over the local network with no cloud service in the loop. It's a good hands-on introduction to real-time audio streaming and multicast networking. Useful for a workshop, garage, or multi-floor house where shouting doesn't reach.",
                "components": ["USB microphone", "Small speaker + amp", "Push-to-talk button", "Raspberry Pi 3 (per node)"],
                "tags": ["home automation", "IoT"],
            },
            {
                "title": "Automated Pet Door with Collar-Tag Recognition",
                "focus": "An RFID reader mounted at a pet door checks for an authorized collar tag before releasing a servo-driven latch, keeping neighborhood animals out while letting the household pet through freely. Event logs make it easy to see how often (and when) the pet actually uses the door. It's a genuinely more secure alternative to purely magnetic pet-door locks that any similarly-tagged animal could open.",
                "components": ["RFID reader + collar tag", "Servo-driven door latch", "Raspberry Pi 3"],
                "tags": ["IoT", "home automation"],
            },
            {
                "title": "Air Quality & CO2 Monitoring Station",
                "focus": "An NDIR CO2 sensor alongside a PM2.5 particulate sensor gives the Pi 3 enough data to flag both stuffy-room CO2 buildup and general air quality, with a local dashboard showing trends over days and weeks. It directly informs when to crack a window versus when it's dust/smoke driving the numbers. A practical, data-backed upgrade over guessing based on how a room 'feels'.",
                "components": ["NDIR CO2 sensor", "PM2.5 particulate sensor", "Raspberry Pi 3"],
                "tags": ["environmental monitoring", "IoT"],
            },
            {
                "title": "Gesture-Controlled Room Lighting",
                "focus": "An IR gesture sensor near a light switch recognizes a handful of swipe gestures (up, down, left, right) and maps them to relay-controlled lighting scenes, giving touchless control without any voice assistant in the loop. It's aimed at kitchens or workshops where hands are often full or dirty. The gesture sensor's onboard proximity detection also acts as a simple occupancy cue for auto-off.",
                "components": ["IR gesture sensor (APDS-9960)", "Relay module", "Raspberry Pi 3"],
                "tags": ["home automation"],
            },
            {
                "title": "Automated Plant-Care Watering Arm",
                "focus": "A capacitive soil sensor tells the Pi 3 which of several potted plants needs water, and a small 2-axis arm positions a watering nozzle over the right pot before dispensing a measured amount. It's a fun step past a single-plant auto-waterer into small-scale robotic positioning. Genuinely solves the 'watered the wrong plant twice, forgot the other one' problem that comes with more than a couple houseplants.",
                "components": ["Capacitive soil sensor (per plant)", "2-axis servo arm", "Small water pump", "Raspberry Pi 3"],
                "tags": ["robotics", "home automation"],
            },
        ],
    },
    {
        "key": "pi4",
        "name": "Raspberry Pi 4",
        "tier": "Quad-core Linux SBC (USB3, dual display, more compute headroom for local servers / light vision)",
        "board_tag": "single-board-computers",
        "accent": "#A22846",
        "self_refs": ["Raspberry Pi 4"],
        "core_ideas": [
            {
                "title": "Local Multi-Camera NVR with Motion Zones",
                "focus": "Several IP or USB cameras feed into a Pi 4 running a local network video recorder with configurable motion-detection zones per camera, so a tree swaying in the wind doesn't trigger the same alert as someone walking up the driveway. USB3 throughput on the Pi 4 is what makes handling multiple simultaneous streams practical. It replaces a subscription NVR service with something that keeps every clip on hardware you own.",
                "components": ["2-4x IP/USB cameras", "USB3 SSD for storage", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Real-Time Object-Detection Doorbell",
                "focus": "A TensorFlow Lite model running on the Pi 4's CPU classifies what triggered the doorbell camera (person, package, vehicle, animal) before deciding whether to send a notification, cutting down the noisy 'motion detected' alerts of a plain PIR-based doorbell. The Pi 4 has enough headroom to run this inference in close to real time without a separate accelerator. It's a genuinely more useful alert than 'something moved'.",
                "components": ["Raspberry Pi Camera Module", "TensorFlow Lite object-detection model", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Self-Hosted Smart Home Automation Server",
                "focus": "The Pi 4 runs a full home-automation server (Home Assistant-style) tying together Zigbee, WiFi, and MQTT devices behind a single dashboard and automation-rule engine, entirely on the local network. It's the natural upgrade path from a Pi 3 MQTT hub once the number of devices and automations grows past what a bare broker comfortably handles. Genuinely the most practical 'own your smart home' project on this list.",
                "components": ["Zigbee/Z-Wave USB dongle", "USB3 SSD for storage", "Raspberry Pi 4"],
                "tags": ["home automation", "IoT"],
            },
            {
                "title": "Vision-Guided Line-Maze Solving Robot",
                "focus": "Instead of a plain IR reflectance array, the Pi 4 uses a downward-facing camera and a lightweight image-processing pipeline (thresholding + centroid tracking) to follow a line and detect junctions, letting it make maze-solving decisions a fixed sensor array can't. The extra compute over a Pi 3 is what keeps the vision loop fast enough for real-time steering. It's a strong step from 'follows a line' to 'actually reasons about the maze'.",
                "components": ["Raspberry Pi Camera Module", "Motor driver + DC motors", "Chassis", "Raspberry Pi 4"],
                "tags": ["robotics", "computer vision"],
            },
            {
                "title": "Pose-Controlled Smart TV Remote",
                "focus": "A webcam and a lightweight pose-estimation model translate hand gestures (swipe, palm-up, fist) into media-control commands sent to a TV or media center over the network, so 'turn up the volume' doesn't require finding a remote. Pose estimation is squarely in the compute range the Pi 4 can handle without a dedicated accelerator. A genuinely fun demo project that also teaches real applied computer vision.",
                "components": ["USB webcam", "Pose-estimation model (MediaPipe-style)", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Multi-Room Audio & Announcement System",
                "focus": "Several Pi 4 units run a synchronized audio server so music plays in-step across rooms, and any node can interrupt playback with a spoken announcement (e.g., 'dinner's ready') broadcast to the whole house. Getting playback sync tight across nodes is the interesting engineering problem here. It's a genuinely nicer whole-home audio experience than a single Bluetooth speaker, built entirely from boards already on the shelf.",
                "components": ["DAC HAT / USB audio", "Speakers (per room)", "Raspberry Pi 4 (per node)"],
                "tags": ["home automation"],
            },
            {
                "title": "On-Device LLM Voice Assistant for Home Control",
                "focus": "A small quantized language model runs locally on the Pi 4 to parse loosely-phrased voice commands ('it's a bit warm in here') into concrete device actions, going well beyond the rigid keyword matching of a basic voice hub. Running the model on-device means commands never leave the house. It's an ambitious but genuinely achievable edge-AI project given how far small quantized models have come.",
                "components": ["USB microphone", "Quantized local LLM (GGUF-format)", "Raspberry Pi 4"],
                "tags": ["home automation", "edge AI"],
            },
            {
                "title": "Warehouse/Shelf Inventory Scanner Robot",
                "focus": "A camera-equipped rover reads barcodes/QR codes off shelf labels while driving a preset route, cross-checking against an expected inventory list and flagging missing or misplaced items. It's a scaled-down version of the kind of inventory robot warehouses actually deploy, and a great applied-vision project for a robotics club with retail/logistics interests. The Pi 4's compute is what makes real-time barcode decoding while moving practical.",
                "components": ["Raspberry Pi Camera Module", "Barcode/QR decoding library", "Motor driver + chassis", "Raspberry Pi 4"],
                "tags": ["robotics", "computer vision"],
            },
            {
                "title": "Face-Recognition Attendance Kiosk",
                "focus": "A camera at the entrance of a classroom or lab matches faces against a small enrolled database and logs attendance automatically, replacing a paper sign-in sheet. Running recognition locally (rather than a cloud API) keeps biometric data on hardware the institution controls, which matters for student privacy. It's a genuinely deployable project for a student org or small lab, not just a demo.",
                "components": ["Raspberry Pi Camera Module", "Face-recognition library (dlib/face_recognition)", "Small display", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Vision-Assisted Automated Greenhouse Controller",
                "focus": "Alongside standard temperature/humidity/soil sensors, a camera periodically captures leaf images and runs a simple color/texture check to flag early signs of stress (wilting, discoloration) before it's obvious to a casual glance. Actuators (vents, misters, grow lights) respond to both the sensor readings and the vision check. It pushes a normal greenhouse controller from reactive to actually a little bit predictive.",
                "components": ["Multi-sensor array (temp/humidity/soil)", "Raspberry Pi Camera Module", "Relay-driven actuators", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "Real-Time License Plate Gate Controller",
                "focus": "A camera at a gate or barrier runs an ANPR (automatic number-plate recognition) pipeline to check incoming vehicles against an allow-list before triggering a relay-driven gate motor, logging every attempt with a snapshot. The Pi 4's compute headroom keeps recognition latency low enough that a car doesn't have to stop and wait long. A genuinely useful access-control project for a driveway, small lot, or community gate.",
                "components": ["Raspberry Pi Camera Module", "ANPR/OCR pipeline", "Relay-driven gate motor", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
            {
                "title": "3D Printer/CNC Local Monitoring Server",
                "focus": "The Pi 4 runs a local print-farm dashboard (OctoPrint-style) with a webcam feed per machine, tracking print progress and flagging failures (like a spaghetti print) via a simple frame-difference check against the expected model silhouette. Keeping it fully local avoids routing print files and camera feeds through a third-party cloud service. A genuinely practical project for anyone running more than one printer or CNC machine.",
                "components": ["USB webcam (per machine)", "USB3 SSD for storage", "Raspberry Pi 4"],
                "tags": ["computer vision", "home automation"],
            },
        ],
    },
    {
        "key": "pi5",
        "name": "Raspberry Pi 5",
        "tier": "Highest-compute Linux SBC (PCIe, fastest CPU, best fit for edge AI / vision / robotics)",
        "board_tag": "single-board-computers",
        "accent": "#00979D",
        "self_refs": ["Raspberry Pi 5"],
        "core_ideas": [
            {
                "title": "Real-Time Multi-Object Tracking Security Camera",
                "focus": "A PCIe-attached AI accelerator hat paired with the Pi 5's faster CPU runs a real-time multi-object tracker (not just detection) across a camera feed, keeping consistent IDs on people and vehicles as they move through frame. That distinction (tracking vs. one-shot detection) is what lets it report 'a person lingered near the door for 4 minutes' instead of just 'motion detected'. It's the kind of behavior-aware alerting that used to require commercial security-grade hardware.",
                "components": ["Raspberry Pi Camera Module 3", "PCIe AI accelerator HAT", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Autonomous Indoor Delivery Robot",
                "focus": "A depth camera feeds a lightweight SLAM-style mapping and obstacle-avoidance stack, letting the robot navigate a known indoor route (office to break room, say) without a human driving it. The Pi 5's CPU/PCIe headroom is genuinely the difference between this running smoothly versus stuttering on older Pi boards. It's an ambitious but realistic robotics capstone project.",
                "components": ["Depth camera (stereo or ToF)", "Motor driver + differential-drive chassis", "Wheel encoders", "Raspberry Pi 5"],
                "tags": ["robotics", "computer vision"],
            },
            {
                "title": "Edge-AI Quality-Inspection Camera",
                "focus": "A fixed camera over a small assembly line runs an on-device defect-classification model (trained on a handful of good/bad sample images) to flag parts that don't meet spec, in real time, without sending any images off-device. It's a genuinely deployable small-scale version of industrial machine-vision inspection systems that normally cost thousands. A strong project for anyone interested in manufacturing/industrial edge AI.",
                "components": ["Raspberry Pi Camera Module", "PCIe AI accelerator HAT", "Conveyor/fixture rig", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Real-Time Sign Language Recognition Assistant",
                "focus": "A camera and an on-device hand-landmark model translate a set of sign-language gestures into on-screen text or synthesized speech in real time, running entirely locally for both latency and privacy reasons. The Pi 5's extra compute is what keeps frame-to-text latency low enough to feel like a real conversation aid rather than a laggy demo. A genuinely valuable accessibility project.",
                "components": ["Raspberry Pi Camera Module", "Hand-landmark model (MediaPipe-style)", "Small speaker", "Raspberry Pi 5"],
                "tags": ["computer vision", "accessibility"],
            },
            {
                "title": "Privacy-Preserving Fall-Detection Camera",
                "focus": "An on-device pose-estimation model watches for the specific motion signature of a fall (rapid vertical drop + prolonged horizontal pose) and alerts a caregiver, without ever streaming raw video off the device, addressing the biggest privacy objection to camera-based elder care monitoring. Running the model locally on the Pi 5 rather than in the cloud is the whole point here. A genuinely useful assistive-tech project with real social value.",
                "components": ["Raspberry Pi Camera Module", "Pose-estimation model", "Raspberry Pi 5"],
                "tags": ["computer vision", "accessibility"],
            },
            {
                "title": "High-FPS Visual Servoing for a Robotic Arm",
                "focus": "A camera mounted near a small robotic arm's end effector feeds a fast object-localization loop that continuously corrects the arm's trajectory toward a moving target, rather than following a fixed pre-programmed path. Keeping this loop at a usable frame rate is exactly the kind of workload the Pi 5's extra CPU throughput was built for. It's a hands-on introduction to closed-loop visual servoing, a real robotics research topic, on affordable hardware.",
                "components": ["USB/CSI camera", "Small robotic arm (servo-driven)", "Raspberry Pi 5"],
                "tags": ["robotics", "computer vision"],
            },
            {
                "title": "Edge Node for Pedestrian/Traffic Counting",
                "focus": "A camera overlooking a small intersection or crosswalk runs an on-device detection-and-counting pipeline, logging pedestrian and vehicle counts by time of day without ever recording or transmitting identifiable footage. It's aimed at neighborhood associations or small municipalities that want real traffic data without a full city-scale sensor deployment. The Pi 5 is what makes real-time counting (not just periodic snapshots) practical at this price point.",
                "components": ["Raspberry Pi Camera Module", "Object-detection model", "Weatherproof enclosure", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Autonomous Lawn-Boundary Mapping Rover",
                "focus": "A small rover combines a downward camera, wheel encoders, and a basic GPS module to trace and record a lawn's boundary on a first manual lap, then plans coverage paths for future autonomous mowing runs (the mowing blade itself is left out of scope for safety). The mapping and path-planning math genuinely needs the Pi 5's compute margin to run in real time on a moving platform. A strong, safety-conscious entry point into autonomous ground-vehicle robotics.",
                "components": ["GPS module", "Wheel encoders", "Downward-facing camera", "Raspberry Pi 5"],
                "tags": ["robotics", "computer vision"],
            },
            {
                "title": "Real-Time Crowd Density Estimation Display",
                "focus": "A wide-angle camera over an entrance runs a density-estimation model (rather than trying to count and track every individual, which breaks down in dense crowds) and drives a simple public display showing current occupancy for an event or venue. It's a genuinely useful safety/comfort tool for event organizers, and density estimation is a distinct, more robust technique than per-person tracking at scale. On-device inference means no footage needs to leave the venue's own network.",
                "components": ["Wide-angle camera", "Density-estimation model", "Status display", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Multimodal Voice + Vision Home Assistant",
                "focus": "The Pi 5 runs both a local speech-recognition pipeline and a lightweight vision model simultaneously, so a command like 'turn off whatever I'm pointing at' can combine what it hears with what the camera sees to resolve ambiguity that voice alone can't. Running both models locally and in real time is realistically only feasible on the Pi 5 in this lineup. It's an ambitious but genuinely novel edge-AI project that goes beyond a typical single-modality assistant.",
                "components": ["USB microphone array", "Raspberry Pi Camera Module", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Edge-AI Wildlife Species Classifier Camera Trap",
                "focus": "Unlike a basic motion-triggered trail camera, this one runs an on-device species-classification model right after each trigger, so it can tag captures by species and skip saving/uploading empty or false-trigger frames (blowing leaves, shadows). Running classification on-device rather than uploading everything for cloud processing saves a lot of storage and bandwidth in a remote field deployment. A genuinely useful tool for citizen-science wildlife monitoring projects.",
                "components": ["Raspberry Pi Camera Module", "Species-classification model", "Battery + solar panel", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
            {
                "title": "Local NVR with Real-Time Anomaly Detection",
                "focus": "Beyond simple motion zones, this NVR learns a rough baseline of 'normal' activity per camera (typical times, typical paths) and flags footage that deviates from it, like activity at 3am in a spot that's normally empty. The anomaly model runs entirely on the Pi 5 alongside the recording pipeline itself. It's a meaningfully smarter alerting layer than the motion-zone approach on the Pi 4 build, made possible by the extra headroom.",
                "components": ["2-4x IP/USB cameras", "PCIe AI accelerator HAT", "USB3 SSD", "Raspberry Pi 5"],
                "tags": ["computer vision", "edge AI"],
            },
        ],
    },
    {
        "key": "pynq_z2",
        "name": "PYNQ-Z2 (FPGA)",
        "tier": "Zynq-7020 SoC (ARM Cortex-A9 + programmable logic, HLS-friendly, PYNQ/Python overlay flow)",
        "board_tag": "fpga",
        "accent": "#FF6600",
        "self_refs": ["PYNQ-Z2"],
        "core_ideas": [
            {
                "title": "Custom Conv2D HLS Accelerator for Image Classification",
                "focus": "A convolution layer is hand-written in Vivado HLS and wired into the programmable logic as an AXI-Stream IP core, offloading the heaviest part of a small CNN's inference from the ARM cores onto dedicated hardware. Measured against a pure-software baseline on the same board, this kind of accelerator typically lands a 3-5x speedup at a fraction of the power draw of running it on a GPU. It's the canonical 'why FPGA acceleration matters' demo, and a genuinely strong portfolio piece.",
                "components": ["Vivado HLS Conv2D IP core", "AXI4-Stream DMA", "PYNQ-Z2"],
                "tags": ["FPGA acceleration", "edge AI"],
            },
            {
                "title": "FPGA-Accelerated FFT Spectrum Analyzer",
                "focus": "A streaming FFT core in the programmable logic processes ADC samples (audio or RF) in real time, feeding magnitude spectrum data back to Python running on the ARM side for display, at a throughput a software FFT on the same chip couldn't sustain continuously. It's a solid, self-contained DSP project that shows off exactly what hardware pipelining is for: fixed, predictable per-sample latency. Genuinely useful as a bench tool for audio or RF work, not just a demo.",
                "components": ["Xilinx FFT IP core", "ADC input (Pmod or onboard)", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Hardware AES Core for Secure IoT Gateway",
                "focus": "An AES-128/256 encryption/decryption core implemented directly in programmable logic handles line-rate encryption for data passing through a small IoT gateway running on the PYNQ-Z2's ARM side, freeing the processor entirely from crypto overhead. Doing encryption in fixed hardware also sidesteps a whole category of timing-based software side-channel concerns that software AES implementations have to work around. A strong project for anyone interested in applied hardware security.",
                "components": ["AES HLS/RTL core", "AXI-Lite control interface", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Real-Time Edge-Detection Video Pipeline",
                "focus": "A Sobel or Canny edge-detection pipeline built entirely in programmable logic processes a live camera feed frame-by-frame at full video rate, something a software implementation on the ARM cores alone would struggle to sustain smoothly. Pixels stream through a chain of pipelined HLS stages rather than being buffered and processed frame-at-a-time, which is the core lesson in why streaming architectures matter for video FPGA work. A classic and genuinely instructive PYNQ computer-vision build.",
                "components": ["PYNQ camera/HDMI input", "Sobel/Canny HLS pipeline", "PYNQ-Z2"],
                "tags": ["FPGA acceleration", "computer vision"],
            },
            {
                "title": "Low-Latency PID Motor Control Core",
                "focus": "A PID control loop implemented directly in programmable logic (rather than running as software on the ARM core) drives a motor with microsecond-scale, jitter-free timing that a software loop competing with an OS scheduler can't guarantee. It's a clean demonstration of when hardware control genuinely beats software control: anything where consistent timing matters more than flexibility. A great entry point into hardware-in-the-loop control systems.",
                "components": ["Motor driver + DC/servo motor", "Quadrature encoder", "PID HLS core", "PYNQ-Z2"],
                "tags": ["FPGA acceleration", "robotics"],
            },
            {
                "title": "Hardware QRS Detector for ECG Signal Processing",
                "focus": "A Pan-Tompkins-style QRS detection pipeline (bandpass filter, derivative, squaring, moving-window integration) is implemented as a streaming HLS pipeline in programmable logic, processing an ECG signal in real time to flag heartbeats with consistent low latency. This is squarely the kind of biomedical DSP workload where fixed, deterministic timing genuinely matters. A strong, resume-worthy project bridging FPGA design and biomedical signal processing.",
                "components": ["ECG front-end (AD8232 or similar)", "QRS-detection HLS pipeline", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Custom AXI-Stream Sensor-Fusion DMA Pipeline",
                "focus": "Multiple sensor streams (say, an IMU and an ADC) are merged through a custom AXI-Stream DMA pipeline in programmable logic that timestamp-aligns and interleaves the data before handing a single clean stream to the ARM side, instead of software having to poll and merge each source separately. This offloads a genuinely fiddly synchronization problem onto hardware where it belongs. A great project for understanding how real sensor-fusion systems handle multi-rate data at the hardware level.",
                "components": ["IMU sensor", "ADC input", "Custom AXI-Stream DMA IP", "PYNQ-Z2"],
                "tags": ["FPGA acceleration", "sensor fusion"],
            },
            {
                "title": "FPGA-Based Software-Defined Radio Front-End",
                "focus": "A digital down-converter and channel filter built in programmable logic take raw high-rate ADC samples and produce a much lower-rate baseband stream that Python on the ARM side can process further (demodulation, decoding), splitting the SDR pipeline between what hardware does best (rate reduction) and what software does best (flexible protocol logic). This hardware/software split is exactly how production SDR platforms are architected. A genuinely deep and rewarding RF project.",
                "components": ["RF front-end / ADC (Pmod)", "DDC + filter HLS core", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Hardware RNG & PUF-Based Device Authentication",
                "focus": "A ring-oscillator-based physical unclonable function (PUF) implemented in programmable logic derives a device-unique fingerprint from tiny manufacturing variations in the FPGA fabric itself, paired with a hardware random-number generator for challenge-response authentication that doesn't depend on storing a secret key anywhere. It's a genuinely elegant hardware-security concept: identity derived from physical imperfection rather than a stored value that can be extracted. A strong, discussion-worthy security-focused FPGA project.",
                "components": ["Ring-oscillator PUF core", "Hardware RNG core", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Real-Time Stereo Vision Depth Map Generator",
                "focus": "A stereo block-matching pipeline in programmable logic computes a disparity (depth) map from a synchronized pair of camera feeds in real time, a workload that's notoriously hard to run at full frame rate in pure software on an embedded ARM core. Pipelining the search-and-compare stages in hardware is what keeps this from choking at anything beyond a few frames per second. A genuinely advanced and satisfying FPGA computer-vision build.",
                "components": ["Stereo camera pair", "Block-matching HLS pipeline", "PYNQ-Z2"],
                "tags": ["FPGA acceleration", "computer vision"],
            },
            {
                "title": "Hardware Sort/Search Accelerator for Embedded Queries",
                "focus": "A pipelined hardware sorting network and binary-search core built in programmable logic accelerates lookups over a fixed embedded dataset (a lookup table, sensor calibration set, or small local database) far faster than a software search loop competing for ARM cycles. It's a clean, teachable example of applying classic hardware-acceleration principles (parallelism, pipelining) to a problem that isn't signal processing or vision, which broadens the FPGA-acceleration story. Good for a portfolio that wants to show FPGA use beyond the usual DSP/vision demos.",
                "components": ["Sorting-network HLS core", "Binary-search HLS core", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
            {
                "title": "Custom RISC-V Soft-Core Sensor Coprocessor",
                "focus": "A small open-source RISC-V soft core is synthesized into the PYNQ-Z2's programmable logic to run lightweight sensor-preprocessing firmware independently of the main ARM cores, freeing them for higher-level application logic while the soft core handles real-time polling and filtering. Building and integrating a soft core is a genuinely deep dive into how processor and fabric coexist on a single SoC. One of the more advanced projects here, and a great one for anyone aiming at computer-architecture or FPGA-tooling roles.",
                "components": ["Open-source RISC-V soft core (e.g. PicoRV32)", "Sensor peripherals (I2C/SPI)", "PYNQ-Z2"],
                "tags": ["FPGA acceleration"],
            },
        ],
    },
]

BOARD_BY_KEY = {b["key"]: b for b in BOARDS}
BOARD_ROTATION = [b["key"] for b in BOARDS]

# Keyword conflicts: a twist is skipped for a core idea if any of its
# keywords already shows up in that idea's title/focus text, so a project
# that's already solar-powered never gets stamped "Solar-Powered Edition",
# etc. Twists not listed here have no conflicts and pair with anything.
TWIST_CONFLICT_KEYWORDS = {
    "solar-powered": ["solar"],
    "mesh-networked": ["mesh"],
    "voice-alert": ["speaker", "voice-controlled", "intercom", "spoken", "synthesized speech"],
    "predictive-maintenance": ["predictive maintenance"],
    "multi-sensor-fusion": ["fusion", "second sensing modality", "cross-validation"],
    "data-logger": ["historical trend", "long-term local"],
}


def twist_compatible(core_idea, twist):
    keywords = TWIST_CONFLICT_KEYWORDS.get(twist["id"])
    if not keywords:
        return True
    haystack = f"{core_idea['title']} {core_idea['focus']}".lower()
    return not any(kw in haystack for kw in keywords)
