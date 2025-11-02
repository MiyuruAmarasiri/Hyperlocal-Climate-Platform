import Head from "next/head";

const scriptSrc = process.env.NEXT_PUBLIC_THIRD_PARTY_SCRIPT_SRC;
const scriptIntegrity = process.env.NEXT_PUBLIC_THIRD_PARTY_SCRIPT_INTEGRITY;
const scriptCrossOrigin = process.env.NEXT_PUBLIC_THIRD_PARTY_SCRIPT_CROSSORIGIN || "anonymous";

export default function SecurityHead() {
  if (!scriptSrc) {
    return null;
  }

  return (
    <Head>
      <script
        src={scriptSrc}
        integrity={scriptIntegrity || undefined}
        crossOrigin={scriptCrossOrigin}
        defer
      />
    </Head>
  );
}
