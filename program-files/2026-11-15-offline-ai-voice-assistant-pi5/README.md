# Offline AI Voice Assistant — Pi 5 Edition

A fully offline, privacy-first voice assistant that runs entirely on the
**Raspberry Pi 5** — no cloud, no subscriptions, no data leaving your home.

## Setup

### 1. Build whisper.cpp
```bash
git clone https://github.com/ggerganov/whisper.cpp /opt/whisper.cpp
cd /opt/whisper.cpp && make -j4
bash models/download-ggml-model.sh base.en
```

### 2. Install Ollama + pull model
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull mistral        # ~4 GB
# or lighter: ollama pull llama3.2:3b  (~2 GB)
```

### 3. Install Piper TTS
```bash
mkdir -p /opt/piper/voices
# Download binary
wget -q https://github.com/rhasspy/piper/releases/latest/download/piper_arm64.tar.gz \
     -O /tmp/piper.tar.gz
tar xzf /tmp/piper.tar.gz -C /opt/piper
export PATH="$PATH:/opt/piper"
# Download voice
cd /opt/piper/voices
wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
wget -q "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
```

### 4. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 5. Run
```bash
# Basic (no LED, no MQTT)
python main.py

# With LED ring on GPIO 18 (12 LEDs) + home automation via MQTT
sudo python main.py --led --mqtt-host 192.168.1.10 --model mistral
```

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Orchestration loop |
| `hotword_detector.py` | VAD-based wake detection |
| `whisper_stt.py` | Speech-to-text via whisper.cpp |
| `ollama_chat.py` | LLM conversation via Ollama |
| `piper_tts.py` | Neural TTS via Piper |
| `led_controller.py` | WS2812B LED ring feedback |
| `home_automation.py` | MQTT + GPIO device control |

## Benchmarks (Pi 5, 8 GB, Raspberry Pi OS Bookworm)

| Stage | Model | Latency |
|---|---|---|
| Whisper STT | `base.en` | ~700 ms |
| Ollama LLM | `mistral` Q4 | ~2–3 s |
| Piper TTS | `en_US-lessac-medium` | ~400 ms |
| **Total** | | **~3–4 s** |

## Tags
`#offline-ai` `#voice-assistant` `#raspberry-pi-5`
