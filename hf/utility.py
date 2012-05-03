
def prettyDataSize(size_in_bytes):
    """ Takes a data size in bytes and formats a pretty string. """
    unit = "B"
    size_in_bytes = float(size_in_bytes)
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "kiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "MiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "GiB"
    if size_in_bytes > 1024:
        size_in_bytes /= 1024
        unit = "TiB"
    print size_in_bytes, "%.1f "%size_in_bytes + unit
    return "%.1f "%size_in_bytes + unit