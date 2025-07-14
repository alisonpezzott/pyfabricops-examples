# Libraries
import json
import os
import pyfabricops as pf
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Enable logging and set authentication provider
pf.enable_notebook_logging() # Enable logging for script
pf.set_auth_provider('env') 

# Get repo root
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # Goes up one level from notebooks folder
project = 'PowerBIDemo'
project_path = os.path.join(repo_root, 'src', project)
print(f"Project path: {project_path}")

# Define branches configuration path
branches_path = os.path.join(repo_root, 'branches.json')
print(f"Branches configuration path: {branches_path}")

# Load branches configuration
branch = pf.get_current_branch()
workspace_suffix = pf.get_workspace_suffix(path=branches_path)

# Define workspace name based on project and branch
workspace_name = project + workspace_suffix
print(f'Branch: {branch}, Workspace: {workspace_name}') 

# Create workspace, assign roles and extract configuration

# Extract workspace roles configuration
workspace_roles_path = os.path.join(repo_root, 'workspaces_roles.json')
print(f"Workspace roles configuration path: {workspace_roles_path}")
with open(workspace_roles_path, 'r', encoding='utf-8') as f:
    roles = json.load(f)

# Create workspace and assign roles
pf.create_workspace(
    workspace_name, 
    description='First Power BI Project with PyFabricOps', 
	roles=roles,
)

# Export workspace configuration
pf.export_workspace_config(
    workspace_name, 
    project_path, 
    branches_path=branches_path,
)  