import json
from datetime import datetime
from pathlib import Path

import pytest

from ingestion import sensor_mqtt
from shared.config import get_settings


class FakeClient:
    def __init__(self, *_, **__):
        self.attrs = {}
        self.tls_args = None
        self.tls_insecure = None

    def username_pw_set(self, *_args, **_kwargs):
        pass

    def tls_set(self, **kwargs):
        self.tls_args = kwargs

    def tls_insecure_set(self, value):
        self.tls_insecure = value

    def reconnect_delay_set(self, *args, **kwargs):
        pass

    def connect(self, *_args, **_kwargs):
        pass

    def loop(self, *_args, **_kwargs):
        pass

    def loop_stop(self):
        pass

    def disconnect(self):
        pass

    def subscribe(self, *args, **kwargs):
        pass

    def __setattr__(self, key, value):
        if key in {"attrs", "tls_args", "tls_insecure"}:
            super().__setattr__(key, value)
        else:
            self.attrs[key] = value


def test_sensor_mqtt_tls(monkeypatch, tmp_path):
    ca = tmp_path / "ca.pem"
    ca.write_text("certificate")
    monkeypatch.setenv("DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("LOGS_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("MQTT_CA_CERT", str(ca))
    get_settings.cache_clear()

    monkeypatch.setattr(sensor_mqtt.mqtt, "Client", FakeClient)

    ingestor = sensor_mqtt.SensorMQTTIngestor(persist_dir=tmp_path)

    assert ingestor._client.tls_args["ca_certs"] == str(ca)
    message = sensor_mqtt.SensorMessage(topic="sensors/demo", payload={"value": 1}, received_at=datetime.utcnow())
    ingestor._persist(message)
    log_file = tmp_path / "sensor_messages.ndjson"
    assert log_file.exists()
    content = log_file.read_text().strip()
    assert json.loads(content)["topic"] == "sensors/demo"
