import styles from "../styles/Section.module.css";

export default function Section({ title, subtitle, children, id }) {
  return (
    <section id={id} className={styles.section}>
      <header className={styles.header}>
        <h2>{title}</h2>
        {subtitle ? <p>{subtitle}</p> : null}
      </header>
      <div className={styles.content}>{children}</div>
    </section>
  );
}
