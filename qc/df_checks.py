import pandas as pd
from qc.utils import get_logger

logger = get_logger("indices_qc")

__all__ = [
    "check_crs",
    "check_dtype",
    "check_within_range",
    "check_valid_cog",
    "check_nodata",
    "check_extent_match",
    "check_aligned",
    "check_resolution",
    "check_units",
]


def check_crs(df: pd.DataFrame) -> bool:
    if (len(df["crs"].unique()) == 1):
        logger.info(f"CRS is consistent over all files: {df['crs'].unique()}")
        return True
    else:
        logger.error(f"issue with CRS consistency, check QC file")
        return False


def check_dtype(df: pd.DataFrame) -> bool:
    if (len(df["dtype"].unique()) == 1):
        logger.info(f"data type is consistent over all files: {df['dtype'].unique()}")
        return True
    else:
        logger.error(f"issue with data type consistency, check QC file")
        return False


def check_within_range(df: pd.DataFrame) -> bool:
    if (len(df["within_range"].unique()) == 1):
        logger.info(f"index range is consistent over all files: {df['within_range'].unique()}")
        return True
    else:
        logger.error(f"issue with index range consistency, check QC file")
        return False


def check_valid_cog(df: pd.DataFrame) -> bool:
    if (len(df["valid_cog"].unique()) == 1):
        logger.info(f"All files are valid COGS")
        return True
    else:
        logger.error(f"issue with one or more COGS, check QC file")
        return False


def check_nodata(df: pd.DataFrame) -> bool:
    if (len(df["nodata"].unique()) == 1):
        logger.info(f"All files have the same nodata value")
        return True
    else:
        logger.error(f"Inconsistent no data values, check QC file")
        return False


def check_extent_match(df: pd.DataFrame) -> bool:
    if (len(df["extent_match"].unique()) == 1):
        logger.info(f"All files have the same extent")
        return True
    else:
        logger.error(f"Inconsistent extent, check QC file")
        return False


def check_aligned(df: pd.DataFrame) -> bool:
    if (len(df["aligned"].unique()) == 1):
        logger.info(f"All files are pixel aligned")
        return True
    else:
        logger.error(f"Inconsistent pixel alignement, check QC file")
        return False


def check_resolution(df: pd.DataFrame) -> bool:
    if (len(df["is_resolution_10"].unique()) == 1):
        logger.info(f"All files have the same resolution")
        return True
    else:
        logger.error(f"Inconsistent resolution, check QC file")
        return False


def check_units(df: pd.DataFrame) -> bool:
    if (len(df["is_units_m"].unique()) == 1):
        logger.info(f"All files have the same units")
        return True
    else:
        logger.error(f"Inconsistent units, check QC file")
        return False
