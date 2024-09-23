import luigi
import logging
import json
import os
from string import Template

from luigi import LocalTarget
from luigi.util import requires

from orchestration.SetupWorkDirs import SetupWorkDirs
from orchestration.SubmitJob import SubmitJob

log = logging.getLogger('luigi-interface')


class SubmitJobs(luigi.Task):
    workingFolder = luigi.Parameter()
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()
    outputFolder = luigi.Parameter()
    containerPath = luigi.Parameter()
    indices = luigi.Parameter()
    templatesDir = luigi.Parameter()
    testProcessing = luigi.BoolParameter(default=False)

    templateFilename = ""
    platform = ""
    sbatchFileName = ""
    outfile = ""

    def run(self):
        products = []
        with self.input().open('r') as setupWorkDirs:
            products = json.load(setupWorkDirs)["products"]

        with open(os.path.join(self.templatesDir, self.templateFilename), "r") as t:
            sbatchTemplate = Template(t.read())

        tasks = []
        indices = self.indices.split(",")

        for product in products:
            commandArgs = {
                "jobWorkingDir": product["parentWorkDir"],
                "inputMount": self.basketFolder,
                "outputMount": self.outputFolder,
                "stateMount": product["stateDir"],
                "workingMount": product["workingDir"],
                "tmpMount": product["tmpDir"],
                "containerPath": self.containerPath,
                "productId": product["productName"],
                "indexCount": len(indices),
                "indices": f"--indices {self.indices}",
            }

            sbatchScript = sbatchTemplate.substitute(commandArgs)
            sbatchScriptPath = os.path.join(product["parentWorkDir"], self.sbatchFileName)

            with open(sbatchScriptPath, "w") as sbatchFile:
                sbatchFile.write(sbatchScript)

            task = SubmitJob(
                stateFolder=self.stateFolder,
                name=product["productName"],
                sbatchScriptPath=sbatchScriptPath,
                testProcessing=self.testProcessing,
            )

            tasks.append(task)

        yield tasks

        output = {
            "basket": self.basketFolder,
            "jobs": []
        }

        for task in tasks:
            submittedJob = {}
            with task.output().open('r') as taskOutput:
                submittedJob = json.load(taskOutput)

            output["jobs"].append(submittedJob)

        with self.output().open('w') as o:
            json.dump(output, o, indent=4)

    def output(self):
        outFile = os.path.join(self.stateFolder, self.outfile)
        return LocalTarget(outFile)


@requires(SetupWorkDirs)
class SubmitJobsForS1(SubmitJobs):
    templateFilename = "s1_index_generation_job_template.sbatch"
    platform = "S1"
    sbatchFileName = "s1_index_generation_job.sbatch"
    outfile = "SubmitJobsForS1.json"


@requires(SetupWorkDirs)
class SubmitJobsForS2(SubmitJobs):
    templateFilename = "s2_index_generation_job_template.sbatch"
    platform = "S2"
    sbatchFileName = "s2_index_generation_job.sbatch"
    outfile = "SubmitJobsForS2.json"
