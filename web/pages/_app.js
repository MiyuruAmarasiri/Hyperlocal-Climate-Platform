import "../styles/globals.css";
import SecurityHead from "../components/SecurityHead";

export default function App({ Component, pageProps }) {
  return (
    <>
      <SecurityHead />
      <Component {...pageProps} />
    </>
  );
}
