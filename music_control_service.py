import asyncio
import websockets
from subprocess import Popen, PIPE


##
# tools
##
def run_applescript(script):
    p = Popen(['osascript', '-'], stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    return (stdout, stderr)


##
# commands
##
def get_volume():
    print('- get_volume')
    script = """
    tell application "Music" 
	    set currentVolume to sound volume
	    currentVolume
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return stdout.strip('\n')

def set_volume(volume):
    print(f'- set_volume: {volume}')
    script = f"""
    tell application "Music" 
	    set the sound volume to {volume}
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return get_volume()

def toggle_play_pause():
    print('- toggle_play_pause')
    script = 'tell application "Music" to playpause'
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')

def next_track():
    print('- next_track')
    script = 'tell application "Music" to play next track'
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')

def prev_track():
    print('- prev_track')
    script = 'tell application "Music" to play previous track'
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    
def set_shuffled(state):
    # state: true, false
    print(f'- set_shuffled: {state}')
    script = f"""
    tell application "Music"
        set shuffle enabled to {state}
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return get_shuffled()

def get_shuffled():
    print('- get_shuffled')
    script = """
    tell application "Music" 
	    set shuffleEnabled to shuffle enabled
        shuffleEnabled
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return stdout.strip('\n').lower()

def set_repeat_state(state):
    # state:  off, all, one
    print(f'- set_repeat_state: {state}')
    script = f"""
    tell application "Music"
        set song repeat to {state}
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return get_repeat_state()

def get_repeat_state():
    print('- get_repeat_state')
    script = """
    tell application "Music" 
	    set songRepeat to song repeat
        songRepeat
    end tell
    """
    stdout, stderr = run_applescript(script)
    print(f'-> stdout: {stdout} , stderr: {stderr}')
    return stdout.strip('\n')


##
# run command
##
def run_cmd(cmd):
    print(f'cmd: {cmd}')
    if len(cmd) == 0:
        return '[error](missing)'
    name = cmd[0]
    if name == 'get_volume':
        result = get_volume()
        return f'[volume]({result})'
    elif name == 'set_volume':
        if len(cmd) == 1:
            return '[set_volume](missing)'
        result = set_volume(cmd[1])
        return f'[set_volume]({result})'
    elif name == 'toggle_play_pause':
        toggle_play_pause()
        return '[toggle_play_pause](ok)'
    elif name == 'next_track':
        next_track()
        return '[next_track](ok)'
    elif name == 'prev_track':
        prev_track()
        return '[prev_track](ok)'
    if name == 'get_shuffled':
        result = get_shuffled()
        return f'[shuffled]({result})'
    elif name == 'set_shuffled':
        if len(cmd) == 1:
            return '[set_shuffled](missing)'
        state = set_shuffled(cmd[1])
        return f'[set_shuffled]({state})'
    if name == 'get_repeat_state':
        result = get_repeat_state()
        return f'[repeat_state]({result})'
    elif name == 'set_repeat_state':
        if len(cmd) == 1:
            return '[set_repeat_state](missing)'
        state = set_repeat_state(cmd[1])
        return f'[set_repeat_state]({state})'
    return '[error](not_found)'


##
# websocket
##
async def handle_connection(websocket):
    try:
        connected_list.append(websocket)
        async for message in websocket:
            print(f'\nmessage: "{message}"')
            cmd = message.split()
            result = run_cmd(cmd)
            for connected in connected_list:
                await connected.send(result)
    except websockets.exceptions.ConnectionClosedError:
        print('> ConnectionClosedError')
    finally:
        connected_list.remove(websocket)

async def main():
    async with websockets.serve(handle_connection, "0.0.0.0", 9487):
        await asyncio.Future()  # run forever


##
# setup and start
##
connected_list = []
asyncio.run(main())
