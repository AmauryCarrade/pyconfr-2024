import json
from pathlib import Path

from babel.dates import format_date, format_time, format_timedelta
from datetime import date, time, timedelta
from flask import Flask, Response, render_template
from flask_frozen import Freezer
from markdown2 import Markdown
from sassutils.wsgi import SassMiddleware
from slugify import slugify

app = Flask(__name__, static_url_path='/2024/static')
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'pyconfr': {
        'sass_path': 'static/sass',
        'css_path': 'static/css',
        'wsgi_path': '/2024/static/css',
        'strip_extension': True}})
with (Path(app.root_path) / 'schedule.json').open() as fd:
    SCHEDULE = json.load(fd)
_GIT_MAIN = Path(app.root_path) / '.git' / 'refs' / 'heads' / 'main'
GIT_VERSION = _GIT_MAIN.read_text().strip()[:7]


@app.template_filter()
def slug(string):
    return slugify(string, max_length=30)


TALK_CATEGORIES = {
    slug(talk['submission_type']['en']): talk['submission_type']
    for dates in
    tuple(SCHEDULE['schedule'].values()) + tuple(SCHEDULE['sprints'].values())
    for hours in dates.values()
    for talk in hours.values()
}


@app.template_filter()
def format_duration(minutes):
    return format_timedelta(
        timedelta(seconds=minutes*60), threshold=10, format='short')


@app.template_filter()
def format_day(day, lang):
    day_date = date.fromisoformat(day)
    return format_date(day_date, format='full', locale=lang)


@app.template_filter()
def format_minutes(minutes, lang):
    hour_time = time(int(minutes) // 60, int(minutes) % 60)
    return format_time(hour_time, format='short', locale=lang)


@app.template_filter()
def markdown(string):
    return Markdown().convert(string)


@app.template_filter()
def ical_datetime(string):
    return string.replace('-', '').replace(':', '').split('+')[0]


@app.template_filter()
def ical_text(string):
    return string.replace('\n', '\n\t')


@app.template_filter()
def version(url):
    return f'{url}?{GIT_VERSION}'


@app.route('/')
@app.route('/2024/')
@app.route('/2024/<lang>/<name>.html')
def page(name='index', lang='fr'):
    return render_template(
        f'{lang}/{name}.jinja2.html', page_name=name, lang=lang,
        schedule=SCHEDULE)


@app.route('/2024/<lang>/talks/<category>.html')
def talks(lang, category):
    return render_template(
        f'{lang}/talks.jinja2.html', lang=lang, page_name='talks',
        category=category, title=TALK_CATEGORIES[category][lang],
        schedule=SCHEDULE, categories=TALK_CATEGORIES)


@app.route('/2024/<lang>/full-schedule.html')
def schedule(lang):
    return render_template(
        'schedule.jinja2.html', page_name='full-schedule', lang=lang,
        schedule=SCHEDULE)


@app.route('/2024/<lang>/calendar.ics')
def calendar(lang):
    ics = render_template('calendar.jinja2.ics', lang=lang, schedule=SCHEDULE)
    return Response(ics, mimetype='text/calendar')


@app.cli.command('freeze')
def freeze():
    Freezer(app).freeze()
