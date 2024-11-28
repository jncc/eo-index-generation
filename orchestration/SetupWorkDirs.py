import luigi
import os
import json
import logging

from luigi import LocalTarget

from orchestration.GetArdProducts import GetArdProductsFromFilters, GetArdProductsFromTextFileList

log = logging.getLogger('luigi-interface')


class SetupWorkDirs(luigi.Task):
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()
    workingFolder = luigi.Parameter()

    # Ceda Ard Finder Params. Set them to None if not used
    startDate = luigi.OptionalParameter(default=None)
    endDate = luigi.OptionalParameter(default=None)
    ardFilter = luigi.OptionalParameter(default=None)
    spatialOperator = luigi.OptionalParameter(default=None)
    satelliteFilter = luigi.OptionalParameter(default=None)

    orbit = luigi.IntParameter(default=-9999)
    orbitDirection = luigi.Parameter(default="")
    wkt = luigi.Parameter(default="")

    def requires(self):
        # Dynamically choose the workflow based on the presence of inputs.txt in the root of the basket folder
        if os.path.exists(os.path.join(self.basketFolder, "inputs.txt")):
            return self.clone(GetArdProductsFromTextFileList)
        else:
            # First check that the parameters are set correctly
            for k in ["startDate", "endDate", "ardFilter", "spatialOperator", "satelliteFilter"]:
                if self.param_kwargs.get(k) is None:
                    raise ValueError(f"Parameter {k} is not set")
            return self.clone(GetArdProductsFromFilters)

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
