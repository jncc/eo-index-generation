# requirements - necessary

* Workflow takes in start data and end date
* Get ARD product from CEDA archive - modify existing finder script
* Produce indicies for s1 and s2 frames based on preconfigured selection - config file
* Produce metadata file for each output
* Validate output using a task based on the exisiting hab change detection validation script
* Move outputs to ceda ingestion area

# requirements - optional

* Implement scheduling on jasmin (rose/cylc)
* Email run report
  * Produce report in public folder
  * Run AWS process to forward report from public folder using SES

# Notes

* Automation system assumes responsible for managing the window of dates for wich the workflow is and has been run.
* There are no checks to see if an index has been previously generated for a frame.