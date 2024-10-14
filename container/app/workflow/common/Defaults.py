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


QcChecks = {
    "crs": "EPSG:27700",
    "dtype": "float32",
    "nodata": "-9999.0",
    "range": {
        "S1": [-504, 504],
        "S2": [-1, 1]
    }
}


CogProcess = {
    "maxCogProcesss": 4
}
