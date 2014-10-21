def log(msg, level=0):
    print('\t'*level + msg)
    return msg

def warn(msg, level=0):
    msg = 'WARNING: ' + msg
    print('\t'*level + msg)
    return msg

def error(msg, level=0):
    msg = 'ERROR: ' + msg
    print('\t'*level + msg)
    return msg
