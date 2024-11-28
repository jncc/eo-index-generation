import luigi
import os
import json
import workflow.common.Defaults as defaults
import logging
import subprocess

from luigi.util import requires
from luigi import LocalTarget
from pebble import ProcessPool, ProcessExpired
from functional import seq
from workflow.processing.ApplyIndicesCorrections import ApplyS1IndicesCorrections, ApplyS2IndicesCorrections

log = logging.getLogger('luigi-interface')
"""
Takes the index files and converts it into a cloud optimised GeoTIFF using 
"""


class GenerateIndicesCogs(luigi.Task):
    workingFolder = luigi.Parameter(default=defaults.Paths["working"])
    stateFolder = luigi.Parameter(default=defaults.Paths["state"])

    _stateFileName = ""

    def generateCogFile(self, jobData):
        indexFilePath = jobData["indexFilePath"]

        bits = os.path.splitext(indexFilePath)
        tempIndexFile1 = f"{bits[0]}_TEMP{bits[1]}"

        cogFilePath = jobData["cogFilePath"]

        cmd = f"gdalwarp -dstnodata -9999 {indexFilePath} {tempIndexFile1}"

        self.executeSubProcess(cmd)

        cmd = f"gdaladdo -r nearest {tempIndexFile1} 2 4 8 16 32 64 128 256 512"

        self.executeSubProcess(cmd)

        cmd = f"gdal_translate -of \"COG\" -co \"COMPRESS=DEFLATE\" -co \"BIGTIFF=YES\" -co \"COPY_SRC_OVERVIEWS=YES\" {tempIndexFile1} {cogFilePath}"
        self.executeSubProcess(cmd)

        os.remove(tempIndexFile1)

        return {
            "indexName": jobData["indexName"],
            "cogFilePath": cogFilePath
        }

    def executeSubProcess(self, cmd):
        try:
            log.info("Running cmd: " + cmd)

            subprocess.run(cmd, check=True, stderr=subprocess.STDOUT, shell=True)

        except subprocess.CalledProcessError as e:
            errStr = "command '{}' returned with error (code {}): {}".format(e.cmd, e.returncode, e.output)
            log.error(errStr)
            raise RuntimeError(errStr)

    def run(self):

        with self.input().open('r') as aic:
            indicesFiles = (json.load(aic))["indicesFiles"]

        cogDir = os.path.join(self.workingFolder, "indices-cogs")

        os.makedirs(cogDir, exist_ok=True)

        jobList = seq(indicesFiles) \
            .map(lambda x: {
                "indexName": x["indexName"],
                "indexFilePath": x["indexFile"],
                "cogFilePath": os.path.join(cogDir, os.path.basename(x["indexFile"]))
            }).to_list()

        cogFiles = []

        with ProcessPool(max_workers=len(jobList)) as pool:

            generateCogJobs = pool.map(self.generateCogFile, jobList)

            try:
                for cogFileResult in generateCogJobs.result():
                    cogFiles.append(cogFileResult)
            except ProcessExpired as error:
                log.error("%s. Exit code: %d", error, error.exitcode)

        for cog in cogFiles:
            if not os.path.isfile(cog["cogFilePath"]):
                raise Exception(f"Cant find generated cog {cog['cogFilePath']}")

        output = {
            "indicesCogFiles": cogFiles
        }

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self._stateFileName)
        return LocalTarget(outFile)


@requires(ApplyS1IndicesCorrections)
class GenerateIndicesCogsForS1(GenerateIndicesCogs):

    _stateFileName = "GenerateIndicesCogsForS1.json"

    def nullFunction(self):
        pass


@requires(ApplyS2IndicesCorrections)
class GenerateIndicesCogsForS2(GenerateIndicesCogs):

    _stateFileName = "GenerateIndicesCogsForS2.json"

    def nullFunction(self):
        pass
