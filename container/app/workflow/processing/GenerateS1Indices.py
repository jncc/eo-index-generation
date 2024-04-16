import luigi
import os
import json
import logging
import re
import rpy2.robjects as robjects
import workflow.common.Defaults as defaults

from luigi.util import requires
from luigi.parameter import EnumListParameter
from luigi import LocalTarget
from functional import seq
from workflow.processing.PrepareProcessing import PrepareProcessing
from workflow.processing.GenerateSpatialFrameworkSubset import GenerateSpatialFrameworkSubsetForS1

log = logging.getLogger('luigi-interface')

# Make task dependent on spatial framework subset to ensure no time
# is wasted computing indices for a granule that has no polygons


@requires(PrepareProcessing, GenerateSpatialFrameworkSubsetForS1)
class GenerateS1Indices(luigi.Task):
    sentinelFrameId = luigi.Parameter()
    rFunctionRoot = luigi.Parameter(default=defaults.RFunctionRoot)
    workingFolder = luigi.Parameter(default=defaults.Paths["output"])
    vvBand = luigi.IntParameter(default=defaults.S1IndexDefaults["vvBand"])
    vhBand = luigi.IntParameter(default=defaults.S1IndexDefaults["vhBand"])
    threshold = luigi.IntParameter(default=defaults.S1IndexDefaults["threshold"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    indices = EnumListParameter(
        enum=defaults.S1Indices,
        description="A comma separated list of any of RVI,VVVH,VHVV,RFDI",
        default=defaults.S1IndexDefaults["defaultIndices"])

    def run(self):
        with self.input()[0].open('r') as pp:
            ardFiles = (json.load(pp))["ardFiles"]

        robjects.r(f"setwd('{self.rFunctionRoot}')")

        r_source = robjects.r['source']

        r_source(os.path.join(self.rFunctionRoot, 'renv/activate.R'))

        functionPath = os.path.join(self.rFunctionRoot, "FunctionRunS1Indices.R")
        r_source(functionPath)

        runS1Indices = robjects.r['runS1Indices']

        imagePath = seq(ardFiles) \
            .filter(lambda x: x.lower().endswith(".tif")) \
            .first()

        indices = seq(self.indices) \
            .map(lambda x: x.value) \
            .distinct() \
            .drop_while(lambda x: not len(x.strip())) \
            .reduce(lambda x, y: f"{x}, {y}")

        datestamp = re.findall("([0-9]{8})", self.sentinelFrameId)[0]
        outPath = os.path.join(self.workingFolder, "indices-tifs", "sentinel_1", datestamp[0:4], datestamp[4:6], datestamp[6:8])

        if not os.path.exists(outPath):
            os.makedirs(outPath)

        log.info(f"""Generating S1 indices with imagepath - {imagePath}, 
            fileout_path - {outPath}, 
            index - {indices}, 
            vh - {self.vvBand}, 
            vv - {self.vhBand},
            threshold - {self.threshold}""")

        rawData = runS1Indices(
            self.sentinelFrameId,
            imagePath,
            outPath,
            self.vvBand,
            self.vhBand,
            indices,
            self.threshold)

        indicesFiles = json.loads(rawData[0])

        if len(indicesFiles) == 0:
            raise Exception("No indices have been computed")

        output = {
            "indicesFiles": indicesFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, 'GenerateS1Indices.json')
        return LocalTarget(outFile)
