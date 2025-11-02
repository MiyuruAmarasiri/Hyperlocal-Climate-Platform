import styles from "../styles/StatCard.module.css";

export default function StatCard({ label, value, description, accent }) {
  return (
    <article className={styles.card} data-accent={accent || "default"}>
      <h3>{label}</h3>
      <p className={styles.value}>{value}</p>
      {description ? <p className={styles.description}>{description}</p> : null}
    </article>
  );
}
