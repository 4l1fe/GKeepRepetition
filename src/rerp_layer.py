import logging

import typer
import pandas as pd

from settings import DATA_DIR
from app_layer import SyncApplication, DataApplication
from constants import LEAST_UPDATED_COUNT, EventType

logger = logging.getLogger()


# @kapi.command()
# @click.option('--color', default=gkeepapi.node.ColorValue.Gray.name, type=click.Choice([n for n in gkeepapi.node.ColorValue.__members__.keys()],
# 																					   case_sensitive=False))
# @click.option('--archived / --no-archived', default=True)
# @click.option('--count', type=int, default=REPEATING_COUNT)
# @click.pass_obj
# def hide(obj, color, archived, count):
# 	with obj.db.cursor() as cur:
# 		for item in cur:
# 			raise click.Abort("DB isn't empty")
#
# 	notes = obj.keep.find(colors=[gkeepapi.node.ColorValue[color]], archived=archived)
# 	data = {}
# 	for i, n in enumerate(notes, start=1):
# 		print_note(n)
# 		n.pinned = True
# 		n.archived = False
# 		data[n.id] = n.title + TEXT_TITLE_SEP + n.text
# 		n.title = n.text = ''
# 		if i == count:
# 			break
#
# 	logger.info(len(data))
# 	obj.db.update(data)
# 	obj.keep.sync_and_dump(dump=True)


# @kapi.command()
# @click.pass_obj
# def unhidie(obj):
# 	with obj.db.cursor() as cur:
# 		for nid, data in cur:
# 			note = obj.keep.get(nid)
# 			data = data.decode()
# 			title, text = data.split(TEXT_TITLE_SEP, maxsplit=1)
# 			note.title = title
# 			note.text = text
# 			note.archived = True
# 			note.pinned = False
# 			print_note(note)
#
# 	obj.keep.sync_and_dump(dump=True)
# 	obj.db.drop_db()

keep_cli = typer.Typer()
charts_cli = typer.Typer()
cli = typer.Typer()
cli.add_typer(keep_cli, name='keep')
cli.add_typer(charts_cli, name='charts')


@keep_cli.callback()
def init_keep_cli(email: str, ctx: typer.Context, log_level: str = 'INFO'):
	logging.basicConfig(level=log_level)
	app = SyncApplication(email)
	ctx.obj: SyncApplication = app


@charts_cli.callback()
def init_charts_cli(ctx: typer.Context, log_level: str = 'INFO'):
	logging.basicConfig(level=log_level)
	app = DataApplication()
	ctx.obj: DataApplication = app


@keep_cli.command()
def create_events(ctx: typer.Context, dry_run: bool = False):
	if dry_run:
		logger.info('Dry run.')
		previous_state, current_state = ctx.obj.sync_and_get_states()
		events = ctx.obj.make_events(previous_state['nodes'], current_state['nodes'])
		logger.info(len(events))
		logger.info(events)
		return

	ctx.obj.create_events()


@keep_cli.command()
def pin_default_least_updated(ctx: typer.Context, count: int = LEAST_UPDATED_COUNT, dry_run: bool = False):
	if dry_run:
		nodes = ctx.obj.find_default_least_updated_iter(count=count)
		for n in nodes:
			logger.info(n)
		return

	ctx.obj.pin_default_least_updated(count=count)


@keep_cli.command()
def test(ctx: typer.Context):
	logger.info(ctx)


@charts_cli.command()
def create_chart(ctx: typer.Context, type_,  w: int = 40, h: int = 10,
				 file: str = DATA_DIR.joinpath('added-chart.png').as_posix()):
	if type_ == EventType.CREATED:
		groups = ctx.obj.get_day_groups_created_notes()
	elif type_ == EventType.UPDATED:
		groups = ctx.obj.get_day_groups_updated_notes()
	elif type_ == EventType.DELETED:
		groups = ctx.obj.get_day_groups_deleted_notes()

	df = pd.DataFrame(groups)
	df.set_index('note_created_date')
	df.index = pd.to_datetime(df.index)
	plot = df.plot.bar()
	plot.figure.set_size_inches(w,h)
	plot.figure.savefig(file)
	logger.info('Saved to %s', file)