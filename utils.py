import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

import backoff
import requests


@backoff.on_exception(backoff.expo,
                      (requests.ConnectionError, requests.Timeout))
def make_request(url: str, params=None) -> requests.Response:
    """Return response of the request to the given `url`.

    Fails if redirect happens.
    """
    resp = requests.get(url, params=params)
    resp.raise_for_status()

    # former `check_for_redirect` function
    # if resp.history:
    #     raise requests.HTTPError('Redirects not allowed.')

    return resp


def get_filename_from_url(url: str) -> str:
    """Return filename with extension from `url`.

    >>> get_filename_from_url('https://example.com/images/test.png')
    'test.png'
    >>> get_filename_from_url('/images/test.png')
    'test.png'
    >>> get_filename_from_url('/shots/test.png')
    'test.png'
    """
    url_path = urlsplit(url).path
    _, filename = os.path.split(unquote(url_path))
    return filename


def get_filepath(filename: str, foldername: str) -> Path:
    folder = Path(foldername)
    folder.mkdir(exist_ok=True)
    return folder.joinpath(filename)
