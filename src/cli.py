import os
import gkeepapi
import click

from types import SimpleNamespace
from db import DB
from utils import print_note
from keep import Keeep
from settings import DATA_DIR
from google_auth_oauthlib.flow import InstalledAppFlow


PINNED_COUNT = 10
REPEATING_COUNT = 1
TEXT_TITLE_SEP = '\n\n'
CLIENT_SECRETS_FILE = DATA_DIR / "secrets.json"
SCOPES = ['https://www.googleapis.com/auth/memento', 'https://www.googleapis.com/auth/reminders']


@click.command()
def gapi():
	os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
	flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE.as_posix(), gkeepapi.Keep.OAUTH_SCOPES)
	credentials = flow.run_console()
	print(flow.credentials.token)


@click.group()
@click.argument('email')
@click.pass_context
def kapi(ctx, email):
	ctx.obj = SimpleNamespace()
	ctx.obj.keep = Keeep().login(email)
	ctx.obj.db = DB()


@kapi.command()
@click.pass_obj
def test(obj):
	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue.White], archived=False)
	n = next(notes)
	print_note(n)


@kapi.command()
@click.option('--count', default=PINNED_COUNT)
@click.pass_obj
def pin_oldest(keep, count):
	notes = keep.find(colors=[gkeepapi.node.ColorValue.White], archived=False)
	notes = sorted(notes, key=lambda n: n.timestamps.created)[:count]
	for n in notes:
		print_note(n)
		n.pinned = True

	keep.sync(dump=True)


@kapi.command()
@click.option('--color', default=gkeepapi.node.ColorValue.Gray.name, type=click.Choice([n for n in gkeepapi.node.ColorValue.__members__.keys()],
																					   case_sensitive=False))
@click.option('--archived / --no-archived', default=True)
@click.option('--count', type=int, default=REPEATING_COUNT)
@click.pass_obj
def hide(keep, color, archived, count):
	with db.cursor() as cur:
		for item in  cur:
			raise click.Abort("DB isn't empty")

	notes = keep.find(colors=[gkeepapi.node.ColorValue[color]], archived=archived)
	data = {}
	for i, n in enumerate(notes, start=1):
		print_note(n)
		n.pinned = True
		n.archived = False
		data[n.id] = n.title + TEXT_TITLE_SEP + n.text
		n.title = n.text = ''
		if i == count:
			break

	print(len(data))
	db.update(data)

	keep.sync(dump=True)


@kapi.command()
@click.pass_obj
def unhidie(keep):
	with db.cursor() as cur:
		for nid, data in cur:
			note = keep.get(nid)
			data = data.decode()
			title, text = data.split(TEXT_TITLE_SEP, maxsplit=1)
			note.title = title
			note.text = text
			note.archived = True
			note.pinned = False
			print_note(note)

	keep.sync(dump=True)
	drop_db()


if __name__ == '__main__':
	# gapi()
	kapi()