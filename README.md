# PhenoGen REST API

We are building a REST API to provide access to all public data.  Eventually this will also
include running most functions available through the website.  Keep checking back for new functions.

## Domains for Functions Calls:

Functions can be called at either:

https://rest.phenogen.org

or

https://rest-test.phenogen.org
Please note this is a development and testing version of the API.  Please do not use this 
for actual data analysis.  Only for development.

## Help

https://rest-doc.phenogen.org - temporarily unavailable (as of 6/17/22), but will be available within a 
few days

All functions should include help as a response if you call the function with this appended to the 
end `?help=Y`.  The response returns a JSON object with supported methods and then list of parameters 
and description of each parameter as well as a list of options if there is a defined list of values.

## R methods for the API

We are developing methods to call the REST API from R and to retrieve the data directly from PhenoGen into
R.  For now this is limited to the datasets at https://phenogen.org/web/sysbio/resources.jsp -> New RNA 
Sequencing Datasets Experimental Details/Downloads

We will turn this into an R package and release it.

GitHub Repository - 
https://github.com/TabakoffLab/PhenoGenRESTR