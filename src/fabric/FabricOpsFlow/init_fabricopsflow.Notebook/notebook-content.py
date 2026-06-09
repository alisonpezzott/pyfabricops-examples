# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "399ff0f0-fa34-4e5a-a481-c4424dfc3c9c",
# META       "default_lakehouse_name": "LakeUnique",
# META       "default_lakehouse_workspace_id": "a6f837e7-7cd8-4ea7-bc5b-2898f3c85704",
# META       "known_lakehouses": [
# META         {
# META           "id": "399ff0f0-fa34-4e5a-a481-c4424dfc3c9c"
# META         }
# META       ]
# META     },
# META     "warehouse": {
# META       "default_warehouse": "21e6be66-089b-44d9-8a4a-1b7ce071c527",
# META       "known_warehouses": [
# META         {
# META           "id": "21e6be66-089b-44d9-8a4a-1b7ce071c527",
# META           "type": "Lakewarehouse"
# META         }
# META       ]
# META     }
# META   }
# META }

# MARKDOWN ********************

# # FabricOpsFlow Initialization Script  
# This script initializes the FabricOpsFlow environment for a project by creating workspaces, connections, pipelines and connecting to a repository in Azure DevOps. It also adds specified users as admins to the workspaces and connections.
# Make sure to review and update the parameters below before running the script.  
# 
# # Pre-requisites:
# 
# ## Azure Portal / Microsoft Entra setup:
# - Create an app registration in Azure / Microsoft Entra.
# - Note down the application (client) ID, directory (tenant) ID and create a client secret for the app registration. Note down the client secret value as well, as it won"t be shown again.
# - Give and grant it the following permissions to create items and connections in Microsoft Fabric and to connect to Azure DevOps Pipelines:
#   - Azure DevOps: svo.pipelineresources_manege  
#   - Azure Key Vault: user_impersonation  
#   - Power BI: 
#     - Connection.ReadWrite.All  
#     - Connection.Reshare.All
#     - Content.Create  
#     - Gateway.ReadWrite.All  
#     - Item.Execute.All
#     - Item.ReadWrite.All
#     - Item.Reshare.All
#     - Tenant.ReadWrite.All
#     - Workspace.GitCommit.All
#     - Workspace.GitUpdate.All
#     - Workspace.ReadWrite.All  
# 
# - Add the service principal to a security group and note down the name of this group.
# 
# ## Azure Portal / Key Vault setup:
# - Create an Azure Key Vault, configure the following secrets, and assign the `Key Vault Secrets User` role to the service principal and all users participating in the project: 
#   - fab-tenant-id
#   - fab-client-id
#   - fab-client-secret
#   
# ## Azure DevOps setup:  
# - Create an Azure DevOps organization and project and a repository.  
# - Note down the organization name, project name and repository name and set the parameters below accordingly. The script will create a repository in the specified project, but it needs to exist beforehand. You can use the same project for multiple environments, as the script will create different branches and suffixes for workspaces and pipelines.  
# - Add the service principal and all users participating in the project to the Azure DevOps project with at least contributor access.  
# - Initialize a repository in Azure DevOps with a main branch.
# - Create a new dummy file into a new folder. E.g. `/src/README.md`. This is required for the script to be able to create branches and connect workspaces to them.
# -  Checkout a new branch from main named `develop`. This is required for the script to be able to create the DEV environment.  
# -  In Pipelines/Library create a new variable group called `FAB_CREDENTIALS` and link it to the Azure Key Vault created in the previous steps, syncing all secrets. This is required for the pipeline to be able to retrieve the secrets from the Key Vault. Set the name of the variable group in the parameters below:  
#   - FAB-CLIENT-ID
#   - FAB-CLIENT-SECRET
#   - FAB-TENANT-ID     
# 
# ## Microsoft Fabric setup:
# - Add the group in the Microsoft Fabric admin portal to the options to run Rest API scripts and to create items and connections. Enable to a subset of organization and set the group name in the following options: 
#   - Service principals can create workspaces, connections, and deployment pipelines
#   - Service principals can call Fabric public APIs
#   - Service principals can access read-only admin APIs
#   - Service principals can access admin APIs used for updates
#   - Enhance admin APIs responses with detailed metadata
#   - Enhance admin APIs responses with DAX and mashup expressions
# - If you are running the script in a Microsoft Fabric notebook, make sure to set a temporary default lakehouse because staging defintion items when creating or updating them. 


