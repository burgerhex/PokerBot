
COMMAND_START = "!"


def is_command(msg):
    return msg.startswith(COMMAND_START)


def capitalize(st):
    return st[0].upper() + st[1:].lower()


def extract_parts(command):
    assert command.startswith(COMMAND_START), "can't extract parts from non-command message"

    command = command[len(COMMAND_START):]
    parts = command.split(" ")

    while "" in parts:
        parts.remove("")

    return parts


def english_list(ls, func=lambda x: x):
    ls = [func(elem) for elem in ls]

    if len(ls) == 0:
        return ""
    elif len(ls) == 1:
        return str(ls[0])
    elif len(ls) == 2:
        return f"{str(ls[0])} and {str(ls[1])}"
    else:
        result = ""

        for item in ls[:-1]:
            result += str(item) + ", "

        return result + "and " + str(ls[-1])
