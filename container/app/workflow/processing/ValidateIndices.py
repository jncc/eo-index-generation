import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import re
import pandas as pd

from luigi.util import requires
from luigi import LocalTarget

from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS1
from workflow.processing.CopyIndicesCogsToOutput import CopyIndicesCogsToOutputForS2
from workflow.processing.ValidateIndex import ValidateIndex

log = logging.getLogger('luigi-interface')


class ValidateIndices(luigi.Task):
    productId = luigi.Parameter()
    ardPath = luigi.Parameter()
    indexQcRange = luigi.ListParameter()
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])
    outputFolder = luigi.Parameter(default=defaults.Paths["output"])

    _stateFileName = ""
    _satellite = ""

    @staticmethod
    def process(results):
        df = pd.DataFrame.from_dict(results)
        df["Check"] = df.index.isin(df.sample(frac=0.05, random_state=1).index)  # 5% check

        err = []

        len(df["crs"].unique()) == 1 or err.append("issue with CRS consistency")
        len(df["dtype"].unique()) == 1 or err.append("issue with data type consistency")
        len(df["within_range"].unique()) == 1 or err.append("issue with index range consistency")
        len(df["valid_cog"].unique()) == 1 or err.append("issue with one or more COGS")
        len(df["nodata"].unique()) == 1 or err.append("Inconsistent no data values")
        len(df["extent_match"].unique()) == 1 or err.append("Inconsistent extent")
        len(df["aligned"].unique()) == 1 or err.append("Inconsistent pixel alignement")
        len(df["is_resolution_10"].unique()) == 1 or err.append("Inconsistent resolution")
        len(df["is_units_m"].unique()) == 1 or err.append("Inconsistent units")

        if err:
            log.error(f"Issues with QC: {err}")

        res = {}
        dfc = df.copy()

        object_cols = dfc.select_dtypes(include=['object']).columns  # Convert objects to string so (hopefully) no error with json dump
        excluded_cols = ["ard_transform", "transform"]  # ... Exclude known good columns

        object_cols = [col for col in object_cols if col not in excluded_cols]
        dfc[object_cols] = dfc[object_cols].astype(str)

        dfc.set_index(["tile", "index"], inplace=True)
        dfc = dfc.T

        for (product, index) in dfc.columns:
            if product not in res:
                res[product] = {index: dfc[product, index].to_dict()}
            else:
                res[product].update({index: dfc[product, index].to_dict()})

        return res, err

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
                    indexQcRange=self.indexQcRange,
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
            "qcErrors": processed_results[1] if processed_results[1] else False,
            "qcResults": processed_results[0]
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


@requires(CopyIndicesCogsToOutputForS1)
class ValidateIndicesForS1(ValidateIndices):

    _satellite = "S1"
    indexQcRange = luigi.ListParameter(default=defaults.S1IndexDefaults["qcRange"])
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_1")

    _stateFileName = "ValidateIndicesForS1.json"


@requires(CopyIndicesCogsToOutputForS2)
class ValidateIndicesForS2(ValidateIndices):

    _satellite = "S2"
    indexQcRange = luigi.ListParameter(default=defaults.S2IndexDefaults["qcRange"])
    ardPath = luigi.Parameter(default=f"{defaults.ArdBasePath}/sentinel_2")

    _stateFileName = "ValidateIndicesForS2.json"
