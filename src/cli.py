import os
import gkeepapi
import click

from types import SimpleNamespace
from db import DB
from utils import print_note
from keep import Keep
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
	ctx.obj.keep = Keep().login(email)
	ctx.obj.db = DB()


@kapi.command()
@click.option('--dump', type=click.BOOL, default=False)
@click.pass_obj
def test(obj, dump):
	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue.White], archived=False)
	n = next(notes)
	print_note(n)

	if dump:
		state = obj.keep.dump()
		obj.keep.file_dump(state)


@kapi.command()
@click.option('--count', default=PINNED_COUNT)
@click.pass_obj
def pin_oldest(obj, count):
	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue.White], archived=False)
	notes = sorted(notes, key=lambda n: n.timestamps.created)[:count]
	for n in notes:
		print_note(n)
		n.pinned = True

	obj.keep.sync(dump=True)


@kapi.command()
@click.option('--color', default=gkeepapi.node.ColorValue.Gray.name, type=click.Choice([n for n in gkeepapi.node.ColorValue.__members__.keys()],
																					   case_sensitive=False))
@click.option('--archived / --no-archived', default=True)
@click.option('--count', type=int, default=REPEATING_COUNT)
@click.pass_obj
def hide(obj, color, archived, count):
	with obj.db.cursor() as cur:
		for item in cur:
			raise click.Abort("DB isn't empty")

	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue[color]], archived=archived)
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
	obj.db.update(data)
	obj.keep.sync(dump=True)


@kapi.command()
@click.pass_obj
def unhidie(obj):
	with obj.db.cursor() as cur:
		for nid, data in cur:
			note = obj.keep.get(nid)
			data = data.decode()
			title, text = data.split(TEXT_TITLE_SEP, maxsplit=1)
			note.title = title
			note.text = text
			note.archived = True
			note.pinned = False
			print_note(note)

	obj.keep.sync(dump=True)
	obj.db.drop_db()


if __name__ == '__main__':
	# gapi()
	kapi()