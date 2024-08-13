
import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import re
import shutil

from luigi.util import requires
from luigi import LocalTarget
from workflow.processing.GenerateIndicesCogs import GenerateIndicesCogsForS1
from workflow.processing.GenerateIndicesCogs import GenerateIndicesCogsForS2

log = logging.getLogger('luigi-interface')
"""
Copies the indices COGs to the output folder
"""


class CopyIndicesCogsToOutput(luigi.Task):
    productId = luigi.Parameter()
    outputFolder = luigi.Parameter(default=defaults.Paths["output"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])

    _stateFileName = ""

    def getOutputFilePath(self, cogFilePath, indexName):
        satellite = self.productId[1:2]
        datestamp = re.findall("([0-9]{8})", self.productId)[0]
        filename = os.path.basename(cogFilePath)

        outPath = os.path.join(self.outputFolder, f"sentinel_{satellite}", indexName.lower(), datestamp[0:4], datestamp[4:6], datestamp[6:8], filename)

        return outPath

    def run(self):

        with self.input().open('r') as generateIndicesCogs:
            cogFiles = (json.load(generateIndicesCogs))["indicesCogFiles"]

        indicesCogFiles = []
        for cog in cogFiles:
            source = cog["cogFilePath"]
            indexName = cog["indexName"]
            destination = self.getOutputFilePath(source, indexName)
            destinationDir = os.path.dirname(destination)

            os.makedirs(destinationDir, exist_ok=True)

            shutil.copyfile(source, destination)

            indicesCogFiles.append({
                "indexName": indexName,
                "cogFilePath": destination
            })

        output = {
            "indicesCogFiles": indicesCogFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


@requires(GenerateIndicesCogsForS1)
class CopyIndicesCogsToOutputForS1(CopyIndicesCogsToOutput):

    _stateFileName = "CopyIndicesCogsToOutputForS1.json"

    def nullFunction(self):
        pass


@requires(GenerateIndicesCogsForS2)
class CopyIndicesCogsToOutputForS2(CopyIndicesCogsToOutput):

    _stateFileName = "CopyIndicesCogsToOutputForS2.json"

    def nullFunction(self):
        pass
