# requirements - necessary

* Workflow takes in start data and end date
* Get ARD product from CEDA archive - modify existing finder script
* Produce indicies for s1 and s2 frames based on preconfigured selection - config file
* Produce metadata file for each output
* Validate output using a task based on the exisiting hab change detection validation script 
  * indexes-qc.py needs refactoring to have a parser & rule style
  * Rules should be distinct and testable.
* Move outputs to ceda ingestion area

# requirements - optional

* Implement scheduling on jasmin (rose/cylc)
* Email run report
  * Produce report in public folder
  * Run AWS process to forward report from public folder using SES

# Notes

* Automation system assumes responsible for managing the window of dates for wich the workflow is and has been run.
* There are no checks to see if an index has been previously generated for a frame.

# Orchestration

## import cdse search modules

<!-- Import module using the following mech:

```

import .util
import sys

spec = importlib.util.spec_from_file_location("module.name", "/path/to/file.py")
foo = importlib.util.module_from_spec(spec)
sys.modules["module.name"] = foo
spec.loader.exec_module(foo)

foo.MyClass() -->

```
* Call CreateSymlinks task?
* Use product name to determine s1 or s2 index creation task
* Create container job for each symlinked product to create indicies, target task determined by convention of ard prod name

# Index creation

* Copy product to working folder (PrepareProcessing)
* Run index job, s1 or s2 determined by orchestration
* validate output.


