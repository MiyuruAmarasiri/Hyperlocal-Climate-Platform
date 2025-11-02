import { useState } from "react";
import Layout from "../components/Layout";
import Section from "../components/Section";
import { fetchForecast } from "../lib/api";

export default function ForecastPage() {
  const [lat, setLat] = useState(37.7749);
  const [lon, setLon] = useState(-122.4194);
  const [horizon, setHorizon] = useState(48);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState(null);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const response = await fetchForecast({ latitude: parseFloat(lat), longitude: parseFloat(lon), horizon: parseInt(horizon, 10) });
      setData(response);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <Section
        title="Hyperlocal Forecast Sandbox"
        subtitle="Query the FastAPI proxy for a point-based bundle sourced from ECMWF/Open-Meteo with automatic failover."
      >
        <form onSubmit={handleSubmit} style={formStyle}>
          <FormField label="Latitude">
            <input type="number" step="0.0001" value={lat} onChange={(e) => setLat(e.target.value)} required style={inputStyle} />
          </FormField>
          <FormField label="Longitude">
            <input type="number" step="0.0001" value={lon} onChange={(e) => setLon(e.target.value)} required style={inputStyle} />
          </FormField>
          <FormField label="Horizon (hours)">
            <input type="number" min="6" max="168" step="6" value={horizon} onChange={(e) => setHorizon(e.target.value)} style={inputStyle} />
          </FormField>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <button className="cta" type="submit" disabled={loading}>
              {loading ? "Fetching..." : "Get Forecast"}
            </button>
            {error ? <p style={{ color: "#fca5a5" }}>{error}</p> : null}
          </div>
        </form>
      </Section>
      {data ? (
        <Section title="Hourly Forecast" subtitle={`Source: ${data.source}`}>
          <div style={{ overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Temperature (°C)</th>
                  <th>Precip (mm)</th>
                  <th>Wind (m/s)</th>
                </tr>
              </thead>
              <tbody>
                {data.hourly.slice(0, 48).map((entry) => (
                  <tr key={entry.time}>
                    <td>{new Date(entry.time).toLocaleString()}</td>
                    <td>{entry.temperature_c.toFixed(1)}</td>
                    <td>{entry.precipitation_mm.toFixed(2)}</td>
                    <td>{entry.windspeed_ms.toFixed(1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Section>
      ) : null}
    </Layout>
  );
}

function FormField({ label, children }) {
  return (
    <label style={{ display: "grid", gap: "0.5rem", fontWeight: 600 }}>
      <span>{label}</span>
      {children}
    </label>
  );
}

const formStyle = {
  display: "grid",
  gap: "1.25rem",
  maxWidth: "520px",
};

const inputStyle = {
  width: "100%",
  marginTop: "0.2rem",
  padding: "0.7rem 0.9rem",
  borderRadius: "12px",
  border: "1px solid rgba(148, 163, 184, 0.4)",
  backgroundColor: "rgba(15, 23, 42, 0.6)",
  color: "#e2e8f0",
  fontSize: "1rem",
};
