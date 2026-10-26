import assert from 'node:assert/strict';
import test from 'node:test';
import worker from './worker.mjs';

const data = new TextEncoder().encode('authored fixture update');
const path = '/mw3/1.0.37/1.0.37.zip';
const env = {
  PUBLIC_OBJECTS: JSON.stringify({ [path]: { key: 'online-updates/mw3/1.0.37/1.0.37.zip', bytes: data.length } }),
  UPDATES: {
    async head() { return { size: data.length, etag: 'fixture', httpEtag: '"fixture"' }; },
    async get(key, options) {
      assert.equal(key, 'online-updates/mw3/1.0.37/1.0.37.zip');
      assert.equal(options.onlyIf.etagMatches, 'fixture');
      return { body: options.range ? data.slice(options.range.offset) : data };
    }
  }
};
const request = (suffix = path, options) => new Request('https://updates.example.test' + suffix, options);
test('only approved public update objects are served', async () => {
  const result = await worker.fetch(request(), env);
  assert.equal(result.status, 200);
  assert.deepEqual(new Uint8Array(await result.arrayBuffer()), data);
  for (const target of ['/', '/packs/anything.mw3pack', '/MechWarrior-3.iso', '/?key=secret', '/mw3/1.0.37/other.zip'])
    assert.equal((await worker.fetch(request(target), env)).status, 404);
  for (const method of ['PUT', 'DELETE', 'POST', 'PATCH', 'OPTIONS'])
    assert.equal((await worker.fetch(request(path, { method }), env)).status, 405);
});
test('strong validator range resume, changed validator restart, and invalid ranges', async () => {
  const resumed = await worker.fetch(request(path, { headers: { Range: 'bytes=4-', 'If-Range': '"fixture"' } }), env);
  assert.equal(resumed.status, 206);
  assert.equal(resumed.headers.get('Content-Range'), `bytes 4-${data.length - 1}/${data.length}`);
  assert.deepEqual(new Uint8Array(await resumed.arrayBuffer()), data.slice(4));
  const restarted = await worker.fetch(request(path, { headers: { Range: 'bytes=4-', 'If-Range': '"old"' } }), env);
  assert.equal(restarted.status, 200);
  assert.deepEqual(new Uint8Array(await restarted.arrayBuffer()), data);
  for (const range of ['bytes=99999-', 'bytes=-4', 'bytes=0-4,8-10'])
    assert.equal((await worker.fetch(request(path, { headers: { Range: range } }), env)).status, 416);
});
test('HEAD is bounded; incorrect object size and forbidden allowlist entries fail closed', async () => {
  const result = await worker.fetch(request(path, { method: 'HEAD' }), env);
  assert.equal(result.headers.get('Content-Length'), String(data.length));
  assert.equal(await result.text(), '');
  const wrong = { ...env, PUBLIC_OBJECTS: JSON.stringify({ [path]: { key: 'online-updates/mw3/1.0.37/1.0.37.zip', bytes: 1 } }) };
  assert.equal((await worker.fetch(request(), wrong)).status, 503);
  const bad = { ...env, PUBLIC_OBJECTS: JSON.stringify({ '/packs/private.mw3pack': { key: 'packs/private.mw3pack' } }) };
  assert.equal((await worker.fetch(request('/packs/private.mw3pack'), bad)).status, 503);
});
