import luigi
import os
import json
import logging

from luigi import LocalTarget
from luigi.util import requires

from orchestration.GetArdProducts import GetArdProducts

log = logging.getLogger('luigi-interface')


@requires(GetArdProducts)
class SetupWorkDirs(luigi.Task):
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()
    workingFolder = luigi.Parameter()

    def run(self):
        products = []
        with self.input().open('r') as getProducts:
            products = json.load(getProducts)["products"]

        output = {
            "products": []
        }

        for productName in products:
            workspaceName = f'{os.path.basename(self.basketFolder)}_{productName}'
            workspacePath = os.path.join(self.workingFolder, workspaceName)

            if not os.path.exists(workspacePath):
                os.makedirs(workspacePath)

            workspaceWorkingDir = os.path.join(workspacePath, "working")
            if not os.path.exists(workspaceWorkingDir):
                os.makedirs(workspaceWorkingDir)

            workspaceStateDir = os.path.join(workspacePath, "state")
            if not os.path.exists(workspaceStateDir):
                os.makedirs(workspaceStateDir)

            workspaceTmpDir = os.path.join(workspaceWorkingDir, "tmp")
            if not os.path.exists(workspaceTmpDir):
                os.makedirs(workspaceTmpDir)

            output["products"].append({
                "productName": productName,
                "parentWorkDir": workspacePath,
                "workingDir": workspaceWorkingDir,
                "stateDir": workspaceStateDir,
                "tmpDir": workspaceTmpDir
            })

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, "SetupWorkDirs.json")
        return LocalTarget(outFile)
