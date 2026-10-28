"""Build the public media gallery and individual mech features."""
from html import escape
import json
import re
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from .render_mechlab import frame

TRAILER = '2olchoLkZro'
YOUTUBE_CHANNEL = 'UC0YGz5FEh7-ij1miUmXECiw'
YOUTUBE_FEED = f'https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL}'


def latest_videos(root):
    """Use YouTube's uploads feed, retaining a local snapshot for offline builds."""
    fallback = json.loads((root / 'data/youtube-latest.json').read_text(encoding='utf-8'))
    try:
        request = Request(YOUTUBE_FEED, headers={'User-Agent': 'CoreCriticalWebsite/1.0'})
        with urlopen(request, timeout=6) as response:
            feed = ElementTree.fromstring(response.read())
        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'yt': 'http://www.youtube.com/xml/schemas/2015',
        }
        videos = []
        for entry in feed.findall('atom:entry', namespaces):
            video_id = entry.findtext('yt:videoId', namespaces=namespaces)
            title = entry.findtext('atom:title', namespaces=namespaces)
            published = entry.findtext('atom:published', namespaces=namespaces)
            if video_id and re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id) and title and published:
                videos.append({'id': video_id, 'title': title, 'published': published[:10]})
        if videos:
            return videos[:8]
    except (OSError, ElementTree.ParseError, ValueError) as error:
        print(f'YouTube feed unavailable; using saved video list: {error}')
    return fallback[:8]


def video_carousel(videos):
    cards = []
    for index, video in enumerate(videos):
        video_id = video['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', video_id):
            raise ValueError(f'Invalid YouTube video ID: {video_id}')
        title = escape(video['title'])
        published = escape(video['published'])
        featured_class = ' youtube-card-featured' if index == 0 else ''
        badge = '<span class="youtube-card-badge">Newest video</span>' if index == 0 else ''
        cards.append(
            f'<a class="youtube-card{featured_class}" href="https://www.youtube.com/watch?v={video_id}" '
            f'target="_blank" rel="noopener noreferrer" aria-label="Watch {title} on YouTube">'
            + badge +
            f'<img src="https://i.ytimg.com/vi/{video_id}/hqdefault.jpg" alt="" '
            'width="480" height="360" loading="lazy">'
            f'<span class="youtube-card-title">{title}</span>'
            f'<time datetime="{published}">{published}</time></a>'
        )
    return (
        '<section class="youtube-latest" aria-labelledby="youtube-latest-heading">'
        '<div class="youtube-carousel-heading"><div><h2 id="youtube-latest-heading">Latest on YouTube</h2>'
        '<p>The newest upload leads the lineup. Fresh videos appear automatically.</p></div>'
        '<div class="youtube-carousel-controls">'
        '<button type="button" data-carousel-prev aria-label="Previous videos">←</button>'
        '<button type="button" data-carousel-next aria-label="Next videos">→</button></div></div>'
        '<div class="youtube-carousel" tabindex="0" aria-label="Latest Core Critical videos">'
        + ''.join(cards) + '</div></section>'
    )


def trailer():
    return ('<div class="video-frame"><iframe src="https://www.youtube-nocookie.com/embed/' + TRAILER + '" '
            'title="Core Critical: MW3 announcement trailer" loading="lazy" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
            'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>')


def media_nav(active, nested=False):
    prefix = '../' if nested else ''
    links = [('media.html', 'All media'), ('media-mechs.html', 'Mechs'), ('media-gameplay.html', 'Gameplay')]
    return '<nav class="media-nav" aria-label="Media categories">' + ''.join(
        f'<a href="{prefix}{url}"' + (' aria-current="page"' if label == active else '') + f'>{label}</a>'
        for url, label in links) + '</nav>'


def page(root, title, description, content, nested=False):
    html = frame(root, title, description, content, nested)
    home = (root / 'index.html').read_text(encoding='utf-8')
    nav = home[home.index('<nav class="primary-nav"'):home.index('</nav>') + 6]
    if nested:
        import re
        nav = re.sub(r'href="(?!https?://)([^"]+)"', r'href="../\1"', nav)
    old_nav = html[html.index('<nav class="primary-nav"'):html.index('</nav>') + 6]
    html = html.replace(old_nav, nav)
    href = '../media.html' if nested else 'media.html'
    return html.replace(f'href="{href}">Media', f'href="{href}" aria-current="page">Media')


def mech_link(m, media_base):
    return (f'<a class="mech-tile" href="mechs/{m["slug"]}.html">'
            f'<img src="{media_base}/{m["slug"]}.jpg" alt="{escape(m["name"])} in the development build" '
            'width="960" height="540" loading="lazy">'
            f'<div><h2>{escape(m["name"])}</h2><p>{escape(m["alias"] or m["focus"])}</p>'
            '<span class="text-link">View mech &amp; orbit video <span aria-hidden="true">→</span></span></div></a>')


