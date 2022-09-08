import time
from typing import Union, Optional
from pathlib import Path
from datetime import datetime

from hvpy.api_groups.movies.queue_movie import queueMovieInputParameters
from hvpy.facade import downloadMovie, getMovieStatus, queueMovie
from hvpy.utils import _add_shared_docstring, save_file

__all__ = [
    "createMovie",
]


@_add_shared_docstring(queueMovieInputParameters)
def createMovie(
    startTime: datetime,
    endTime: datetime,
    layers: str,
    events: str,
    eventsLabels: bool,
    imageScale: float,
    format: str = "mp4",
    frameRate: str = "15",
    maxFrames: Optional[str] = None,
    scale: Optional[bool] = None,
    scaleType: Optional[str] = None,
    scaleX: Optional[float] = None,
    scaleY: Optional[float] = None,
    movieLength: Optional[float] = None,
    watermark: bool = True,
    width: Optional[str] = None,
    height: Optional[str] = None,
    x0: Optional[str] = None,
    y0: Optional[str] = None,
    x1: Optional[str] = None,
    y1: Optional[str] = None,
    x2: Optional[str] = None,
    y2: Optional[str] = None,
    size: int = 0,
    movieIcons: Optional[int] = None,
    followViewport: Optional[int] = None,
    reqObservationDate: Optional[datetime] = None,
    overwrite: bool = False,
    filename: Optional[Union[str, Path]] = None,
    hq: bool = False,
    timeout: float = 5,
) -> Path:
    """
    Automatically creates a movie using `queueMovie`, `getMovieStatus` and
    `downloadMovie` functions.

    Parameters
    ----------
    overwrite
        Whether to overwrite the file if it already exists.
        Default is `False`.
    filename
        The path to save the file to.
        Optional, will default to ``f"{starttime}_{endtime}.{format}"``.
    hq
        Download a higher-quality movie file (valid for "mp4" movies only, ignored otherwise).
        Default is `False`, optional.
    timeout
        The timeout in minutes to wait for the movie to be created.
        Default is 5 minutes.
    {Insert}

    Examples
    --------
    >>> from hvpy import createMovie, DataSource, create_events, create_layers
    >>> from datetime import datetime, timedelta
    >>> movie_location = createMovie(
    ...     startTime=datetime.today() - timedelta(days=15, minutes=5),
    ...     endTime=datetime.today() - timedelta(days=15),
    ...     layers=create_layers([(DataSource.AIA_171, 100)]),
    ...     events=create_events(["AR"]),
    ...     eventsLabels=True,
    ...     imageScale=1,
    ...     filename="my_movie",
    ... )
    >>> # This is to cleanup the file created from the example
    >>> # you don't need to do this
    >>> from pathlib import Path
    >>> Path('my_movie.mp4').unlink()
    """
    input_params = locals()
    # These are used later on but we want to avoid passing
    # them into queueMovie.
    overwrite = input_params.pop("overwrite")
    filename = input_params.pop("filename")
    hq = input_params.pop("hq")
    timeout = input_params.pop("timeout")
    res = queueMovie(**input_params)
    if res.get("error"):
        raise RuntimeError(res["error"])
    timeout_counter = time.time() + 60 * timeout  # Default 5 minutes
    while True:
        status = getMovieStatus(
            id=res["id"],
            format=format,
            token=res["token"],
        )
        if status["status"] in [0, 1]:
            time.sleep(3)
        if status["status"] == 2:
            break
        if time.time() > timeout_counter:
            raise RuntimeError(f"Exceeded timeout of {timeout} minutes.")
        if status["status"] == 3:
            raise RuntimeError(status["error"])
    binary_data = downloadMovie(
        id=res["id"],
        format=format,
        hq=hq,
    )
    if filename is None:
        filename = f"{res['id']}_{startTime.date()}_{endTime.date()}.{format}"
    else:
        filename = f"{filename}.{format}"
    save_file(
        data=binary_data,
        filename=filename,
        overwrite=overwrite,
    )
    return Path(filename)
