import luigi
import os
import re
import json
import rpy2.robjects as robjects
import workflow.common.Defaults as defaults
import logging

from luigi.parameter import EnumParameter
from luigi import LocalTarget
from functional import seq

log = logging.getLogger('luigi-interface')


class GenerateS2Index(luigi.Task):
    productId = luigi.Parameter()
    rFunctionRoot = luigi.Parameter(default=defaults.RFunctionRoot)
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    index = luigi.parameter.EnumParameter(
        enum=defaults.S2Indices,
        description="One of Brightness,EVI,GLI,GNDVI,GRVI,NBR,NDMI,NDVI,NDWI,RB,RDVI,RG,SAVI,SBL")
    rBand = luigi.IntParameter(default=defaults.S2IndexDefaults["rBand"])
    gBand = luigi.IntParameter(default=defaults.S2IndexDefaults["gBand"])
    bBand = luigi.IntParameter(default=defaults.S2IndexDefaults["bBand"])
    nirBand = luigi.IntParameter(default=defaults.S2IndexDefaults["nirBand"])
    swirBand1 = luigi.IntParameter(default=defaults.S2IndexDefaults["swirBand1"])
    swirBand2 = luigi.IntParameter(default=defaults.S2IndexDefaults["swirBand2"])

    ardFiles = luigi.Parameter()
    _stateFileName = luigi.Parameter()

    def run(self):
        imagePath = self.ardFiles

        robjects.r(f"setwd('{self.rFunctionRoot}')")

        r_source = robjects.r['source']

        r_source(os.path.join(self.rFunctionRoot, 'renv/activate.R'))

        functionPath = os.path.join(self.rFunctionRoot, "workflow/FunctionRunS2Indices.R")

        r_source(functionPath)

        runS2Indices = robjects.r['runS2Indices']

        datestamp = re.findall("([0-9]{8})", self.productId)[0]
        outPath = os.path.join(self.workingFolder, "indices-tifs", "sentinel_2", datestamp[0:4], datestamp[4:6], datestamp[6:8])

        os.makedirs(outPath, exist_ok=True)

        log.info(f"""Generating S2 indices with imagepath - {imagePath}, 
            fileout_path - {outPath}, 
            index - {self.index.value.strip()}, 
            r - {self.rBand}, 
            g - {self.gBand}, 
            b - {self.bBand},
            nir - {self.nirBand},
            swir1 - {self.swirBand1},
            swir2 - {self.swirBand2}""")

        rawData = runS2Indices(
            self.productId,
            imagePath,
            outPath,
            self.index.value.strip(),
            self.rBand,
            self.gBand,
            self.bBand,
            self.nirBand,
            self.swirBand1,
            self.swirBand2
        )

        indicesFiles = json.loads(rawData[0])

        if len(indicesFiles) == 0:
            raise Exception("No indices have been computed")

        output = {
            "indicesFiles": indicesFiles[0] if len(indicesFiles) == 1 else indicesFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)