# CELL ********************

# Install if you haven"t already.
%pip install -U -qq pyfabricops 

# Parameters 
project_name = "FabricOpsFlow" # Used for workspaces, pipelines and repository
capacity = "7732a1eb-3893-4642-a85c-93fc3f35d076"      # Or name (see pf.list_capacities()) 

# Azure DevOps required parameters
# Create an Azure DevOps organization and project, and set the parameters below accordingly. 
# The script will create a repository in the specified project, but it needs to exist beforehand.
# You can use the same project for multiple environments, as the script will create different branches and suffixes for workspaces and pipelines.
devops_organization_name = "alisonpezzott" 
devops_project_name = "FabricOpsFlow" 
devops_repository_name = "FabricOpsFlow" 
devops_url = f"https://dev.azure.com/{devops_organization_name}/{devops_project_name}/_git/{devops_repository_name}"

# Workspaces will be created with suffixes based on branches, e.g. main -> FabricOpsFlow-PRD, develop -> FabricOpsFlow-DEV
branches = [      
    {"branch": "develop", "suffix": "DEV"},
    {"branch": "main",    "suffix": "PRD"}, 
] 

# Admins to add to workspaces and connections, with format:
# Allowed User types: "User", "Group", "ServicePrincipal", "ServicePrincipalProfile"
# See pf.get_service_principal_id and pf.get_user_id to retrieve the user_uuid for service principals and users, respectively.
roles = [
    {
        "user_uuid": "9322eb4a-4132-4bd1-8df1-5cd3d1d2400b",   
        "user_type": "User"
    },
    {
        "user_uuid": "bde43861-55e1-4144-b572-be115312967f", 
        "user_type": "ServicePrincipal"
    }
]


# Authenticating method depends on where you are running the script.
# If you are running the script inside of Microsoft Fabric, make sure to fill the Key Vault. 
# Authenticate using "oauth" if in VS Code for authentication with interactive mode. 
# Authenticate using "env" for service principal authentication with environment variables FAB_TENANT_ID, FAB_CLIENT_ID, FAB_CLIENT_SECRET
# Locally, you can set these environment variables in your terminal or IDE. 
authentication_method = "fabric" # Options: "fabric", "env", "oauth"


# If you are running the script inside of Microsoft Fabric, make sure to fill the Key Vault.
key_vault = "https://pezzott-mvp.vault.azure.net/"



# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Authentication and Logging
import os
import pyfabricops as pf

if authentication_method == "fabric": 
    import notebookutils
    os.environ["FAB_TENANT_ID"] = notebookutils.credentials.getSecret(key_vault, "fab-tenant-id") 
    os.environ["FAB_CLIENT_ID"] = notebookutils.credentials.getSecret(key_vault, "fab-client-id") 
    os.environ["FAB_CLIENT_SECRET"] = notebookutils.credentials.getSecret(key_vault, "fab-client-secret") 
    pf.set_auth_provider("fabric") # Authenticate using "fabric" for authentication context of the current user
elif authentication_method == "oauth":
    pf.set_auth_provider("oauth") # Authenticate using "oauth" for authentication with interactive mode
elif authentication_method == "env":
    pf.set_auth_provider("env") # Authenticate using "env" for service principal authentication with environment variables FAB_TENANT_ID, FAB_CLIENT_ID, FAB_CLIENT_SECRET
else:
    raise ValueError('Invalid authentication method. Choose from "fabric", "oauth", or "env"')

# Setup logger
pf.setup_logging("info", "detailed") 
logger = pf.get_logger(__name__)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create Workspaces
workspaces = []
capacity_id = pf.resolve_capacity(capacity) 

