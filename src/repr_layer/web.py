from nicegui import ui


with ui.card().tight():
    ui.label('WOOO')
    with ui.card_section():
        with ui.row():
            ui.button(on_click=lambda: ui.notify('button was pressed')).props('color=green icon=done round')
            ui.button(on_click=lambda: ui.notify('button was pressed')).props('color=red icon=close round')
     
ui.run()
