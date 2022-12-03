import shlex
from os import environ, ttyname
from subprocess import PIPE, Popen, check_output, CalledProcessError
from sys import platform, stdout


def shell_output(cmd):
    return check_output(shlex.split(cmd)).decode()


def tmux_is_focused():
    if "TMUX" not in environ:
        return False

    cur_pane = environ['TMUX_PANE']

    # Let's interpret 'window active' as focused.
    # Previously only 'pane active' was regarded as focused, but that makes too many notification
    cmd = 'tmux list-panes -F "#{pane_id}:#{window_active}:#{session_attached}"'
    panes = shell_output(cmd)

    return True if panes.find(cur_pane + ':1:1') != -1 else False


def linux_window_is_focused():
    xprop_cmd = shlex.split('xprop -root _NET_ACTIVE_WINDOW')
    try:
        xprop_window_id = int(shell_output(xprop_cmd).split()[-1], 16)
    except CalledProcessError:
        return False
    except ValueError:
        return False
    except OSError as e:
        if 'No such file' in e.strerror:
            return False
        else:
            raise
    env_window_id = int(environ.get('WINDOWID', '0'))
    return env_window_id == xprop_window_id


def osascript_tell(app, script):
    p = Popen(['osascript'], stdin=PIPE, stdout=PIPE)
    stdout, stderr = p.communicate(
        ('tell application "{}"\n{}\nend tell'.format(app, script)
         .encode('utf-8')))
    return stdout.decode('utf-8').rstrip('\n')


def darwin_iterm2_shell_is_focused():
    focused_tty = osascript_tell(
        'iTerm',
        'tty of current session of current window',
    )
    return focused_tty == ttyname(stdout.fileno())


def darwin_terminal_shell_is_focused():
    focused_tty = osascript_tell(
        'Terminal',
        'tty of (first tab of (first window whose frontmost is true) '
        'whose selected is true)',
    )
    return focused_tty == ttyname(stdout.fileno())


def darwin_app_shell_is_focused():
    current_appid = {
        'iTerm.app': 'iTerm2',
        'Apple_Terminal': 'Terminal',
    }.get(environ.get('TERM_PROGRAM'))
    focused_appid = osascript_tell(
        'System Events',
        'name of first application process whose frontmost is true',
    )
    if current_appid == focused_appid:
        return {
            'Terminal': darwin_terminal_shell_is_focused,
            'iTerm2': darwin_iterm2_shell_is_focused,
        }[current_appid]()


def is_focused():
    if "TMUX" in environ:
        return tmux_is_focused()

    if platform.startswith('linux') and environ.get('DISPLAY'):
        return linux_window_is_focused()
    elif platform == 'darwin':
        return darwin_app_shell_is_focused()

    return False
