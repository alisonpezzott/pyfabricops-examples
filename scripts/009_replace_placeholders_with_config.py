import glob
import json
import os
import pyfabricops as pf
import re
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


# Retrienving the workspace_id from config.json in the project_path for better performance
config_path = f'{project_path}/config.json'
with open(config_path, 'r') as f:
  config_content = json.load(f)
  config = config_content[branch]  
  workspace_id = config[project]['workspace_config']['workspace_id'] 
print(f'Workspace ID: {workspace_id}')


# Read the config.json retriving the parameters for the semantic model
with open(config_path, 'r') as f:
	config_content = json.load(f)
config = config_content[branch]

semantic_models_config = config[project]['semantic_models']


# Replacing the parameters in the semantic models with the values from config.json
for semantic_model_path in glob.glob(f'{project_path}/**/*.SemanticModel', recursive=True):
	print(f'Processing semantic model: {semantic_model_path}')
	semantic_model_name = semantic_model_path.replace('\\', '/').split('/')[-1].split('.SemanticModel')[0] 
	print(f'Deploying semantic model name: {semantic_model_name}')  

	# Retrieving the semantic model config
	semantic_model_config = semantic_models_config[semantic_model_name]
	semantic_model_parameters = semantic_model_config['parameters']

	# Read the expressions file
	expressions_path = f'{semantic_model_path}//definition/expressions.tmdl'
	with open(expressions_path, 'r') as f:
		expressions = f.read()

	# Build variables dictionary dynamically from config.json
	variables_to_replace = {}
	for parameter_name, parameter_obj in semantic_model_parameters.items():
		variables_to_replace[parameter_name] = parameter_obj['Value']
		print(f"Found parameter: {parameter_name} = {parameter_obj['Value']}")
	
	# Start with original expressions
	expressions_updated = expressions

	# Replace each variable using regex
	for variable_name, new_value in variables_to_replace.items():
		# Pattern to match: VariableName = "any_value"
		pattern = rf'{variable_name}\s*=\s*"[^"]*"'
		replacement = f'{variable_name} = "{new_value}"'
		expressions_updated = re.sub(pattern, replacement, expressions_updated)
		print(f"Replaced {variable_name} with: {new_value}")

	# Write the updated expressions back to the file
	with open(expressions_path, 'w', encoding='utf-8') as f:
		f.write(expressions_updated)
