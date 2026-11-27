"""Render daily notes as static HTML; raw HTML is always escaped."""
from datetime import date
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import re
import xml.etree.ElementTree as ET
from tools.sync_mechlab import CARD_TAGS
START = '<!-- mechlab:updates:start -->'
END = '<!-- mechlab:updates:end -->'
REPO = 'https://github.com/roswellien/CoreCriticalProject'
SITE = 'https://corecritical.dev'

def render_feed(notes, out):
    """Publish only the already-public summaries, with stable per-day IDs."""
    atom = 'http://www.w3.org/2005/Atom'
    ET.register_namespace('atom', atom)
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    for tag, value in (
        ('title', 'Core Critical MechLab'),
        ('link', SITE + '/news.html'),
        ('description', 'Published Core Critical development updates.'),
        ('language', 'en-us'),
    ):
        ET.SubElement(channel, tag).text = value
    ET.SubElement(channel, '{' + atom + '}link', {
        'href': SITE + '/feed.xml', 'rel': 'self',
        'type': 'application/rss+xml',
    })
    for note in notes:
        item = ET.SubElement(channel, 'item')
        url = SITE + '/updates/' + note['date'] + '.html'
        for tag, value in (
            ('title', note['title']), ('link', url),
            ('description', note['excerpt']),
            ('pubDate', format_datetime(datetime.combine(
                date.fromisoformat(note['date']), datetime.min.time(),
                tzinfo=timezone.utc), usegmt=True)),
        ):
            ET.SubElement(item, tag).text = value
        for tag in note['tags']:
            ET.SubElement(item, 'category').text = tag
        ET.SubElement(item, 'guid', isPermaLink='true').text = url
    ET.indent(rss)
    ET.ElementTree(rss).write(out / 'feed.xml', encoding='utf-8', xml_declaration=True)

def prose(text):
    output, paragraph = [], []
    in_list = False
    def flush():
        if paragraph:
            output.append('<p>' + escape(' '.join(paragraph)) + '</p>')
            paragraph.clear()
    for line in text.splitlines() + ['']:
        if line.startswith('- '):
            flush()
            if not in_list:
                output.append('<ul>')
                in_list = True
            output.append('<li>' + escape(line[2:]) + '</li>')
            continue
        if in_list:
            output.append('</ul>')
            in_list = False
        if line.startswith(('## ', '### ')):
            flush()
            level = 3 if line.startswith('### ') else 2
            output.append(f'<h{level}>' + escape(line[level+1:]) + f'</h{level}>')
        elif not line.strip():
            flush()
        else:
            paragraph.append(line.strip())
    return '\n'.join(output)

def label(day):
    return date.fromisoformat(day).strftime('%d %b %Y').lstrip('0')

def tag_slug(tag):
    return tag.lower()


def tag_list(tags):
    if not tags:
        return ''
    items = ''.join(f'<span class="update-tag">{escape(tag)}</span>' for tag in tags)
    return f'<span class="update-tags">{items}</span>'


def card_media(note):
    """The card's thumbnail, or a quiet brand panel so every card keeps the same shape."""
    if note['image']:
        # The thumbnail only decorates; the card's headline and excerpt carry the meaning.
        image_path = escape(note['image'], quote=True)
        return ('<span class="update-card-media"><img src="assets/plates/' + image_path
                + '" alt="" width="640" height="360" loading="lazy" decoding="async"></span>')
    return ('<span class="update-card-media update-card-blank"><img src="assets/plates/brand-mark-128.webp"'
            ' alt="" width="48" height="48" loading="lazy"></span>')


def cards(notes, level=3):
    rendered = []
    for note in notes:
        tag_names = ' '.join(tag_slug(tag) for tag in note['tags'])
        rendered.append(
            f'<a class="update-card" href="updates/{note["date"]}.html" data-tags="{tag_names}">'
            + card_media(note)
            + '<span class="update-card-body"><span class="update-card-meta">'
            f'<time datetime="{note["date"]}">{label(note["date"])}</time>{tag_list(note["tags"])}</span>'
            f'<h{level}>{escape(note["title"])}</h{level}><p>{escape(note["excerpt"])}</p></span></a>')
    return '<div class="update-cards">' + '\n'.join(rendered) + '</div>'


