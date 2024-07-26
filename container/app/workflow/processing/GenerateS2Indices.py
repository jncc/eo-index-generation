import luigi
import os
import re
import json
import rpy2.robjects as robjects
import workflow.common.Defaults as defaults
import logging

from luigi.util import requires
from luigi import LocalTarget
from functional import seq
from workflow.processing.PrepareProcessing import PrepareProcessing
from workflow.processing.MaskGranule import MaskGranule

log = logging.getLogger('luigi-interface')


@requires(MaskGranule)
class GenerateS2Indices(luigi.Task):
    productId = luigi.Parameter()
    rFunctionRoot = luigi.Parameter(default=defaults.RFunctionRoot)
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    indices = luigi.parameter.EnumListParameter(
        enum=defaults.S2Indices,
        description="A comma separted list of any of Brightness,EVI,GLI,GNDVI,GRVI,NBR,NDMI,NDVI,NDWI,RB,RDVI,RG,SAVI,SBL",
        default=defaults.S2IndexDefaults["defaultIndices"])
    rBand = luigi.IntParameter(default=defaults.S2IndexDefaults["rBand"])
    gBand = luigi.IntParameter(default=defaults.S2IndexDefaults["gBand"])
    bBand = luigi.IntParameter(default=defaults.S2IndexDefaults["bBand"])
    nirBand = luigi.IntParameter(default=defaults.S2IndexDefaults["nirBand"])
    swirBand1 = luigi.IntParameter(default=defaults.S2IndexDefaults["swirBand1"])
    swirBand2 = luigi.IntParameter(default=defaults.S2IndexDefaults["swirBand2"])
    parallel = luigi.Parameter(default=None)

    def run(self):
        with self.input().open('r') as pp:
            imagePath = (json.load(pp))["maskedArdFile"]

        robjects.r(f"setwd('{self.rFunctionRoot}')")

        r_source = robjects.r['source']

        r_source(os.path.join(self.rFunctionRoot, 'renv/activate.R'))

        functionPath = os.path.join(self.rFunctionRoot, "workflow/FunctionRunS2Indices.R")

        r_source(functionPath)

        runS2Indices = robjects.r['runS2Indices']

        indexList = seq(self.indices) \
            .map(lambda x: x.value) \
            .distinct() \
            .drop_while(lambda x: not len(x.strip())) \
            .reduce(lambda x, y: f"{x}, {y}")

        datestamp = re.findall("([0-9]{8})", self.productId)[0]
        outPath = os.path.join(self.workingFolder, "indices-tifs", "sentinel_2", datestamp[0:4], datestamp[4:6], datestamp[6:8])

        os.makedirs(outPath, exist_ok=True)

        log.info(f"""Generating S2 indices with imagepath - {imagePath}, 
            fileout_path - {outPath}, 
            index - {indexList}, 
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
            indexList,
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
            "indicesFiles": indicesFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, f"GenerateS2Indices{'_' + self.parallel if self.parallel else ''}.json")
        return LocalTarget(outFile)