def render_media(root, out):
    mechs = json.loads((root / 'data/media-mechs.json').read_text(encoding='utf-8'))
    assets = json.loads((root / 'data/media-assets.json').read_text(encoding='utf-8'))
    media_base = assets['base_url'].rstrip('/')
    from urllib.parse import urlsplit
    origin = urlsplit(media_base)
    if origin.scheme != 'https' or not origin.hostname or origin.query or origin.fragment:
        raise ValueError('Published media needs an HTTPS base URL without a query or fragment')
    for m in mechs:
        for suffix in ('mp4', 'jpg'):
            name = f'{m["slug"]}.{suffix}'
            if name not in assets['files'] or assets['files'][name]['bytes'] <= 0:
                raise ValueError(f'Missing published media identity: {name}')
    intro = '<header class="media-intro"><h1>Media</h1><p>Meet the mechs. See the game in motion.</p></header>'
    content = ('<div class="media-shell">' + intro + media_nav('All media') +
        video_carousel(latest_videos(root)) +
        '<section class="media-trailer" aria-labelledby="trailer-heading"><div><h2 id="trailer-heading">Announcement trailer</h2>'
        '<p>A first look at Core Critical: MW3. Familiar battlefields, rebuilt mech visuals, and lighting in development.</p>'
        '<a class="text-link" href="media-gameplay.html">Explore Gameplay <span aria-hidden="true">→</span></a></div>' + trailer() + '</section>'
        '<section class="category-preview" aria-labelledby="mechs-heading"><div class="section-heading"><h2 id="mechs-heading">Mechs</h2>'
        '<a class="text-link" href="media-mechs.html">Browse all mechs <span aria-hidden="true">→</span></a></div>'
        '<p>Individual profiles and in-game orbit videos from the development build.</p>'
        '<div class="mech-grid">' + ''.join(mech_link(m, media_base) for m in mechs[:3]) + '</div></section></div>')
    (out / 'media.html').write_text(page(root, 'Media', 'Core Critical mech features, orbit videos and gameplay.', content), encoding='utf-8')
    content = ('<div class="media-shell"><header class="media-intro"><h1>Mechs</h1><p>Explore the machines of Core Critical: MW3, one chassis at a time.</p></header>' + media_nav('Mechs') +
        '<p class="gallery-intro">Open a feature for a closer look and its in-game orbit video. These captures show work in progress.</p>'
        '<div class="mech-grid">' + ''.join(mech_link(m, media_base) for m in mechs) + '</div></div>')
    (out / 'media-mechs.html').write_text(page(root, 'Mechs', 'Explore mech profiles and in-game orbit videos from Core Critical: MW3.', content), encoding='utf-8')
    content = ('<div class="media-shell"><header class="media-intro"><h1>Gameplay</h1><p>Footage from the worlds we’re bringing forward.</p></header>' + media_nav('Gameplay') +
        '<article class="gameplay-feature"><h2>Core Critical: MW3 — Announcement trailer</h2><p class="feature-lead">Original gameplay. A modern core.</p>' + trailer() +
        '<div class="feature-copy"><p>Watch the announcement trailer for our AI-developed, human-directed recompilation project. '
        'Explore familiar environments and upgraded mech visuals, alongside dynamic lighting, shadows, normal mapping, and night combat effects in development.</p>'
        '<p>The trailer shows the development build. Features and visuals continue to change as testing progresses.</p>'
        '<a class="text-link" href="https://www.youtube.com/watch?v=' + TRAILER + '">Watch on YouTube <span aria-hidden="true">↗</span></a></div></article></div>')
    (out / 'media-gameplay.html').write_text(page(root, 'Gameplay', 'Watch the Core Critical: MW3 announcement trailer.', content), encoding='utf-8')
    directory = out / 'mechs'
    directory.mkdir(exist_ok=True)
    for i, m in enumerate(mechs):
        alias = f'<p class="mech-alias">Also known as {escape(m["alias"])}.</p>' if m['alias'] else ''
        content = ('<div class="media-shell mech-feature">' + media_nav('Mechs', True) +
            '<a class="back-link" href="../media-mechs.html">← All mechs</a><header class="mech-heading">'
            f'<h1>{escape(m["name"])}</h1>{alias}<p class="feature-lead">{escape(m["focus"])}</p></header>'
            f'<video class="mech-video" controls playsinline preload="none" poster="{media_base}/{m["slug"]}.jpg" '
            f'aria-label="{escape(m["name"])} in-game orbit video"><source src="{media_base}/{m["slug"]}.mp4" type="video/mp4">'
            f'Your browser does not support this video. <a href="{media_base}/{m["slug"]}.mp4">Open the orbit video</a>.</video>'
            '<div class="mech-details"><section><h2>About the ' + escape(m['name']) + '</h2><p>' + escape(m['profile']) + '</p>'
            '<p>' + escape(m['project']) + '</p></section><section><h2>In this preview</h2><dl>'
            f'<div><dt>Location</dt><dd>{escape(m["location"])}</dd></div><div><dt>Lighting</dt><dd>{escape(m["lighting"])}</dd></div>'
            f'<div><dt>Video</dt><dd>{m["duration"]} seconds · 1080p · 60 FPS · Silent</dd></div></dl>'
            '<p class="preview-note">Captured in-game with the orbit camera. Development footage; visuals may change. Capture frame rate is not a gameplay performance benchmark.</p>'
            '</section></div><nav class="mech-pagination" aria-label="More mech features">' +
            f'<a href="{mechs[(i-1)%len(mechs)]["slug"]}.html">← {escape(mechs[(i-1)%len(mechs)]["name"])}</a>'
            f'<a href="{mechs[(i+1)%len(mechs)]["slug"]}.html">{escape(mechs[(i+1)%len(mechs)]["name"])} →</a></nav></div>')
        (directory / f'{m["slug"]}.html').write_text(page(root, m['name'], m['profile'], content, True), encoding='utf-8')
