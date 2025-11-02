import Link from "next/link";
import clsx from "clsx";
import styles from "../styles/Layout.module.css";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/forecast", label: "Forecast" },
  { href: "/risk", label: "Risk Maps" },
  { href: "/sensors", label: "Sensors" },
  { href: "/about", label: "About" }
];

const secureSignals = [
  "Federated API proxy with signed requests",
  "CSP + HSTS enforcing HTTPS everywhere",
  "Role based access & key rotation ready",
  "Audited telemetry with immutable logs"
];

export default function Layout({ children }) {
  return (
    <div className={styles.layout}>
      <div className={styles.backgroundGlow} aria-hidden="true" />
      <header className={styles.header}>
        <div className={styles.brandBlock}>
          <span className={styles.badge}>OpenAI Secure</span>
          <h1 className={styles.brand}>Hyperlocal Climate Platform</h1>
          <p className={styles.tagline}>Enterprise-grade climate intelligence, delivered safely to the last mile.</p>
        </div>
        <nav className={styles.navigation}>
          <ul className={styles.navList}>
            {navItems.map((item) => (
              <li key={item.href}>
                <Link className={clsx(styles.navLink)} href={item.href}>
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
          <div className={styles.navActions}>
            <Link href="/forecast" className={clsx("cta", styles.primaryAction)}>
              Launch Console
            </Link>
            <a href="mailto:climate-risk@openai.com" className={clsx("secondary", styles.secondaryAction)}>
              Contact Team
            </a>
          </div>
        </nav>
      </header>
      <aside className={styles.securityRail}>
        <h2>Security Posture</h2>
        <ul>
          {secureSignals.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </aside>
      <main className={styles.main}>{children}</main>
      <footer className={styles.footer}>
        <div>
          <p>&copy; {new Date().getFullYear()} Hyperlocal Climate-Risk Platform</p>
          <p className={styles.footerMeta}>Powered by FastAPI · Next.js · Zero Trust design</p>
        </div>
      </footer>
    </div>
  );
}
