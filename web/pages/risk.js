import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Section from "../components/Section";
import { fetchRiskMap, fetchAdaptation } from "../lib/api";

const basinOptions = [
  { value: "basin-1", label: "Basin 1" },
  { value: "basin-2", label: "Basin 2" },
  { value: "basin-3", label: "Basin 3" }
];

export default function RiskPage() {
  const [basin, setBasin] = useState(basinOptions[0].value);
  const [risk, setRisk] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [riskResponse, adaptationResponse] = await Promise.all([
          fetchRiskMap(basin),
          fetchAdaptation(basin)
        ]);
        setRisk(riskResponse.features || []);
        setRecommendations(adaptationResponse.recommendations || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [basin]);

  return (
    <Layout>
      <Section
        title="Risk overlays"
        subtitle="Intersect forecasted hazard grids with exposure layers to prioritize adaptation tactics."
      >
        <div style={{ display: "grid", gap: "1rem", maxWidth: "340px" }}>
          <label style={{ display: "grid", gap: "0.5rem", fontWeight: 600 }}>
            Basin
            <select value={basin} onChange={(e) => setBasin(e.target.value)} style={selectStyle}>
              {basinOptions.map((option) => (
                <option value={option.value} key={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        {loading ? <p>Loading risk layers...</p> : null}
        {error ? <p style={{ color: "#fca5a5" }}>{error}</p> : null}
        {!loading && !error ? (
          <div style={gridWrapper}>
            <article style={analysisCard}>
              <h3>Exposure summary</h3>
              <div style={{ display: "grid", gap: "1rem" }}>
                {risk.map((feature, index) => (
                  <div key={index} style={featureRow}>
                    <header>
                      <h4>Cell #{index + 1}</h4>
                      <span className={`badge risk-${feature.properties.risk_level}`}>{feature.properties.risk_level}</span>
                    </header>
                    <dl>
                      {Object.entries(feature.properties)
                        .filter(([key]) => key !== "risk_level")
                        .map(([key, value]) => (
                          <div key={key}>
                            <dt>{key}</dt>
                            <dd>{typeof value === "number" ? value.toFixed(3) : String(value)}</dd>
                          </div>
                        ))}
                    </dl>
                  </div>
                ))}
              </div>
            </article>
            <article style={analysisCard}>
              <h3>Adaptation guidance</h3>
              <ul style={listStyle}>
                {recommendations.map((rec) => (
                  <li key={rec.area_id}>
                    <strong>{rec.risk_level.toUpperCase()}</strong> — {rec.recommendation}
                  </li>
                ))}
              </ul>
            </article>
          </div>
        ) : null}
      </Section>
    </Layout>
  );
}

const selectStyle = {
  display: "block",
  marginTop: "0.2rem",
  padding: "0.6rem 1rem",
  borderRadius: "12px",
  border: "1px solid rgba(148, 163, 184, 0.3)",
  background: "rgba(15, 23, 42, 0.65)",
  color: "#e2e8f0",
};

const gridWrapper = {
  display: "grid",
  gap: "1.5rem",
  marginTop: "2rem",
};

const analysisCard = {
  background: "rgba(15, 23, 42, 0.7)",
  borderRadius: "18px",
  border: "1px solid rgba(148, 163, 184, 0.15)",
  padding: "1.5rem",
  display: "grid",
  gap: "1rem",
};

const featureRow = {
  border: "1px solid rgba(148, 163, 184, 0.12)",
  borderRadius: "14px",
  padding: "1rem",
  display: "grid",
  gap: "0.75rem",
  background: "rgba(2, 6, 23, 0.55)",
};

const listStyle = {
  margin: 0,
  paddingLeft: "1.2rem",
  lineHeight: 1.7,
};
