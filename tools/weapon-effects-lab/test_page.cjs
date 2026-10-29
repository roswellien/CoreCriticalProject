// Shared DOM input for the offline viewer tests; script contents stay separate.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function readPage(html) {
    const scripts = new Map();
    for (const match of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)) {
        const id = match[1].match(/\bid\s*=\s*["']([^"']+)["']/i)?.[1];
        if (!id) continue;
        assert(!scripts.has(id), `Duplicate script id: ${id}`);
        scripts.set(id, { attributes: match[1], textContent: match[2] });
    }
    const data = scripts.get("lab-data");
    assert(data, "Missing lab data element");
    assert.match(data.attributes, /\btype\s*=\s*["']application\/json["']/i);
    const script = scripts.get("lab-script");
    assert(script, "Missing executable lab script");
    return { data, script: script.textContent };
}

function checkUnbuiltPage(filename, message) {
    const page = readPage(fs.readFileSync(path.join(__dirname, filename), "utf8"));
    assert.equal(JSON.parse(page.data.textContent), null);
    assert.throws(
        () =>
            vm.runInNewContext(page.script, {
                document: {
                    getElementById: (id) => {
                        assert.equal(id, "lab-data");
                        return page.data;
                    },
                },
            }),
        (error) => error.message === message,
    );
}

module.exports = { readPage, checkUnbuiltPage };
