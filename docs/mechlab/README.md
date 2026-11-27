# Public MechLab summaries

Add one file named YYYY-MM-DD.md for each development day that should appear on the public website. The filename is the development date, not the time GitHub receives the commit. These notes are explicitly public-facing, even while this repository is private.

Format:

    # A clear title for the day's progress
    Tags: Renderer, Fix
    Image: vulkan-c1m1-beach-1280.webp

    A short opening paragraph describing the update (600 characters maximum).

    ## What changed

    - First update.
    - Second update.

    ## What comes next

    Remaining work and important limits.

The website shows each note as a card. The optional lines directly under the title fill in the card:

- `Tags:` up to three topics, separated by commas, from this list: Renderer, Native, Launcher, Playtest, Tools, Content, Website, Fix. They label the card, drive the topic filter on /news, appear on the update page and become RSS categories. To add a topic, add it to `CARD_TAGS` in `website/tools/sync_mechlab.py`.
- `Image:` a thumbnail, given as the path of an existing `.webp` file under `website/assets/plates/` (for example `studio/mod-studio-editor-v2.webp`). Use a real in-game or tool capture. Without one, the card shows the Core Critical mark instead.

The build stops with an error for an unknown tag, more than three tags, or a missing image, so a mistake cannot reach the live site.

Supported formatting: a single # title, plain paragraphs, ## and ### headings, and - bullet lists. Raw HTML is displayed as text. Inline Markdown links, emphasis, images, and tables are not interpreted; use plain prose and bullets.

Submit each dated note in a task branch pull request to develop. After review, it reaches the live website through a separate develop-to-main release pull request; merging into main triggers the Cloudflare Pages build, which reads the notes from this directory. The website builds the latest three summaries into the homepage and all summaries into /news and /updates/YYYY-MM-DD. Corrections to a dated note update the same page. A source link identifies the most recent main-branch commit that changed the note.

Ordinary game commits do not create website entries. Other session summaries, private evidence, game files, and commit bodies are not scanned or published. Keep secrets, private paths, original media, and unreviewed claims out of these notes. Read the repository's distribution policy before adding public material.

If publishing fails, the previous successful site remains available; inspect the workflow in the Actions tab and rerun after correcting the note or configuration. Do not delete the last dated note: empty input fails visibly and retains the previous published summaries.
