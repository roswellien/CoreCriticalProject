# Public MechLab summaries

Add one file named YYYY-MM-DD.md for each development day that should appear on the public website. The filename is the development date, not the time GitHub receives the commit. These notes are explicitly public-facing, even while this repository is private.

Format:

    # A clear title for the day's progress

    A short opening paragraph describing the update (600 characters maximum).

    ## What changed

    - First update.
    - Second update.

    ## What comes next

    Remaining work and important limits.

Supported formatting: a single # title, plain paragraphs, ## and ### headings, and - bullet lists. Raw HTML is displayed as text. Inline Markdown links, emphasis, images, and tables are not interpreted; use plain prose and bullets.

Push the note to main. The Publish MechLab updates workflow copies only dated files from this directory into the website's public summary dataset. The website builds the latest three summaries into the homepage and all summaries into /news and /updates/YYYY-MM-DD. Corrections to a dated note update the same page. A source link identifies the most recent main-branch commit that changed the note.

Ordinary game commits do not create website entries. Other session summaries, private evidence, game files, and commit bodies are not scanned or published. Keep secrets, private paths, original media, and unreviewed claims out of these notes. Read the repository's distribution policy before adding public material.

If publishing fails, the previous successful site remains available; inspect the workflow in the Actions tab and rerun after correcting the note or configuration. Do not delete the last dated note: empty input fails visibly and retains the previous published summaries.
