from config import COLOR_NAME_MAP


def get_color_name(color):
    return COLOR_NAME_MAP.get(color, str(color))