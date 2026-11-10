// api.<domain> → the GrowthPilot API on Modal. Keeps the address Meta, SePay and the web app use.
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    url.hostname = env.UPSTREAM_HOST;
    const upstream = new Request(url, request);
    upstream.headers.set("X-Client-IP", request.headers.get("CF-Connecting-IP") || "");
    return fetch(upstream, { redirect: "manual" });
  },
};