def tag_filter(notes):
    """Filter buttons for /news. Hidden until site.js wires them up, so visitors without
    JavaScript never see controls that do nothing."""
    used_tags = [tag for tag in CARD_TAGS if any(tag in note['tags'] for note in notes)]
    buttons = ['<button type="button" data-tag="" aria-pressed="true">All</button>']
    for tag in used_tags:
        buttons.append(f'<button type="button" data-tag="{tag_slug(tag)}" aria-pressed="false">{escape(tag)}</button>')
    return ('<div class="update-filter" role="group" aria-label="Filter updates by topic" hidden>'
            + ''.join(buttons) + '</div><p class="update-filter-status" aria-live="polite"></p>')

def frame(root, title, description, content, nested=False):
    about = (root / 'about.html').read_text(encoding='utf-8')
    header = about[about.index('<header'):about.index('</header>')+9].replace(' aria-current="page"', '')
    footer = about[about.index('<footer'):about.index('</footer>')+9]
    if nested:
        for attr in ('href', 'src'):
            header = re.sub(fr'{attr}="(?!https?://|#)([^"]+)"', fr'{attr}="../\1"', header)
            footer = re.sub(fr'{attr}="(?!https?://|#)([^"]+)"', fr'{attr}="../\1"', footer)
    prefix = '../' if nested else ''
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<meta name="description" content="{escape(description, quote=True)}"><meta name="theme-color" content="#141717">'
        f'<title>{escape(title)} — Core Critical</title><link rel="icon" href="{prefix}assets/plates/brand-mark-64.png" type="image/png">'
        f'<link rel="alternate" type="application/rss+xml" title="Core Critical MechLab" href="{prefix}feed.xml">'
        f'<link rel="stylesheet" href="{prefix}styles.css?v=20261128"><script src="{prefix}site.js?v=20261128" defer></script></head>'
        '<body class="interior overview"><a class="skip-link" href="#main">Skip to content</a>' + header + '<main id="main">' + content + '</main>' + footer + '</body></html>\n')

def render_site(root, out, notes):
    for note in notes:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', note['date']):
            raise ValueError('Invalid daily note date')
        date.fromisoformat(note['date'])
        if not re.fullmatch(r'[0-9a-f]{40}', note['commit']):
            raise ValueError('Invalid source commit')
        if note['image'] and not (root / 'assets' / 'plates' / note['image']).is_file():
            raise ValueError(f"{note['date']}.md image not found: assets/plates/{note['image']}")
    notes.sort(key=lambda n: n['date'], reverse=True)
    render_feed(notes, out)
    homepage = (out / 'index.html').read_text(encoding='utf-8')
    if homepage.count(START) != 1 or homepage.count(END) != 1:
        raise ValueError('Expected one MechLab homepage region')
    before, rest = homepage.split(START)
    _, after = rest.split(END)
    homepage = before + START + '\n' + cards(notes[:3]) + '\n' + END + after
    homepage = homepage.replace('</head>', '<link rel="alternate" type="application/rss+xml" title="Core Critical MechLab" href="feed.xml"></head>', 1)
    (out / 'index.html').write_text(homepage, encoding='utf-8')
    news = '<section class="page-banner"><h1>Latest from the MechLab</h1><p>Daily development summaries from Core Critical.</p></section><section class="page-content" aria-label="Daily summaries">' + tag_filter(notes) + cards(notes, level=2) + '</section>'
    (out / 'news.html').write_text(frame(root, 'Latest from the MechLab', 'Daily Core Critical development summaries.', news), encoding='utf-8')
    directory = out / 'updates'
    directory.mkdir(exist_ok=True)
    for n in notes:
        body = '<section class="page-banner"><h1>' + escape(n['title']) + f'</h1><p><time datetime="{n["date"]}">{label(n["date"])}</time>' + tag_list(n['tags']) + '</p></section><div class="page-content"><article class="content-section daily-summary">' + prose(n['body']) + '<p class="related-reading"><a href="../news.html">All MechLab updates</a> · ' + f'<a href="{REPO}/commit/{n["commit"]}">View source commit on GitHub</a></p><p class="art-note">The source repository is currently private; GitHub links require collaborator access.</p></article></div>'
        (directory / (n['date'] + '.html')).write_text(frame(root, n['title'], n['excerpt'], body, True), encoding='utf-8')
