const PROXY_PREFIX = "/api/proxy";

async function request(path, options = {}) {
  const response = await fetch(`${PROXY_PREFIX}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`Request failed (${response.status}): ${detail}`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export function fetchForecast({ latitude, longitude, horizon }) {
  return request("/forecast", {
    method: "POST",
    body: JSON.stringify({ latitude, longitude, horizon_hours: horizon }),
  });
}

export function fetchRiskMap(basinId) {
  return request("/risk-map", {
    method: "POST",
    body: JSON.stringify({ basin_id: basinId }),
  });
}

export function fetchAdaptation(basinId) {
  const params = new URLSearchParams({ basin_id: basinId });
  return request(`/adaptation?${params.toString()}`, { method: "GET" });
}

export function fetchHealth() {
  return request("/health", { method: "GET" });
}
