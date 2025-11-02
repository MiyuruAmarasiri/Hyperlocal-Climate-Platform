"""MQTT client for community sensor data."""

from __future__ import annotations

import json
import logging
import queue
import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import paho.mqtt.client as mqtt
from shared.config import get_settings

log = logging.getLogger(__name__)


@dataclass
class SensorMessage:
    topic: str
    payload: dict
    received_at: datetime


class SensorMQTTIngestor:
    """Threaded MQTT client that buffers sensor messages for downstream processing."""

    def __init__(
        self,
        topic: str = "sensors/#",
        on_message: Optional[Callable[[SensorMessage], None]] = None,
        persist_dir: Optional[Path] = None,
        qos: int = 1,
    ) -> None:
        settings = get_settings()
        self.broker_url = settings.mqtt_broker_url
        self.username = settings.mqtt_username
        self.password = settings.mqtt_password
        self.ca_cert = settings.mqtt_ca_cert
        self.client_cert = settings.mqtt_client_cert
        self.client_key = settings.mqtt_client_key
        self.topic = topic
        self.on_message = on_message
        self.persist_dir = persist_dir or (settings.data_root / "processed" / "sensors")
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.persist_dir / "sensor_messages.ndjson"
        self.qos = min(max(qos, 0), 2)
        self._queue: "queue.Queue[SensorMessage]" = queue.Queue()
        self._client = mqtt.Client(client_id=f"hyperlocal-{datetime.utcnow().timestamp()}", clean_session=True)
        if self.username and self.password:
            self._client.username_pw_set(self.username, self.password)
        self._client.on_message = self._handle_message
        self._client.on_connect = self._handle_connect
        self._client.on_disconnect = self._handle_disconnect
        self._configure_tls()
        self._client.reconnect_delay_set(min_delay=1, max_delay=60)
        self._thread: Optional[threading.Thread] = None
        self._running = threading.Event()

    def start(self) -> None:
        host, port = self._parse_broker(self.broker_url)
        self._client.connect(host, port)
        self._running.set()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running.clear()
        self._client.disconnect()
        if self._thread:
            self._thread.join()

    def poll(self) -> Optional[SensorMessage]:
        try:
            item = self._queue.get_nowait()
        except queue.Empty:
            return None
        return item

    def _loop(self) -> None:
        while self._running.is_set():
            self._client.loop(timeout=1.0)

    def _handle_connect(self, client: mqtt.Client, _userdata, _flags, rc: int) -> None:
        if rc != 0:
            log.error("MQTT connection failed with code %s", rc)
            return
        client.subscribe(self.topic, qos=self.qos)
        log.info("Subscribed to %s", self.topic)

    def _handle_message(self, _client: mqtt.Client, _userdata, message: mqtt.MQTTMessage) -> None:
        try:
            payload = json.loads(message.payload.decode("utf-8"))
        except json.JSONDecodeError:
            log.warning("Invalid payload on %s", message.topic)
            return
        sensor_message = SensorMessage(
            topic=message.topic,
            payload=payload,
            received_at=datetime.utcnow(),
        )
        self._queue.put(sensor_message)
        self._persist(sensor_message)
        if self.on_message:
            self.on_message(sensor_message)

    def _handle_disconnect(self, _client: mqtt.Client, _userdata, rc: int) -> None:
        if rc != 0:
            log.warning("Unexpected MQTT disconnection (code=%s); client will auto-reconnect", rc)

    def _configure_tls(self) -> None:
        if not self.ca_cert:
            return
        tls_kwargs = {"ca_certs": str(self.ca_cert)}
        if self.client_cert and self.client_key:
            tls_kwargs["certfile"] = str(self.client_cert)
            tls_kwargs["keyfile"] = str(self.client_key)
        self._client.tls_set(**tls_kwargs)
        self._client.tls_insecure_set(False)

    def _persist(self, message: SensorMessage) -> None:
        timestamp = message.received_at.strftime("%Y%m%dT%H%M%S%f")
        path = self.persist_dir / f"{timestamp}.json"
        path.write_text(json.dumps({"topic": message.topic, "payload": message.payload}))
        self._append_to_log(message)

    def _append_to_log(self, message: SensorMessage) -> None:
        record = {
            "topic": message.topic,
            "received_at": message.received_at.isoformat(),
            "payload": message.payload,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")

    @staticmethod
    def _parse_broker(url: str) -> tuple[str, int]:
        if url.startswith("mqtt://"):
            without_scheme = url[len("mqtt://") :]
        else:
            without_scheme = url
        if ":" in without_scheme:
            host, port = without_scheme.split(":", 1)
            return host, int(port)
        return without_scheme, 1883


__all__ = ["SensorMQTTIngestor", "SensorMessage"]
