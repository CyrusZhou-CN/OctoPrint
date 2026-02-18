from typing import Optional, Union

from pydantic import Field

from octoprint.schema import BaseModel, BaseModelExtra
from octoprint.vendor.with_attrs_docs import with_attrs_docs


@with_attrs_docs
class ApiAnalysisVolume(BaseModel):
    minX: float
    """Minimum X"""
    minY: float
    """Minimum Y"""
    minZ: float
    """Minimum Z"""
    maxX: float
    """Maximum X"""
    maxY: float
    """Maximum Y"""
    maxZ: float
    """Maximum Z"""


@with_attrs_docs
class ApiAnalysisDimensions(BaseModel):
    width: float
    """Width (X axis)"""
    height: float
    """Height (Z axis)"""
    depth: float
    """Depth (Y axis)"""


@with_attrs_docs
class ApiAnalysisFilamentUse(BaseModel):
    length: Optional[float] = None
    """Length of used filament"""
    volume: Optional[float] = None
    """Volume of used filament"""
    weight: Optional[float] = None
    """Weight of used filament"""


@with_attrs_docs
class ApiEntryAnalysis(BaseModelExtra):
    printingArea: Optional[ApiAnalysisVolume] = None
    """Bounding box of coordinates where extrusion happened"""
    dimensions: Optional[ApiAnalysisDimensions] = None
    """Size of the bounding box where extrusion happened"""
    travelArea: Optional[ApiAnalysisVolume] = None
    """Bounding box of coordinates where movement happened"""
    travelDimensions: Optional[ApiAnalysisDimensions] = None
    """Size of the bounding box where movement happened"""
    estimatedPrintTime: Optional[float] = None
    """Estimated print time in minutes"""
    filament: dict[str, ApiAnalysisFilamentUse] = {}
    """Estimated filament use, mapping tool to stats"""


@with_attrs_docs
class ApiEntryLastPrint(BaseModel):
    success: bool
    """Whether the print was successful or not"""
    date: float
    """When the print happened"""
    printerProfile: Optional[str] = None
    """Used printer profile"""
    printTime: Optional[float] = None
    """Print duration"""


@with_attrs_docs
class ApiEntryPrints(BaseModel):
    success: int = 0
    """Number of successful prints"""
    failure: int = 0
    """Number of failed prints"""
    last: Optional[ApiEntryLastPrint] = None
    """Information about the last print"""


@with_attrs_docs
class ApiEntryStatistics(BaseModelExtra):
    averagePrintTime: dict[str, float] = {}
    """Average print time of this item per printer profile"""
    lastPrintTime: dict[str, float] = {}
    """Last print time of this item per printer profile"""


@with_attrs_docs
class ApiStorageEntry(BaseModelExtra):
    name: str
    """Internal name"""
    display: str
    """Display name"""
    origin: str
    """Storage this item belongs to"""
    path: str
    """Path of item in storage"""
    user: Optional[str] = None
    """User who created the item"""

    date: Optional[int] = None
    """Last modification date of entry"""
    size: Optional[int] = None
    """Size of entry in bytes"""

    type_: str = Field(serialization_alias="type")
    """Entry type, possible values are currently ``folder``, ``machinecode`` & ``model``"""
    typePath: list[str]
    """Full type path"""

    prints: Optional[ApiEntryPrints] = None
    """Print stats"""

    refs: dict[str, str] = {}
    """
    Other URLs related to this item.

    Currently supported:

    * ``resource``: The HTTP resource that represents the file or folder (so, a URL).
    * ``download``: The download URL for the file. Never present for folders. Also not present
      if the parent storage of the file doesn't support ``read_file``. Never present for folders.
    * ``model``: The model from which this file was generated, if known. Never present for folders.
    """


@with_attrs_docs
class ApiStorageFolder(ApiStorageEntry):
    children: list[Union["ApiStorageFile", "ApiStorageFolder"]] = []
    """Folder contents (files & other folders)"""

    type_: str = Field("folder", serialization_alias="type")
    """Always ``folder`` for folders"""
    typePath: list[str] = ["folder"]
    """Always ``["folder"]`` for folders"""


@with_attrs_docs
class ApiStorageFile(ApiStorageEntry):
    gcodeAnalysis: Optional[ApiEntryAnalysis] = None
    """GCODE analysis result"""

    statistics: Optional[ApiEntryStatistics] = None
    """Print statistics"""


