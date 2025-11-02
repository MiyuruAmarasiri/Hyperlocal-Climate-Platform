import Layout from "../components/Layout";
import Section from "../components/Section";

export default function AboutPage() {
  return (
    <Layout>
      <Section title="Mission" subtitle="Empower frontline communities with trustworthy, hyperlocal flood intelligence.">
        <p style={{ lineHeight: 1.7 }}>
          The Hyperlocal Climate-Risk Platform is an OpenAI initiative pairing advanced modelling with secure engineering
          practices. We believe that adaptation technology must be both explainable and defensible, with controls that meet
          government and enterprise procurement standards before deployment.
        </p>
      </Section>
      <Section title="Roadmap">
        <ul style={{ lineHeight: 1.7 }}>
          <li>Global pilots with national hydrological agencies and humanitarian partners.</li>
          <li>Expanded adaptation content powered by socio-economic vulnerability indices.</li>
          <li>Offline-first mobile experiences with multilingual alert packages.</li>
          <li>Open developer APIs guarded by fine-grained authorization policies.</li>
        </ul>
      </Section>
      <Section title="Get involved">
        <p>
          Email <a href="mailto:climate-risk@openai.com">climate-risk@openai.com</a> to collaborate on deployments,
          contribute domain expertise, or integrate additional hazard models.
        </p>
      </Section>
    </Layout>
  );
}
