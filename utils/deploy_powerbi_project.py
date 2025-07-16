# Import support libraries
from dotenv import load_dotenv
import json
import os
from pathlib import Path
import pyfabricops as pf
from typing import Literal

def deploy_powerbi_project(
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


    pf.export_all_semantic_models(
        workspace_name, 
        project_path, 
        branch=branch,
        workspace_suffix=workspace_suffix,
    )


    pf.deploy_all_reports_cicd(
        project_path=project_path,
        workspace_alias=project,
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
