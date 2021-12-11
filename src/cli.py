import logging
from types import SimpleNamespace

import gkeepapi
import click
import typer

from utils import print_note
from keep import Keep
from data_layer import database
from app_layer import Application


PINNED_COUNT = 10
REPEATING_COUNT = 1
TEXT_TITLE_SEP = '\n\n'
logger = logging.getLogger()


@click.group()
@click.argument('email')
@click.option('--sync', type=click.BOOL, default=False)
@click.pass_context
def kapi(ctx, email, sync):
	ctx.obj = SimpleNamespace()
	ctx.obj.keep = Keep().login(email, sync=sync)
	ctx.obj.db = database


@kapi.command()
@click.pass_obj
def test(obj):
	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue.White], archived=False)
	n = next(notes)
	print_note(n)


@kapi.command()
@click.pass_obj
def dump_state(obj):
	obj.keep.sync()
	state = obj.keep.dump()
	obj.keep.file_dump(state)


@kapi.command()
@click.option('--dry-run', type=click.BOOL, default=False)
@click.pass_obj
def create_events(obj, dry_run):
	prev_state = obj.keep.dump()
	logger.info('Syncing...')
	obj.keep.sync()
	logger.info('Synced.')
	cur_state = obj.keep.dump()

	obj.keep.file_dump(cur_state)

	if create_events:
		pass


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

	logger.info(len(data))
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


cli = typer.Typer()


@cli.callback()
def main(email: str, ctx: typer.Context, sync: bool = False, log_level: str = 'DEBUG'):
	logging.basicConfig(level=log_level)
	app = Application(email, sync=sync)
	ctx.obj: Application = app


@cli.command()
def create_events(ctx: typer.Context, dry_run: bool = False):
	if dry_run:
		logger.info('Dry run.')
		previous_state, current_state = ctx.obj.get_states()
		events = ctx.obj.make_events(previous_state['nodes'], current_state['nodes'])
		logger.info(len(events))
		logger.info(events)
		return

	ctx.obj.create_events()


@cli.command()
def sync(ctx: typer.Context):
	ctx.obj.sync()


@cli.command()
def test(ctx: typer.Context):
	logger.info(ctx)


if __name__ == '__main__':
	# kapi()
	cli()

