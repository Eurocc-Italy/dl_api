# DTaaS API - Part of Digital Twin as a Service (DTaaS)

## Overview
The DTaaS API is RESTful API following OpenAPI specification coded with Flask (python). 

The DTaaS API is designed to enable to connect with the cloud-based infrastructure and facilitate user interactions via HTTP requests. For such goal the API sets up communication between multiple components (such as the MongoDB, the S3 Storage*, and the DTaaS Text User Interface) and data management.

More in detail, the DTaaS service can be describe as:

  - a Cloud-based infrastructure with a VM running a MongoDB database instance. This database contains the metadata for all the files in the data lake / digital twin, including the path to the actual corresponding file in the HPC parallel filesystem.
  - a HPC cluster which contains the actual files, stored in dual parallel filesystem/S3 mode (datalake). The HPC part runs the processing script sent by the user on the files matching the query.
  - The Text User Interface, used to query the datalake and run processing scripts on the files matching the query.

The API enables user operations (Upload, Download, Update, Delete...) acting as a conduit between the correct handling of requests on the MongoDB and S3 Storage*, and calling the appropriate methods from the DTaaS TUI to interact with the HPC cluster. 

By default the API functions by running the Werkzeug Flask server. **Consider switching to a more robust server if the system has to be put on a production environment** 


## Requirements
- Python 3.5.2 or higher. (The service has been tested with python 3.9.g)
- xxx

## Installation

We highly recommend installing the software in a custom Python virtual environment. You can set up a virtual environment with third-party tools such as [Anaconda](https://docs.anaconda.com/free/anaconda/install/index.html) or with the built-in [venv](https://docs.python.org/3/library/venv.html) module.

After having set up and activated your virtual environment, download this repo and install the necessary dependencies listed in requirement.txt and test_requirements.txt

  ```bash
pip install -r requirements.txt
pip install -r test_requirements.txt
  ```

## Usage

### Running the server 
To initiate the DataLake API server, execute the following command from the root directory: 
  ```bash
python -m swagger_server
  ```
### Running Tests
 
Conduct tests to ensure the API's reliability and correctness from the root directory:
  ```bash
python -m swagger_server.test.test_default_controller
  ```

### Accessing UI Docs
OpenAPI provides the swagger ui default documentation, which is accessible from: 
```bash
http://localhost:8080/v1/ui/
  ```

## Brief Folder Structure Explanation
Besides auxiliary files provided by the connexion library, the code base is essentially contained within the swagger_server folder. Within this: 

- swagger: Holds the YAML file defining the API's specifications.
- controller: Contains the default_controller.py which handles api requests behavior
- test: Contains test_default_controller.py, ensuring reliability and correctness of the requests.
- models: Validates request parameters as dictated by the schemas provided within the swagger.yaml file

## API calls examples via curl
The OpenAPI documentation can be used in order to obtain the below commands.  

**download** a document at path/to/file
```bash
curl -X 'GET' \
  'http://localhost:8080/v1/download?id=path%2Fto%2Ffile' \
  -H 'accept: application/octet-stream'
  ```

**query_and_process** call with query_file = queryTry.txt (*required), python_file = pyTry.py and config_json= configTry.json
```bash
curl -X 'POST' \
  'http://localhost:8080/v1/query_and_process' \
  -H 'accept: text/plain' \
  -H 'Content-Type: multipart/form-data' \
  -F 'config_json=@configTry.json;type=application/json' \
  -F 'python_file=@pyTry.py;type=text/x-python' \
  -F 'query_file=@queryTry.txt;type=text/plain'
  ```

**upload** airplane_0582.jpg file with associated metadata single_entry_metadata_test.json
```bash
curl -X 'POST' \
  'http://localhost:8080/v1/upload' \
  -H 'accept: text/plain' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@airplane_0582.jpg;type=image/jpeg' \
  -F 'json_data=@single_entry_metadata_test.json;type=application/json'
  ```

**delete** path/to/file file and its associated metadata
```bash
curl -X 'DELETE' \
  'http://localhost:8080/v1/delete?file_path=path%2Fto%2Ffile' \
  -H 'accept: */*'
  ```

**update** the metadata associate with path/to/file with the content of single_entry_metadata_test.json
```bash
curl -X 'PATCH' \
  'http://localhost:8080/v1/update?path=path%2Fto%2Ffile' \
  -H 'accept: */*' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@single_entry_metadata_test.json;type=application/json'
```

**replace** the file at path/to/file and the corresponding metadata with airplane_0582.jpg file and the content of single_entry_metadata_test.json as metada
```bash
curl -X 'PUT' \
  'http://localhost:8080/v1/replace?path=path%2Fto%2Ffile' \
  -H 'accept: */*' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@airplane_0582.jpg;type=image/jpeg' \
  -F 'json_data=@single_entry_metadata_test.json;type=application/json'
```


## Additional Resources:
This server, generated by the [swagger-codegen](https://github.com/swagger-api/swagger-codegen) project, leverages the [OpenAPI-Spec](https://github.com/swagger-api/swagger-core/wiki) to create a Flask server stub. It utilizes the [Connexion](https://github.com/zalando/connexion) library for enhanced functionality. As such you can find more information on the general structure at: 

- https://swagger.io/docs/
- https://connexion.readthedocs.io/en/stable/


## Contributions: 
We welcome contributions for the Datalake API.

## Credits and Contact
The Service was developed by the collaboration of IFAB and CINECA within the framework of the EUROCC2 European project.

For more information you can contact

- ivan&benedetta&tony&luca&eric@ifabcineca.com

## Licence
ifabcinecaeurocclicence




