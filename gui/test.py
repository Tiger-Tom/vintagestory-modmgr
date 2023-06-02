import webview
import webview.menu as wm

"""
This example demonstrates how to create an application menu
"""


def change_active_window_content():
    active_window = webview.active_window()
    if active_window:
        active_window.load_html('<h1>You changed this window!</h1>')

def click_me():
    active_window = webview.active_window()
    if active_window:
        active_window.load_html('<h1>You clicked me!</h1>')

def do_nothing():
    pass

def say_this_is_window_2():
    active_window = webview.active_window()
    if active_window:
        active_window.load_html('<h1>This is window 2</h2>')

def open_file_dialog():
    active_window = webview.active_window()
    active_window.create_file_dialog(webview.SAVE_DIALOG, directory='/', save_filename='test.file')


if __name__ == '__main__':
    window_1 = webview.create_window('Application Menu Example', 'https://pywebview.flowrl.com/hello')
    window_2 = webview.create_window('Another Window', html='<h1>Another window to test application menu</h1>')

    menu_items = [
        wm.MenuAction('Change Active Window Content', change_active_window_content),
        wm.Menu(
            'Nothing Here',
            [
                wm.MenuAction('This will do nothing', do_nothing)
            ]
        )
    ]

    webview.start(menu=menu_items)
