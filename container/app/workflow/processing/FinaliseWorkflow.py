import luigi
import os
import json

import workflow.common.Defaults as defaults
from workflow.processing.ValidateIndices import ValidateIndicesForS1
from workflow.processing.ValidateIndices import ValidateIndicesForS2

from luigi import LocalTarget
from luigi.parameter import EnumListParameter


class FinaliseWorkflow(luigi.Task):
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    productId = luigi.Parameter()
    indices = ""

    _stateFileName = ""
    _satellite = ""

    def requires(self):
        for index in self.indices:
            if self._satellite == "S1":
                yield ValidateIndicesForS1(productId=self.productId, indices=[index], parallel=index.value)
            elif self._satellite == "S2":
                yield ValidateIndicesForS2(productId=self.productId, indices=[index], parallel=index.value)

    def run(self):

        output = {
            "productId": self.productId,
            # "qcConsistencyErrors"
        }

        for i in self.input():
            with i.open("r") as ValidateIndices:
                data = json.load(ValidateIndices)

                if "qcConsistencyErrors" in output:
                    output["qcConsistencyErrors"] = bool(data["qcErrors"]) or output["qcConsistencyErrors"]
                else:
                    output["qcConsistencyErrors"] = bool(data["qcErrors"])

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


class FinaliseS1Workflow(FinaliseWorkflow):
    indices = EnumListParameter(
        enum=defaults.S1Indices,
        description="A comma separated list of any of RVI,VVVH,VHVV,RFDI",
        default=defaults.S1IndexDefaults["defaultIndices"])

    _satellite = "S1"
    _stateFileName = "FinaliseS1Workflow.json"


class FinaliseS2Workflow(FinaliseWorkflow):
    indices = EnumListParameter(
        enum=defaults.S2Indices,
        description="A comma separted list of any of Brightness,EVI,GLI,GNDVI,GRVI,NBR,NDMI,NDVI,NDWI,RB,RDVI,RG,SAVI,SBL",
        default=defaults.S2IndexDefaults["defaultIndices"])

    _satellite = "S2"
    _stateFileName = "FinaliseS2Workflow.json"
