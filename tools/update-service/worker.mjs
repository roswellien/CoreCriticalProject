// Read-only public update delivery. Public paths map to publisher-selected objects;
// a bucket key, prefix, or caller-supplied URL is never accepted as a parameter.
export default {
  async fetch(request, env) {
    const headers = { "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store" };
    if (!['GET', 'HEAD'].includes(request.method))
      return new Response('Read-only update service', { status: 405, headers: { ...headers, Allow: 'GET, HEAD' } });
    const path = new URL(request.url).pathname;
    const allowed = JSON.parse(env.PUBLIC_OBJECTS);
    const entry = Object.hasOwn(allowed, path) ? allowed[path] : null;
    if (!entry) return new Response('Update not found', { status: 404, headers });
    // Configuration must fail closed even if a publication script supplies an unintended object.
    const catalog = path === '/channels/playtest/catalog.json';
    if ((!catalog && !/^\/(launcher|mw3)\/\d+\.\d+\.\d+\/\d+\.\d+\.\d+\.(ccupdate|mw3update|zip)$/.test(path)) ||
        !entry.key.startsWith('online-updates/') || (!catalog && !entry.key.endsWith(path.split('/').at(-1))))
      return new Response('Invalid delivery configuration', { status: 503, headers });
    const info = await env.UPDATES.head(entry.key);
    if (!info || (!catalog && info.size !== entry.bytes))
      return new Response('Update unavailable', { status: 503, headers });
    const responseHeaders = new Headers({ ...headers,
      'Content-Type': catalog || path.endsWith('update') ? 'application/json' : 'application/octet-stream',
      'ETag': info.httpEtag, 'Accept-Ranges': 'bytes',
      'Cache-Control': catalog ? 'no-cache, no-store, must-revalidate' : 'public, max-age=31536000, immutable' });
    if (!catalog) responseHeaders.set('Content-Disposition', 'attachment; filename="' + path.split('/').at(-1) + '"');
    let range;
    const requestedRange = request.headers.get('Range');
    const ifRange = request.headers.get('If-Range');
    if (requestedRange && (!ifRange || ifRange === info.httpEtag)) {
      const match = /^bytes=(\d+)-$/.exec(requestedRange);
      const offset = match ? Number(match[1]) : NaN;
      if (!Number.isSafeInteger(offset) || offset < 0 || offset >= info.size) {
        responseHeaders.set('Content-Range', `bytes */${info.size}`);
        responseHeaders.set('Cache-Control', 'no-store');
        return new Response(null, { status: 416, headers: responseHeaders });
      }
      range = { offset, length: info.size - offset };
      responseHeaders.set('Content-Range', `bytes ${offset}-${info.size - 1}/${info.size}`);
    }
    const length = range?.length ?? info.size;
    responseHeaders.set('Content-Length', String(length));
    if (request.method === 'HEAD') return new Response(null, { status: range ? 206 : 200, headers: responseHeaders });
    // Bind the body to the same strong object validator inspected above.
    const object = await env.UPDATES.get(entry.key, { onlyIf: { etagMatches: info.etag }, ...(range ? { range } : {}) });
    if (!object || !('body' in object)) return new Response('Update changed; retry', { status: 503, headers });
    return new Response(object.body, { status: range ? 206 : 200, headers: responseHeaders });
  }
};
