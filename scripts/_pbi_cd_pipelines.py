# Import support libraries
from dotenv import load_dotenv
import json
import os
from pathlib import Path
import pyfabricops as pf
import time
from typing import Literal


def _pbi_deploy_to_workspace(
    project: str,
    mode: Literal['init_from_local', 'update_from_local', 'update_from_git'],
    *,
    workspace_alias: str = None,
    project_path: str = None,
    dataflows_gen1: list[str] = None,
):
    """
    Deploys a Power BI project using PyFabricOps.
    This script sets up the workspace, deploys folders, dataflows, semantic models, and reports.
    """
    
    # Load environment variables from .env file
    load_dotenv()


    # Set authentication provider
    pf.set_auth_provider('env') 


    # Setup logging
    pf.setup_logging(format_style='minimal')


    # Project parameters
    project = project.strip()  # Ensure no leading/trailing spaces 
    workspace_alias = workspace_alias.strip() if workspace_alias else project.strip()  # Ensure no leading/trailing spaces
    root_path = pf.get_root_path()
    project_path = project_path if project_path else Path(root_path) / project


    # Get branch and workspace information
    branch = pf.get_current_branch()
    workspace_suffix = pf.get_workspace_suffix()
    workspace_name = workspace_alias + workspace_suffix 


    # Display project details
    print('=============== PROJECT DETAILS ===============')
    print(f'Project: {project}')
    print(f'Workspace: {workspace_name}')
    print(f'Project path: {project_path}') 
    print('===============================================')


    # Retrieve workspace roles configuration
    workspace_roles_path = os.path.join(root_path, 'workspaces_roles.json')
    print(f"Workspace roles configuration path: {workspace_roles_path}")
    with open(workspace_roles_path, 'r', encoding='utf-8') as f:
        roles = json.load(f)


    # Create workspace and assign roles
    pf.create_workspace(
        workspace_name, 
        description='A Power BI Project with PyFabricOps', 
        roles=roles,
    )


    # Export workspace configuration
    pf.export_workspace_config(
        workspace_name, 
        project_path, 
        branch=branch,
        workspace_suffix=workspace_suffix,
    ) 


    # Retrienving the workspace_id from config.json in the project_path for better performance
    config_path = f'{project_path}/config.json'
    config_content = pf.read_json(config_path)
    config = config_content[branch]  
    workspace_id = config[workspace_alias]['workspace_config']['workspace_id'] 
    print(f'Workspace ID: {workspace_id}')


    # Deploy the folders first
    pf.deploy_folders(
        workspace=workspace_id, 
        project_path=project_path,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    # Check if running in GitHub Actions or manually
    if os.environ.get('GITHUB_ACTIONS', '').lower() == 'true':
        print("Running inside GitHub Actions.")
        running_in_github_actions = True
    else:
        print("Running manually (not in GitHub Actions).")
        running_in_github_actions = False
        # Deploy the calendar dataflow gen1
        # Due a conflict with others dataflow generations and limitations with folders we need deploy it separately.
        if dataflows_gen1:
            for dataflow in dataflows_gen1:
                pf.deploy_dataflow_gen1(
                    workspace=workspace_id, 
                    path=f'{project_path}/{project}/{dataflow}',
                )


    # Export dataflow config
    # Dataflows gen1 don't have folders support on export.
    # They arrive in the root of the workspace.
    pf.export_all_dataflows_gen1(
        workspace=workspace_id,
        project_path=project_path,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    # Extract the parameters from semantic models
    if mode == 'init_from_local':
        pf.extract_semantic_models_parameters(
            project_path,
            workspace_alias=project,
            branch=branch,
        )


    # Replace the placeholders with actual values
    elif mode in ['update_from_local', 'update_from_git']:
        pf.replace_semantic_models_placeholders_with_parameters(
            project_path,
            workspace_alias=project,
            branch=branch,
        )


    pf.deploy_all_semantic_models(
        workspace=workspace_id, 
        project_path=project_path,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )

    # Time experienced during tests to deploy because of server
    time.sleep(5)

    pf.export_all_semantic_models(
        workspace_name, 
        project_path, 
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    pf.deploy_all_reports_cicd(
        project_path=project_path,
        workspace_alias=workspace_alias,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )

    # Replace parameters with placeholders to commit 
    # For local editing use the function pf.replace_semantic_models_placeholders_with_parameters
    pf.replace_semantic_models_parameters_with_placeholders(
        project_path,
        workspace_alias,
        branch=branch,
    )


def pbi_init_from_local(
    project: str,
    *,
    workspace_alias: str = None,
    project_path: str = None,
    dataflows_gen1: list = None,
):
    """
    Initialize the Power BI workspace with local files.

    Args:
        project (str): The name of the project.
        workspace_alias (str, optional): The alias of the workspace.
        project_path (str, optional): The path to the project files.
        dataflows_gen1 (list, optional): A list of Gen1 dataflows to include.

    Examples:
        pbi_init_workspace(
            project="PowerBIDemo",
            workspace_alias="PowerBIDemo",
            project_path="src/PowerBIDemo",
            dataflows_gen1=["Calendar.Dataflow"],
        )
    """
    _pbi_deploy_to_workspace(
        project=project,
        workspace_alias=workspace_alias,
        mode='init_from_local',
        project_path=project_path,
        dataflows_gen1=dataflows_gen1,
    )


def pbi_update_from_local(
    project: str,
    *,
    workspace_alias: str = None,
    project_path: str = None,
    dataflows_gen1: list = None,
):
    """
    Update the Power BI workspace with local files.

    Args:
        project (str): The name of the project.
        workspace_alias (str, optional): The alias of the workspace.
        project_path (str, optional): The path to the project files.
        dataflows_gen1 (list, optional): A list of Gen1 dataflows to include.

    Examples:
        pbi_update_from_local(
            project="PowerBIDemo",
            workspace_alias="PowerBIDemo",
            project_path="src/PowerBIDemo",
            dataflows_gen1=["Calendar.Dataflow"],
        )
    """
    _pbi_deploy_to_workspace(
        project=project,
        workspace_alias=workspace_alias,
        mode='update_from_local',
        project_path=project_path,
        dataflows_gen1=dataflows_gen1,
    )


def pbi_update_from_git(
    project: str,
    *,
    workspace_alias: str = None,
    project_path: str = None,
):
    """
    Update the Power BI workspace with files from the git repository.
    Ideal to use when you want to sync changes with GitHub Actions pipelines.
    This method doesn't sync dataflows Gen1 because API limitations.

    Args:
        project (str): The name of the project.
        workspace_alias (str, optional): The alias of the workspace.
        project_path (str, optional): The path to the project files.
        dataflows_gen1 (list, optional): A list of Gen1 dataflows to include.

    Examples:
        _update_from_git(
            project="PowerBIDemo",
            workspace_alias="PowerBIDemo",
            project_path="src/PowerBIDemo",
            dataflows_gen1=["Calendar.Dataflow"],
        )
    """
    _pbi_deploy_to_workspace(
        project=project,
        workspace_alias=workspace_alias,
        mode='update_from_git',
        project_path=project_path,
    )


def pbi_sync_from_workspace(
    project: str,
    *,
    workspace_alias: str = None,
    project_path: str = None,
):
    """
    Sync a Power BI Workspace with local.
    """
    
    # Load environment variables from .env file
    load_dotenv()


    # Set authentication provider
    pf.set_auth_provider('env') 


    # Setup logging
    pf.setup_logging(format_style='minimal')


    # Project parameters
    project = project.strip()  # Ensure no leading/trailing spaces 
    workspace_alias = workspace_alias.strip() if workspace_alias else project.strip()  # Ensure no leading/trailing spaces
    root_path = pf.get_root_path()
    project_path = project_path if project_path else Path(root_path) / project


    # Get branch and workspace information
    branch = pf.get_current_branch()
    workspace_suffix = pf.get_workspace_suffix()
    workspace_name = workspace_alias + workspace_suffix 


    # Display project details
    print('=============== PROJECT DETAILS ===============')
    print(f'Project: {project}')
    print(f'Workspace: {workspace_name}')
    print(f'Project path: {project_path}') 
    print('===============================================')


    # Retrieve workspace configuration
    pf.export_workspace_config(
        workspace_name,
        project_path,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    # Retrienving the workspace_id from config.json in the project_path for better performance
    config_path = f'{project_path}/config.json'
    config_content = pf.read_json(config_path)
    config = config_content[branch]  
    workspace_id = config[workspace_alias]['workspace_config']['workspace_id'] 
    print(f'Workspace ID: {workspace_id}')


    # Export all folders
    pf.export_folders(
        workspace=workspace_id, 
        project_path=project_path,
        workspace_path=workspace_alias,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    # Export dataflow config
    # Dataflows gen1 don't have folders support on export.
    # They arrive in the root of the workspace.
    pf.export_all_dataflows_gen1(
        workspace=workspace_id,
        project_path=project_path,
        workspace_path=workspace_alias,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    pf.export_all_semantic_models(
        workspace_name, 
        project_path,
        workspace_path=workspace_alias,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    pf.export_all_reports(
        workspace_name, 
        project_path,
        workspace_path=workspace_alias,
        branch=branch,
        workspace_suffix=workspace_suffix,
    )

    # Replace parameters with placeholders to commit 
    # For local editing use the function pf.replace_semantic_models_placeholders_with_parameters
    pf.replace_semantic_models_parameters_with_placeholders(
        project_path,
        workspace_alias,
        branch=branch,
    )

    # Convert byConnection by byPath on reports definitions.pbir
    pf.convert_reports_to_local_references(
        project_path,
        branch=branch,
    )


def pbi_enable_local_edit(
        project_path: str,
        workspace_alias: str,
        *,
        branch: str = None,
        config_path: str = None, 
):
    """
    Enable local editing for Power BI semantic models.
    """
    pf.replace_semantic_models_placeholders_with_parameters(
        project_path=project_path,
        workspace_alias=workspace_alias,
        branch=branch,
        config_path=config_path,
    )