@with_attrs_docs
class ApiAddedEntry(BaseModel):
    name: str
    """Internal name"""
    display: str
    """Display name"""
    origin: str
    """Storage this item belongs to"""
    path: str
    """Path of item in storage"""
    refs: dict[str, str] = {}
    """
    Other URLs related to this item.

    Currently supported:

    * ``resource``: The HTTP resource that represents the file or folder (so, a URL)
    * ``download``: The download URL for the file. Never present for folders. Also not present
      if the parent storage of the file doesn't support ``read_file``.
    * ``model``: The model from which this file was generated, if known. Never present for folders.
    """


@with_attrs_docs
class ApiStorageUsage(BaseModel):
    free: int
    """Free space on storage, in bytes"""

    total: int
    """Total space on storage, in bytes"""


@with_attrs_docs
class ApiStorageData(BaseModelExtra):
    key: str
    """Storage key"""

    name: str
    """Storage name"""

    capabilities: dict[str, bool]
    """Storage capabilities"""

    files: list[Union[ApiStorageFile, ApiStorageFolder]]
    """Files and folders on storage"""

    usage: Optional[ApiStorageUsage] = None
    """Usage information about storage"""


ReadGcodeFilesResponse = dict[str, ApiStorageData]


@with_attrs_docs
class ReadGcodeFilesResponse_pre_1_12(BaseModel):
    files: list[Union[ApiStorageFile, ApiStorageFolder]]
    """List of files and folders from all storages"""
    free: int
    """Free space on local storage in bytes"""
    total: int
    """Total space on local storage in bytes"""


ReadGcodeFilesForOriginResponse = ApiStorageData


@with_attrs_docs
class ReadGcodeFilesForOriginResponse_pre_1_12(BaseModel):
    files: list[Union[ApiStorageFile, ApiStorageFolder]]
    """List of files and folders from storage"""
    free: Optional[int] = None
    """Free space on storage in bytes, if available"""
    total: Optional[int] = None
    """Total space on storage in bytes, if available"""


@with_attrs_docs
class UploadResponse(BaseModel):
    file: Optional[ApiAddedEntry] = None
    """
    (File only) Information regarding the file that was just uploaded, mapped by the storage that it was uploaded to.
    """
    folder: Optional[ApiAddedEntry] = None
    """(Folder only) Information regarding the folder that was just created"""
    done: bool
    """
    Whether any file processing after upload has already finished (``true``) or not, e.g.
    due to first needing to perform a slicing step (``false``).

    Clients may use this information to direct progress displays related to the upload.
    Always ``true`` for folders.
    """
    effectiveSelect: Optional[bool] = None
    """
    (File only) Whether the file that was just uploaded was selected for printing (``true``)
    or not (``false``). If this is ``false`` but was requested to be ``true`` in the upload request,
    the user lacked permissions, the printer was not operational or already printing and thus
    the request could not be fulfilled.
    """
    effectivePrint: Optional[bool] = None
    """
    (File only) Whether the file that was just uploaded was started on the printer (``true``)
    or not (``false``). If this is ``false`` but was requested to be ``true`` in the upload request,
    the user lacked permissions, the printer was not operational or already printing and thus
    the request could not be fulfilled.
    """


@with_attrs_docs
class UploadResponse_pre_1_12(BaseModel):
    files: Optional[dict[str, ApiAddedEntry]] = None
    """
    (File only) Information regarding the file that was just uploaded, mapped by the storage that it was uploaded to.
    Will only ever contain a single entry.
    """
    folder: Optional[ApiAddedEntry] = None
    """(Folder only) Information regarding the folder that was just created"""
    done: bool
    """
    Whether any file processing after upload has already finished (``true``) or not, e.g.
    due to first needing to perform a slicing step (``false``).

    Clients may use this information to direct progress displays related to the upload.
    Always ``true`` for folders.
    """
    effectiveSelect: Optional[bool] = None
    """
    (File only) Whether the file that was just uploaded was selected for printing (``true``)
    or not (``false``). If this is ``false`` but was requested to be ``true`` in the upload request,
    the user lacked permissions, the printer was not operational or already printing and thus
    the request could not be fulfilled.
    """
    effectivePrint: Optional[bool] = None
    """
    (File only) Whether the file that was just uploaded was started on the printer (``true``)
    or not (``false``). If this is ``false`` but was requested to be ``true`` in the upload request,
    the user lacked permissions, the printer was not operational or already printing and thus
    the request could not be fulfilled.
    """
