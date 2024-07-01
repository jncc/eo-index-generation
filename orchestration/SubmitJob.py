import luigi
import logging
import subprocess
import json
import os
from string import Template
import random
import re
import datetime

from luigi import LocalTarget
from luigi.util import requires

from orchestration.SetupWorkDirs import SetupWorkDirs

log = logging.getLogger('luigi-interface')


class SubmitJob(luigi.Task):
    stateFolder = luigi.Parameter()
    name = luigi.Parameter()
    sbatchScriptPath = luigi.Parameter()
    testProcessing = luigi.BoolParameter(default=False)
    jobId = ""

    def run(self):
        try:
            outputFile = {
                "name": self.name,
                "sbatchScriptPath": self.sbatchScriptPath,
                "jobId": None,
                "submitTime": None
            }

            outputString = ""
            if self.testProcessing:
                randomJobId = random.randint(1000000, 9999999)
                outputString = "JOBID     USER    STAT  QUEUE      FROM_HOST   EXEC_HOST   JOB_NAME   SUBMIT_TIME"\
                    + str(randomJobId)+"   test001  RUN   short-serial jasmin-sci1 16*host290. my-job1 Nov 16 16:51"
            else:
                sbatchCmd = "sbatch {}".format(self.sbatchScriptPath)
                log.info("Submitting job using command: %s", sbatchCmd)
                output = subprocess.check_output(
                    sbatchCmd,
                    stderr=subprocess.STDOUT,
                    shell=True)
                outputString = output.decode("utf-8")

            regex = '[0-9]{5,}'  # job ID is at least 5 digits
            match = re.search(regex, outputString)
            self.jobId = match.group(0)

            log.info("Successfully submitted lotus job <%s> for %s using sbatch script: %s", self.jobId, self.name, self.sbatchScriptPath)

            outputFile["jobId"] = self.jobId
            outputFile["submitTime"] = str(datetime.datetime.now())

            with self.output().open('w') as out:
                json.dump(outputFile, out, indent=4)

        except subprocess.CalledProcessError as e:
            errStr = "command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output)
            log.error(errStr)
            raise RuntimeError(errStr)

    def output(self):
        outFile = os.path.join(self.stateFolder, f'SubmitJob_{self.name}_{self.jobId}.json')
        return LocalTarget(outFile)


class SubmitJobs(luigi.Task):
    workingFolder = luigi.Parameter()
    stateFolder = luigi.Parameter()
    basketFolder = luigi.Parameter()
    outputFolder = luigi.Parameter()
    containerPath = luigi.Parameter()
    indicesList = luigi.Parameter(default="")
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
                "indices": ""
            }

            if self.indicesList != "":
                commandArgs["indicesList"] = f"--indices {self.indicesList}"

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
