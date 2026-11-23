"use strict";

const field = (id) => document.getElementById(id);
let templates = {};

async function send(action, extra = {}) {
    const response = await fetch("/api/content", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, ...extra }),
    });
    const result = await response.json();
    if (!response.ok || result.status !== "ok") {
        throw new Error(JSON.stringify(result, null, 2));
    }
    return result.result;
}

async function perform(action) {
    const projectId = field("project").value;
    const profilePath = field("profile-path").value;
    switch (action) {
        case "configure":
            return send(action, {
                tool: field("tool").value,
                runtime: field("runtime").value,
                workspace: field("workspace").value,
            });
        case "save":
        case "compile":
            await send("save", {
                project_id: projectId,
                source: JSON.parse(field("source").value),
            });
            return action === "save"
                ? { message: "Source saved." }
                : send(action, { project_id: projectId });
        case "package":
            return send(action, { project_id: projectId });
        case "install":
            return send(action, { project_id: projectId });
        case "profile": {
            const result = await send(action, {
                profile_path: profilePath,
                profile: JSON.parse(field("profile").value),
            });
            field("profile").value = JSON.stringify(result.profile, null, 2);
            return result;
        }
        case "inspect":
            return send(action, { profile_path: profilePath });
        case "playtest":
            await perform("profile");
            return send(action, {
                profile_path: profilePath,
                mission: field("mission").value,
                network: {
                    mode: field("network-mode").value,
                    address: field("network-address").value,
                    port: Number(field("network-port").value),
                    players: Number(field("network-players").value),
                },
            });
        default:
            return send(action);
    }
}

document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", async () => {
        const buttons = document.querySelectorAll("button");
        buttons.forEach((item) => (item.disabled = true));
        field("result").textContent = "Checking native content…";
        try {
            field("result").textContent = JSON.stringify(
                await perform(button.dataset.action),
                null,
                2,
            );
        } catch (error) {
            field("result").textContent = error.message;
        } finally {
            buttons.forEach((item) => (item.disabled = false));
        }
    });
});

field("add-template").addEventListener("click", () => {
    try {
        const source = JSON.parse(field("source").value);
        source.definitions.push(structuredClone(templates[field("template").value]));
        field("source").value = JSON.stringify(source, null, 2);
    } catch (error) {
        field("result").textContent = error.message;
    }
});

fetch("/api/content/templates")
    .then((response) => response.json())
    .then((result) => {
        templates = result.templates;
        field("source").value = JSON.stringify(templates.package, null, 2);
        const profile = structuredClone(templates.profile);
        profile.packages = [{ id: templates.package.id, version: templates.package.version }];
        field("profile").value = JSON.stringify(profile, null, 2);
        Object.entries(templates).forEach(([name, value]) => {
            if (!value.kind) return;
            const option = document.createElement("option");
            option.value = name;
            option.textContent = name.replaceAll("_", " ");
            field("template").append(option);
        });
        field("result").textContent =
            "Ready. Configure your native tools, then choose a starter definition.";
    })
    .catch((error) => (field("result").textContent = error.message));
