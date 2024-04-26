import luigi
import logging
import os
import json
import rpy2.robjects as robjects
import workflow.common.Defaults as defaults

from workflow.processing.PrepareProcessing import PrepareProcessing
from luigi import LocalTarget
from luigi.util import requires
from functional import seq

log = logging.getLogger('luigi-interface')


@requires(PrepareProcessing)
class MaskGranule(luigi.Task):
    rFunctionRoot = luigi.Parameter(default=defaults.RFunctionRoot)
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])

    def run(self):
        with self.input().open('r') as pp:
            files = (json.load(pp))

        robjects.r(f"setwd('{self.rFunctionRoot}')")

        r_source = robjects.r['source']
        r_source(os.path.join(self.rFunctionRoot, 'renv/activate.R'))

        functionPath = os.path.join(self.rFunctionRoot, "workflow/FunctionMaskGranule.R")
        r_source(functionPath)

        r_maskGranule = robjects.r['maskGranule']

        try:
            imgfile = seq(files["ardFiles"]).where(lambda x: "stdsref.tif" in x).head()
        except:
            raise Exception("cannot find stdsref.tif file")

        try:
            cloudfile = seq(files["ardFiles"]).where(lambda x: "cloud" in x).head()
        except:
            raise Exception("cannot find cloud mask file")

        try:
            topofile = seq(files["ardFiles"]).where(lambda x: "topo" in x).head()
        except:
            raise Exception("cannot find topo file")

        log.info(f"Generating masked frame for ImageFile: {imgfile} - CloudFile: {cloudfile} - MaskFile: {topofile}")

        jsonResult = r_maskGranule(imgfile, cloudfile, topofile, self.workingFolder)[0]

        output = json.loads(jsonResult)

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, 'MaskGranule.json')
        return LocalTarget(outFile)
