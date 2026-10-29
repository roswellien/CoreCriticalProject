"""Render daily notes as static HTML; raw HTML is always escaped."""
from datetime import date
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape
import re
import xml.etree.ElementTree as ET
START = '<!-- mechlab:updates:start -->'
END = '<!-- mechlab:updates:end -->'
REPO = 'https://github.com/roswellien/MW3Recomp-Private'
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

def rows(notes, level=3):
    return '\n'.join(
        f'<a class="update-row" href="updates/{n["date"]}.html"><time datetime="{n["date"]}">{label(n["date"])}</time>'
        f'<div><h{level}>{escape(n["title"])}</h{level}><p>{escape(n["excerpt"])}</p></div>'
        '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6"/></svg></a>' for n in notes)

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
        f'<title>{escape(title)} — Core Critical</title><link rel="icon" href="{prefix}assets/plates/brand-mark.png">'
        f'<link rel="alternate" type="application/rss+xml" title="Core Critical MechLab" href="{prefix}feed.xml">'
        f'<link rel="stylesheet" href="{prefix}styles.css?v=20261019-media"><script src="{prefix}site.js" defer></script></head>'
        '<body class="interior overview"><a class="skip-link" href="#main">Skip to content</a>' + header + '<main id="main">' + content + '</main>' + footer + '</body></html>\n')

def render_site(root, out, notes):
    for note in notes:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', note['date']):
            raise ValueError('Invalid daily note date')
        date.fromisoformat(note['date'])
        if not re.fullmatch(r'[0-9a-f]{40}', note['commit']):
            raise ValueError('Invalid source commit')
    notes.sort(key=lambda n: n['date'], reverse=True)
    render_feed(notes, out)
    homepage = (out / 'index.html').read_text(encoding='utf-8')
    if homepage.count(START) != 1 or homepage.count(END) != 1:
        raise ValueError('Expected one MechLab homepage region')
    before, rest = homepage.split(START)
    _, after = rest.split(END)
    homepage = before + START + '\n' + rows(notes[:3]) + '\n' + END + after
    homepage = homepage.replace('</head>', '<link rel="alternate" type="application/rss+xml" title="Core Critical MechLab" href="feed.xml"></head>', 1)
    (out / 'index.html').write_text(homepage, encoding='utf-8')
    news = '<section class="page-banner"><h1>Latest from the MechLab</h1><p>Daily development summaries from Core Critical.</p></section><section class="page-content" aria-label="Daily summaries">' + rows(notes, level=2) + '</section>'
    (out / 'news.html').write_text(frame(root, 'Latest from the MechLab', 'Daily Core Critical development summaries.', news), encoding='utf-8')
    directory = out / 'updates'
    directory.mkdir(exist_ok=True)
    for n in notes:
        body = '<section class="page-banner"><h1>' + escape(n['title']) + f'</h1><p><time datetime="{n["date"]}">{label(n["date"])}</time></p></section><div class="page-content"><article class="content-section daily-summary">' + prose(n['body']) + '<p class="related-reading"><a href="../news.html">All MechLab updates</a> · ' + f'<a href="{REPO}/commit/{n["commit"]}">View source commit on GitHub</a></p><p class="art-note">The source repository is currently private; GitHub links require collaborator access.</p></article></div>'
        (directory / (n['date'] + '.html')).write_text(frame(root, n['title'], n['excerpt'], body, True), encoding='utf-8')
