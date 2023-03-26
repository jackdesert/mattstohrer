import sys

from run import CacheUtil

if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise ValueError('ERROR: Include the url whose cache to invalidate')
    url = sys.argv[1]
    CacheUtil.invalidate(url)
