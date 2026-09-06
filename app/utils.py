def info(message):
    print(f"\033[94mINFO:\033[0m     {message}")


def success(message):
    print(f"\033[92mSUCCESS:\033[0m  {message}")


def warning(message):
    print(f"\033[93mWARNING:\033[0m  {message}")


def error(message):
    print(f"\033[91mERROR:\033[0m    {message}")
