const CHANNEL_ID = "UC0YGz5FEh7-ij1miUmXECiw";
const FEED_URL = `https://www.youtube.com/feeds/videos.xml?channel_id=${CHANNEL_ID}`;

export async function onRequestGet(context) {
    const cache = caches.default;
    const cached = await cache.match(context.request);
    if (cached) return cached;

    try {
        const upstream = await fetch(FEED_URL, {
            headers: { Accept: "application/atom+xml" },
        });
        if (!upstream.ok) throw new Error(`YouTube feed returned ${upstream.status}`);

        const xml = await upstream.text();
        if (!xml.includes("<feed") || !xml.includes(CHANNEL_ID)) {
            throw new Error("Unexpected YouTube feed response");
        }

        const response = new Response(xml, {
            headers: {
                "Content-Type": "application/atom+xml; charset=utf-8",
                "Cache-Control": "public, max-age=0, s-maxage=300",
            },
        });
        context.waitUntil(cache.put(context.request, response.clone()));
        return response;
    } catch (error) {
        console.error("Could not refresh the YouTube uploads feed", error);
        return new Response("YouTube uploads temporarily unavailable", {
            status: 502,
            headers: { "Cache-Control": "no-store" },
        });
    }
}
