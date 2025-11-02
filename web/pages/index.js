import Link from "next/link";
import useSWR from "swr";
import Layout from "../components/Layout";
import Section from "../components/Section";
import StatCard from "../components/StatCard";
import { fetchHealth } from "../lib/api";

const fetcher = () => fetchHealth();

export default function HomePage() {
  const { data } = useSWR("health", fetcher, { refreshInterval: 45000 });

  const stats = [
    {
      label: "Operational Services",
      value: data ? data.services.length : "--",
      description: "Weather, risk, adaptation modules online",
      accent: "success",
    },
    {
      label: "Last Health Check",
      value: data ? new Date(data.time).toLocaleTimeString() : "--",
      description: "Realtime service heartbeat",
      accent: "warning",
    },
    {
      label: "API Endpoint",
      value: process.env.NEXT_PUBLIC_API_BASE,
      description: "All calls proxied with signed headers",
    },
  ];

  return (
    <Layout>
      <Section
        title="Climate intelligence with zero-compromise security"
        subtitle="Integrating ECMWF reanalysis, CHIRPS precipitation, and community telemetry with strict security controls for enterprise deployments."
      >
        <div style={{ display: "grid", gap: "1.5rem", maxWidth: "720px" }}>
          <p style={{ lineHeight: 1.7 }}>
            The Hyperlocal Climate-Risk Platform merges planetary-scale datasets with local knowledge to deliver timely,
            trusted alerts. Built by OpenAI engineers, every endpoint is wrapped in API proxies, audited, and hardened for
            sovereign deployments.
          </p>
          <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
            <Link className="cta" href="/forecast">
              Explore Live Forecasts
            </Link>
            <Link className="secondary" href="/risk">
              Inspect Risk Overlays
            </Link>
          </div>
        </div>
      </Section>

      <Section title="Platform readiness" subtitle="Status snapshots sourced from the secured FastAPI health feed.">
        <div style={{ display: "flex", gap: "1.5rem", flexWrap: "wrap" }}>
          {stats.map((item) => (
            <StatCard key={item.label} {...item} />
          ))}
        </div>
      </Section>

      <Section
        title="Capabilities by pillar"
        subtitle="Modular services span ingestion, modelling, adaptation, and omni-channel delivery."
      >
        <div
          style={{
            display: "grid",
            gap: "1.5rem",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          }}
        >
          {FEATURES.map((feature) => (
            <article key={feature.title} style={featureCardStyle}>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
              <ul>
                {feature.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
      </Section>
    </Layout>
  );
}

const FEATURES = [
  {
    title: "Data ingestion",
    description: "Resilient pipelines for deterministic and probabilistic products.",
    items: ["ECMWF ERA5 + forecast blends", "CHIRPS/IMERG precipitation mosaics", "TLS-secured MQTT device mesh"],
  },
  {
    title: "Hydrologic modelling",
    description: "AI + physics for rapid flood situational awareness.",
    items: ["Transfer learning LSTM ensembles", "WRF-Hydro orchestration", "Virtual gauge calibration"],
  },
  {
    title: "Risk & adaptation",
    description: "Blend hazard curves with exposure to guide decisions.",
    items: ["GeoPandas exposure overlays", "Dynamic adaptation scoring", "Sovereign data residency options"],
  },
  {
    title: "Secure delivery",
    description: "Enterprise observability wrapped in a Zero Trust fabric.",
    items: ["API proxy with rotating keys", "Dash ops console & PWA alerts", "Comprehensive audit logging"],
  },
];

const featureCardStyle = {
  background: "rgba(15, 23, 42, 0.75)",
  borderRadius: "20px",
  padding: "1.5rem",
  border: "1px solid rgba(148, 163, 184, 0.18)",
  display: "grid",
  gap: "0.75rem",
  lineHeight: 1.6,
};
