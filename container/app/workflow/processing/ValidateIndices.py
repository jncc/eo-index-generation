import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import re
from functional import seq

from luigi.util import requires
from luigi import LocalTarget

from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS1
from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS2
from workflow.processing.ValidateIndex import ValidateIndex

from workflow.common.Defaults import QcChecks

log = logging.getLogger('luigi-interface')


class ValidateIndices(luigi.Task):
    productId = luigi.Parameter()
    ardPath = luigi.Parameter()
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    outputFolder = luigi.Parameter(default=defaults.Paths["output"])

    _stateFileName = ""
    _satellite = ""

    @staticmethod
    def process(results):

        def check_qc(value, expected=True):
            if value == expected:
                return True
            else:
                return value

        failedIndices = seq(results) \
            .map(lambda x: {"index": x["index"], "qc": {
                "crs": check_qc(x.get("crs"), QcChecks.get_defaults()["crs"]),
                "dtype": check_qc(x.get("dtype"), QcChecks.get_defaults()["dtype"]),
                "nodata": check_qc(x.get("nodata"), QcChecks.get_defaults()["nodata"]),
                "valid_cog": check_qc(x.get("valid_cog")),
                "within_range": check_qc(x.get("within_range")),
                "extent_match": check_qc(x.get("extent_match")),
                "aligned": check_qc(x.get("aligned")),
                "is_resolution_10": check_qc(x.get("is_resolution_10")),
                "is_units_m": check_qc(x.get("is_units_m")),
            }}) \
            .map(lambda x: {"index": x["index"], "qc": {k: v for k, v in x["qc"].items() if v is not True}}) \
            .filter(lambda x: x["qc"] != {}) \
            .to_list()

        errors = []
        for failedIndex in failedIndices:
            for k, v in failedIndex["qc"].items():
                errors.append(f"{failedIndex['index']} {k} = {v} (Expected: {QcChecks.get_defaults().get(k, True)})")

        if errors:
            raise ValueError("QC Check(s) Failed\n" + "\n".join(errors))

        return True

    def run(self):
        with self.input().open('r') as CopyIndicesCogsToOutput:
            cogFiles = (json.load(CopyIndicesCogsToOutput))["indicesCogFiles"]

        datestamp = re.findall("([0-9]{8})", self.productId)[0]

        if self._satellite == "S1":
            ardFile = f"{self.ardPath}/{datestamp[0:4]}/{datestamp[4:6]}/{datestamp[6:8]}/{self.productId}.tif"
        elif self._satellite == "S2":
            ardFile = f"{self.ardPath}/{datestamp[0:4]}/{datestamp[4:6]}/{datestamp[6:8]}/{self.productId}_sat.tif"

        indexValidationTasks = []
        for i in cogFiles:
            indexValidationTasks.append(
                ValidateIndex(
                    productId=self.productId,
                    stateFolder=self.stateFolder,
                    index=i["indexName"],
                    indexFileName=os.path.basename(i["cogFilePath"]),
                    indexFilePath=i["cogFilePath"],
                    indexQcRange=QcChecks.get_range(i["indexName"]),
                    ardFile=ardFile,
                    _stateFileName=f"ValidateIndexFor{self._satellite}_{i['indexName']}.json"
                )
            )

        yield indexValidationTasks

        validationProducts = []
        for task in indexValidationTasks:
            with task.output().open('r') as o:
                validationProducts.append(json.load(o)["qcResults"])

        processed_results = self.process(validationProducts)

        output = {
            "productId": self.productId,
            "qcPassed": True if processed_results else False,
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


@requires(CopyIndicesCogsToOutputForS1)
class ValidateIndicesForS1(ValidateIndices):

    _satellite = "S1"
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_1")

    _stateFileName = "ValidateIndicesForS1.json"


@requires(CopyIndicesCogsToOutputForS2)
class ValidateIndicesForS2(ValidateIndices):

    _satellite = "S2"
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_2")

    _stateFileName = "ValidateIndicesForS2.json"