for branch in branches:
    branch_suffix = branch["suffix"]
    
    workspace_name = f"{project_name}-{branch_suffix}"
    
    workspace_created = pf.create_workspace(
        display_name=workspace_name,
        capacity=capacity_id,
        df=False,
    )
    
    # If workspace creation fails (e.g. because it already exists), retrieve the existing workspace
    if workspace_created:
        workspaces.append(workspace_created)
        workspace_id = workspace_created["id"]
        logger.success(f"Workspace {workspace_name} created with ID {workspace_id}")
    else:
        workspace_retrivied = pf.get_workspace(workspace_name, df=False)
        workspaces.append(workspace_retrivied)
        workspace_id = workspace_retrivied["id"]
        logger.warning(f"Workspace {workspace_name} already exists with ID {workspace_id}")

    # Assign admins to workspace
    for role in roles:
        pf.add_workspace_role_assignment(
            workspace_name, 
            role["user_uuid"], 
            role["user_type"], 
            role="Admin",
            df=False
        )

display(pf.json_to_df(workspaces)) 


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Check capacity assign to workspace
import time    
    
MAX_RETRIES = 10
RETRY_INTERVAL = 10
logger.info(f"Checking capacity assign progress...")

for attempt in range(1, MAX_RETRIES + 1):
    logger.info(f"Attempt {attempt}/{MAX_RETRIES}")
    workspace = pf.get_workspace(f"{project_name}-PRD", df=False)
    
    if workspace["capacityAssignmentProgress"] == "Completed":
        logger.success(f"Capacity assigned successfully.")
        break

    else: 
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_INTERVAL)
        else:
            logger.error(f"Capacity assignment failed after {MAX_RETRIES} attempts.")
            raise TimeoutError(f"Capacity assignment did not complete within {MAX_RETRIES * RETRY_INTERVAL} seconds.") 
              

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create Lakehouses, Pools and Environments in each Workspace
for workspace in workspaces:

    # Create folders in workspace
    folders = ["data", "utils", "notebooks", "pipelines", "reporting"] 
    for folder in folders:
        pf.create_folder(
            workspace=workspace["id"],
            display_name=folder,
            df=False,
        )

    # Create Lakehouses in workspace
    layers = ["bronze", "silver", "gold"]
    for layer in layers:
        pf.create_lakehouse(
            workspace=workspace["id"],
            display_name=f"lh_{layer}",
            folder="data",
            enable_schemas=True,
            df=False,
        )

    # Create Spark pool in workspace
    # Adjust node_family, node_size, and max_node_count based on your needs and budget. 
    # See documentation for details: https://learn.microsoft.com/en-us/fabric/data-engineering/spark-compute
    pool_created = pf.create_workspace_custom_pool(
        workspace=workspace["id"],
        display_name="default_pool",
        auto_scale_enabled=True,
        min_node_count=1,
        max_node_count=16,
        dynamic_executor_allocation_enabled=True,
        min_executors=1,
        max_executors=15,
        node_family="MemoryOptimized",
        node_size="Medium", # Options: Small, Medium, Large
        df=False,
    )

    # If pool creation fails (e.g. because it already exists), retrieve the existing pool
    if pool_created is None:
        pool_created = pf.get_workspace_custom_pool(
            workspace=workspace["id"],
            workspace_custom_pool="default_pool",
            df=False,
        )

    # Create Spark environment in workspace and link to pool
    environment_created = pf.create_environment(
        workspace=workspace["id"],
        display_name="env_default",
        folder = "utils",
        df=False,
    )

    # If environment creation fails (e.g. because it already exists), retrieve the existing environment
    if environment_created is None:
        environment_created = pf.get_environment(
            workspace=workspace["id"],
            environment="env_default",
            df=False,
        )

    # Update environment with Spark compute settings and link to pool
    pf.update_environment_spark_compute(
        workspace=workspace["id"],
        environment="env_default",
        pool="default_pool",
        driver_cores=8,
        driver_memory="56g",
        executor_cores=8,
        executor_memory="56g",
        dynamic_executor_allocation_enabled=True,
        min_executors=1,
        max_executors=15,
        spark_properties=[
            {"key": "spark.sql.caseSensitive", "value": True},
            {"key": "spark.native.enabled", "value": True},
        ],
        runtime_version="1.3"
    )

    # Prepare environment by installing external libraries and publish environment for use in workspace.
    pf.delete_path("../tmp") 

    # Install pyFabricOps library in environment from PyPI. This is required to use FabricOpsFlow SDK 
    # in notebooks and pipelines in the workspace. You can add any other libraries your team needs here as well.
    MAX_RETRIES = 10
    RETRY_INTERVAL = 10
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            pf.add_environment_external_library_from_pypi(
                workspace=workspace["id"],
                environment=environment_created["id"],
                libraries=[
                    ("pyFabricOps", "0.3.15"),
                    ("semantic-link-labs", "0.13.2"),
                ]
            )
            break
        except Exception as e:
            logger.error(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt == MAX_RETRIES:
                raise e
            time.sleep(RETRY_INTERVAL)

    # Publish environment for use in workspace.
    pf.publish_environment(
        workspace=workspace["id"],
        environment=environment_created["id"],
        df=False
    )

    # Update workspace Spark settings and link to pool and environment. 
    # This will ensure that users can select the environment and pool when creating notebooks and pipelines, 
    # and that Spark settings are applied by default.
    pf.update_workspace_spark_settings(
        workspace=workspace["id"],
        automatic_log_enabled=True,
        high_concurrency_notebook_interactive_run_enabled=True,
        high_concurrency_notebook_pipeline_run_enabled=True,
        pool_customize_compute_enabled=True,
        pool_default_name="default_pool",
        pool_default_id=pool_created["id"],
        pool_default_type="Workspace",
        starter_pool_max_node_count= 1,
        starter_pool_max_executors=10,
        environment_name="env_default",
        environment_runtime_version="1.3",
        job_conservative_job_admission_enabled=True,
        job_session_timeout_in_minutes=20,
        df=False
    )

    logger.success(f'Pools, environments and external libraries were created successfully in Workspace: {workspace["displayName"]}')


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create Variable Library Definition Files for workspaces
pf.delete_path("../tmp")

for b in branches:
    suffix = b["suffix"]
    branch = b["branch"]

    workspace = pf.get_workspace(f"{project_name}-{suffix}", df=False)
    
    pool = pf.get_workspace_custom_pool(
        workspace=workspace["id"],
        workspace_custom_pool="default_pool",
        df=False,
    )

    lake_bronze = pf.get_lakehouse(workspace=workspace["id"], lakehouse=f"lh_bronze", df=False)
    lake_bronze_id = lake_bronze["id"]
    lake_bronze_sql_endpoint_connection_string = lake_bronze["properties"]["sqlEndpointProperties"]["connectionString"]
    lake_bronze_sql_endpoint_id = lake_bronze["properties"]["sqlEndpointProperties"]["id"]

    lake_silver = pf.get_lakehouse(workspace=workspace["id"], lakehouse=f"lh_silver", df=False)
    lake_silver_id = lake_silver["id"]
    lake_silver_sql_endpoint_connection_string = lake_silver["properties"]["sqlEndpointProperties"]["connectionString"]
    lake_silver_sql_endpoint_id = lake_silver["properties"]["sqlEndpointProperties"]["id"]
    
    lake_gold = pf.get_lakehouse(workspace=workspace["id"], lakehouse=f"lh_gold", df=False)
    lake_gold_id = lake_gold["id"]
    lake_gold_sql_endpoint_connection_string = lake_gold["properties"]["sqlEndpointProperties"]["connectionString"]
    lake_gold_sql_endpoint_id = lake_gold["properties"]["sqlEndpointProperties"]["id"]

    value_set = {
      "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/valueSet/1.0.0/schema.json",
      "name": branch,
      "variableOverrides": [
        {
          "name": "workspace_name",
          "value": workspace["displayName"]
        },
        {
          "name": "workspace_id",
          "value": workspace["id"]
        },
        {
          "name": "pool_id",
          "value": pool["id"]
        },
        {
          "name": "lake_bronze_id",
          "value": lake_bronze_id
        },
        {
          "name": "lake_bronze_sql_endpoint_connection_string",
          "value": lake_bronze_sql_endpoint_connection_string
        },
        {
          "name": "lake_bronze_sql_endpoint_id",
          "value": lake_bronze_sql_endpoint_id
        },
        {
          "name": "lake_silver_id",
          "value": lake_silver_id
        },
        {
          "name": "lake_silver_sql_endpoint_connection_string",
          "value": lake_silver_sql_endpoint_connection_string
        },
        {
          "name": "lake_silver_sql_endpoint_id",
          "value": lake_silver_sql_endpoint_id
        },
        {
          "name": "lake_gold_id",
          "value": lake_gold_id
        },
        {
          "name": "lake_gold_sql_endpoint_connection_string",
          "value": lake_gold_sql_endpoint_connection_string
        },
        {
          "name": "lake_gold_sql_endpoint_id",
          "value": lake_gold_sql_endpoint_id
        }
      ]
    }

    pf.write_json(
        value_set,
        f"../tmp/vl_variables.VariableLibrary/valueSets/{branch}.json"
    )
   
pf.write_json(
    {
      "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
      "metadata": {
        "type": "VariableLibrary",
        "displayName": "vl_variables",
        "description": ""
      },
      "config": {
        "version": "2.0",
        "logicalId": "00000000-0000-0000-0000-000000000000",
      }
    },
    "../tmp/vl_variables.VariableLibrary/.platform"
)

pf.write_json(
    {
      "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/settings/1.0.0/schema.json",
      "valueSetsOrder": [
        "develop",
        "main"
      ]
    },
    "../tmp/vl_variables.VariableLibrary/settings.json"
)

pf.write_json(
    {
      "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/variableLibrary/definition/variables/1.0.0/schema.json",
      "variables": [
        {
          "name": "workspace_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "workspace_name",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "pool_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_bronze_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_bronze_sql_endpoint_connection_string",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_bronze_sql_endpoint_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_silver_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_silver_sql_endpoint_connection_string",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_silver_sql_endpoint_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_gold_id",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_gold_sql_endpoint_connection_string",
          "note": "",
          "type": "String",
          "value": ""
        },
        {
          "name": "lake_gold_sql_endpoint_id",
          "note": "",
          "type": "String",
          "value": ""
        }
      ]
    },
    "../tmp/vl_variables.VariableLibrary/variables.json"
)

logger.success(f"Created the temporary Variable Library template in ../tmp/vl_variables.VariableLibrary")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create Variable Libraries in each Workspace
for b in branches:
    suffix = b["suffix"]
    pf.create_variable_library(
        workspace=f"{project_name}-{suffix}",
        display_name="vl_variables",
        item_definition=pf.pack_item_definition(path="../tmp/vl_variables.VariableLibrary"),
        folder="utils",
    ) 
    logger.success(f"Variable Library vl_libraries created in workspace {project_name}-{suffix}")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Create Azure DevOps Connection and connect to DEV workspace
connection_name = f"AzureDevOps-{project_name}"
workspace_id = pf.resolve_workspace(f"{project_name}-DEV")

# Create connection to Azure DevOps using service principal authentication. 
# Make sure to set env vars FAB_CLIENT_ID, FAB_CLIENT_SECRET and FAB_TENANT_ID with the credentials of the service principal.
# The service principal must have at least "Project Contributor" role in the Azure DevOps project to be able to connect it to FabricOpsFlow.
connection = pf.create_azure_devops_connection_with_service_principal(
    display_name=connection_name,
    repository_url=devops_url,
    client_id=os.getenv("FAB_CLIENT_ID"),
    client_secret=os.getenv("FAB_CLIENT_SECRET"),
    tenant_id=os.getenv("FAB_TENANT_ID"),
)

# If connection creation fails (e.g. because it already exists), retrieve the existing connection
if connection is not None:
    display(connection)
    
connection_id = pf.resolve_connection(connection_name)

# Assign owners to connection
for role in roles:
    pf.add_connection_role_assignment(
        connection=connection_id,
        user_uuid=role["user_uuid"],
        user_type=role["user_type"],
        role="Owner",
        df=False
    )

# Connect Azure DevOps repository to FabricOpsFlow workspace. 
pf.ado_connect(
    workspace=workspace_id,
    connection_id=connection_id,
    organization_name=devops_organization_name, 
    project_name=devops_project_name,
    repository_name=devops_repository_name,
    branch_name="develop",
    directory_name="src",
)

# If the repository was already connected, update the connection settings to ensure they are correct.
pf.update_my_git_connection(
    workspace=workspace_id,
    request_body_type="UpdateGitCredentialsToConfiguredConnectionRequest",
    connection_id=connection_id,
)

# Initialize Git repository in workspace and make initial commit.     
pf.git_init(workspace=workspace_id, initialize_strategy="PreferWorkspace", df=False)
pf.commit_to_git(workspace=workspace_id, comment="Initial commit", df=False)


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
