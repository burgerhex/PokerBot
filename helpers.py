
COMMAND_START = "!"


def is_command(msg):
    return msg.startswith(COMMAND_START)


def capitalize(st):
    return st[0].upper() + st[1:].lower()


def extract_parts(command):
    assert command.startswith(COMMAND_START), "can't extract parts from non-command message"

    # remove command start
    command = command[len(COMMAND_START):]

    # split by space, remove empties, and return
    parts = command.split(" ")

    while "" in parts:
        parts.remove("")

    return parts

