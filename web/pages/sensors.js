import Layout from "../components/Layout";
import Section from "../components/Section";

export default function SensorsPage() {
  return (
    <Layout>
      <Section
        title="Community sensor mesh"
        subtitle="Secure MQTT ingestion with mutual TLS, QoS guarantees, and immutable telemetry for auditing."
      >
        <div style={grid}>
          <article style={card}>
            <h3>Onboarding steps</h3>
            <ol style={listOrdered}>
              <li>Request device credentials via the operations console.</li>
              <li>Provision certificates signed by the OpenAI Climate PKI.</li>
              <li>Point devices to <code>mqtts://edge.openai-climate.local</code> with QoS 1.</li>
              <li>Publish JSON payloads to <code>sensors/&lt;community&gt;/&lt;device&gt;</code>.</li>
            </ol>
          </article>
          <article style={card}>
            <h3>Data contract</h3>
            <pre style={preStyle}>{`{
  "device_id": "station-17",
  "rainfall_mm": 4.2,
  "river_level_cm": 183,
  "battery_v": 3.7,
  "signature": "base64-ed25519"
}`}</pre>
            <p>Every message is signed at the edge and verified by the ingestion proxy before persistence.</p>
          </article>
          <article style={card}>
            <h3>Security posture</h3>
            <ul style={listUnordered}>
              <li>Client certificates rotated every 90 days with automated revocation.</li>
              <li>Replay protection and payload hashing enforced by the proxy API route.</li>
              <li>Sensor logs appended to encrypted NDJSON and TimescaleDB for forensics.</li>
            </ul>
          </article>
        </div>
      </Section>
    </Layout>
  );
}

const grid = {
  display: "grid",
  gap: "1.5rem",
};

const card = {
  background: "rgba(15, 23, 42, 0.72)",
  borderRadius: "20px",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  padding: "1.75rem",
  display: "grid",
  gap: "1rem",
};

const listOrdered = {
  margin: 0,
  paddingLeft: "1.3rem",
  lineHeight: 1.7,
};

const listUnordered = {
  margin: 0,
  paddingLeft: "1.2rem",
  lineHeight: 1.7,
};

const preStyle = {
  background: "rgba(2, 6, 23, 0.65)",
  borderRadius: "12px",
  padding: "1.1rem",
  overflowX: "auto",
  border: "1px solid rgba(148, 163, 184, 0.18)",
};
