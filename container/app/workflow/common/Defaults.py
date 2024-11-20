from enum import Enum

Paths = {
    "input": "/input",
    "state": "/state",
    "working": "/working",
    "output": "/output"
}


RFunctionRoot = "/app/r-functions"

ArdBasePath = "/neodc/sentinel_ard/data"


class S1Indices(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    RVI = "RVI"
    VVVH = "VVVH"
    VHVV = "VHVV"
    RFDI = "RFDI"


S1IndexDefaults = {
    "defaultIndices": [S1Indices.RVI, S1Indices.VVVH, S1Indices.VHVV, S1Indices.RFDI],
    "vvBand": 1,
    "vhBand": 2,
    "threshold": 50,
}


class S2Indices(Enum):
    def __repr__(self):
        return '<%s.%s>' % (self.__class__.__name__, self.name)

    Brightness = "Brightness"
    EVI = "EVI"
    EVI2 = "EVI2"
    GLI = "GLI"
    GNDVI = "GNDVI"
    NBR = "NBR"
    NDMI = "NDMI"
    NDVI = "NDVI"
    NDWI = "NDWI"
    RB = "RB"
    RDVI = "RDVI"
    RG = "RG"
    SAVI = "SAVI"
    SBL = "SBL"
    GRVI = "GRVI"


S2IndexDefaults = {
    "defaultIndices": [
        S2Indices.NDVI,
        S2Indices.NDWI,
        S2Indices.NDMI,
        S2Indices.NBR
    ],
    "rBand": 3,
    "gBand": 2,
    "bBand": 1,
    "nirBand": 7,
    "swirBand1": 9,
    "swirBand2": 10,
}


class QcChecks:
    _defaults = {
        "crs": "EPSG:27700",
        "dtype": "float32",
        "nodata": "-9999.0",
        "default_range": {
            "S1": [-504, 504],
            "S2": [-1, 1]
        }
    }

    _range_checks = {
        # Add per-index range checks here
        S2Indices.EVI2: [-5, 5]
    }

    @staticmethod
    def get_defaults():
        return QcChecks._defaults

    @staticmethod
    def get_range(index):
        """
        Get the QC range for a given ARD index

        :param index: The index to get the range for
        :type index: str or S1Indices or S2Indices

        :return: The range for the given index
        :rtype: [int, int]

        :raises ValueError: If the index is not recognised
        """

        if type(index) == str:
            if index in S1Indices.__members__:
                index = S1Indices(index)
            elif index in S2Indices.__members__:
                index = S2Indices(index)

        if isinstance(index, S1Indices):
            return QcChecks._range_checks.get(index, QcChecks._defaults["default_range"]["S1"])
        elif isinstance(index, S2Indices):
            return QcChecks._range_checks.get(index, QcChecks._defaults["default_range"]["S2"])
        else:
            raise ValueError(f"Failed getting QC range. Unknown index : {index}")
