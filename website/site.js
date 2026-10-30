const siteHeader = document.querySelector(".site-header");
const menuButton = document.querySelector(".menu-toggle");
function closeMenu(returnFocus = false) {
    if (!siteHeader || !menuButton) return;
    siteHeader.classList.remove("menu-open");
    menuButton.setAttribute("aria-expanded", "false");
    if (returnFocus) menuButton.focus();
}
menuButton?.addEventListener("click", () => {
    const open = menuButton.getAttribute("aria-expanded") !== "true";
    siteHeader.classList.toggle("menu-open", open);
    menuButton.setAttribute("aria-expanded", String(open));
});
document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && siteHeader?.classList.contains("menu-open")) closeMenu(true);
});
document.addEventListener("click", (event) => {
    if (siteHeader && !siteHeader.contains(event.target)) closeMenu();
});
document
    .querySelectorAll(".primary-nav a")
    .forEach((link) => link.addEventListener("click", () => closeMenu()));
window.matchMedia("(min-width: 761px)").addEventListener("change", (event) => {
    if (event.matches) closeMenu();
});
const activePage = (window.location.pathname.split("/").pop() || "index").replace(/\.html$/, "");
document.querySelectorAll(".primary-nav a").forEach((link) => {
    if (link.getAttribute("href")?.replace(/\.html$/, "") === activePage)
        link.setAttribute("aria-current", "page");
});
document.querySelectorAll(".youtube-latest").forEach((section) => {
    const carousel = section.querySelector(".youtube-carousel");
    const card = section.querySelector(".youtube-card");
    if (!carousel || !card) return;

    async function refreshVideos() {
        try {
            const response = await fetch("/api/youtube-latest", { cache: "no-cache" });
            if (!response.ok) return;
            const xml = new DOMParser().parseFromString(await response.text(), "application/xml");
            if (xml.querySelector("parsererror")) return;

            const atom = "http://www.w3.org/2005/Atom";
            const youtube = "http://www.youtube.com/xml/schemas/2015";
            const entries = [...xml.getElementsByTagNameNS(atom, "entry")];
            const videos = entries
                .map((entry) => ({
                    id: entry.getElementsByTagNameNS(youtube, "videoId")[0]?.textContent,
                    title: entry.getElementsByTagNameNS(atom, "title")[0]?.textContent,
                    published: entry.getElementsByTagNameNS(atom, "published")[0]?.textContent,
                }))
                .filter(
                    (video) =>
                        /^[A-Za-z0-9_-]{11}$/.test(video.id) && video.title && video.published,
                )
                .slice(0, 8);
            if (!videos.length) return;
            const currentIds = [...carousel.querySelectorAll(".youtube-card")].map((link) =>
                new URL(link.href).searchParams.get("v"),
            );
            if (videos.map((video) => video.id).join(",") === currentIds.join(",")) return;

            const cards = videos.map((video, index) => {
                const link = document.createElement("a");
                link.className =
                    index === 0 ? "youtube-card youtube-card-featured" : "youtube-card";
                link.href = `https://www.youtube.com/watch?v=${video.id}`;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.setAttribute("aria-label", `Watch ${video.title} on YouTube`);
                if (index === 0) {
                    const badge = document.createElement("span");
                    badge.className = "youtube-card-badge";
                    badge.textContent = "Newest video";
                    link.append(badge);
                }
                const image = document.createElement("img");
                image.src = `https://i.ytimg.com/vi/${video.id}/hqdefault.jpg`;
                image.alt = "";
                image.width = 480;
                image.height = 360;
                image.loading = "lazy";
                const title = document.createElement("span");
                title.className = "youtube-card-title";
                title.textContent = video.title;
                const date = document.createElement("time");
                date.dateTime = video.published.slice(0, 10);
                date.textContent = date.dateTime;
                link.append(image, title, date);
                return link;
            });
            carousel.replaceChildren(...cards);
            carousel.scrollLeft = 0;
        } catch (error) {
            console.warn("Keeping saved YouTube videos until the feed is available", error);
        }
    }

    refreshVideos();
    setInterval(() => {
        if (!document.hidden) refreshVideos();
    }, 300000);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) refreshVideos();
    });
    const scrollCards = (direction) => {
        const visibleCard = carousel.querySelector(".youtube-card");
        if (!visibleCard) return;
        const cardSpacing = parseFloat(getComputedStyle(carousel).gap) || 0;
        const motion = window.matchMedia("(prefers-reduced-motion: reduce)").matches
            ? "auto"
            : "smooth";
        carousel.scrollBy({
            left: direction * (visibleCard.getBoundingClientRect().width + cardSpacing),
            behavior: motion,
        });
    };
    section.querySelector("[data-carousel-prev]")?.addEventListener("click", () => scrollCards(-1));
    section.querySelector("[data-carousel-next]")?.addEventListener("click", () => scrollCards(1));
});
const projectKey = new URLSearchParams(window.location.search).get("id") || "mw3";
if (document.body.hasAttribute("data-project-page")) {
    const active = ["mw3", "pirates-moon", "mw4"].includes(projectKey) ? projectKey : "missing";
    document.querySelectorAll("[data-project]").forEach((section) => {
        section.hidden = section.dataset.project !== active;
    });
    const titles = {
        mw3: "MW3",
        "pirates-moon": "MW3: Pirate’s Moon",
        mw4: "MW4",
        missing: "Project not found",
    };
    document.title = `Core Critical — ${titles[active]}`;
}
