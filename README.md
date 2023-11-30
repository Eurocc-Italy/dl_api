# DTaaS API Brief intro

## Find a more detailed description and the code in the datalake_api

- datalake_api (Main Folder): This is the primary directory for the API server. It contains all the necessary code and resources to run the datalake service.

## Why COCO

COCO_dataset containes image file used in support of the development of the API. 

## Configuration
- .env File: This file is crucial for setting up the environment. It defines essential environment variables, including paths and MongoDB specifications necessary for the API server's operation.

### Variables Employed in default_controller.py
- `MONGO_HOST`: The host where the MongoDB server is located. In this configuration, it's set to `localhost`, indicating that the MongoDB server is running on the same machine as the API server.
- `MONGO_PORT`: The port used to connect to the MongoDB server. The default MongoDB port is `27017`.
- `MONGO_DB_NAME`: The name of the MongoDB database that the API interacts with. In this context, it's named `datalake`.
- `MONGO_COLLECTION_NAME`: The name of the MongoDB collection within the specified database. Here, it's referred to as `metadata`.
- `LOCAL_FOLDER`: The local file path to the folder containing data that the API operates on. It points to `/home/centos/dtaas_test_api/COCO_dataset` in this setup.

### Variables Employed in test_default_controller.py
- `TEST_MONGO_HOST`: Similar to `MONGO_HOST` but specifically configured for testing purposes.
- `TEST_MONGO_PORT`: Similar to `MONGO_PORT` but specifically configured for testing purposes.
- `TEST_MONGO_DB_NAME`: Similar to `MONGO_DB_NAME` but specifically configured for testing purposes.
- `TEST_MONGO_COLLECTION_NAME`: Similar to `MONGO_COLLECTION_NAME` but specifically configured for testing purposes.
- `TEST_LOCAL_FOLDER`: Similar to `LOCAL_FOLDER` but specifically configured for testing purposes.
- `TEST_IMAGE_1` and `TEST_IMAGE_2`: These variables represent the names of test image files used in the testing process.
- `TEST_METADATA_CONTENT`: A JSON array containing metadata information for testing. It includes an example entry with an `id` and a `path` pointing to a test image file.
- `TEST_QUERY_FILE_CONTENT`: A sample SQL query used for testing purposes. It retrieves data from a hypothetical table named `your_table`.
- `TEST_PYTHON_FILE_CONTENT`: A sample Python script used for testing purposes. It simply prints 'Hello, world!'
- `TEST_CONFIG_JSON_CONTENT`: A JSON object containing configuration settings. It includes both `config_server` and `config_client` sections with various configuration options for the server and client components.

