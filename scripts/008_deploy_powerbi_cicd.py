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


# Deploy the folders first.
pf.deploy_folders(
	workspace=workspace_id, 
	project_path=project_path,
	branches_path=branches_path,
)  


# Deploy the calendar dataflow gen1
# Due a conflict with others dataflow generations and limitations with folders we need deploy it separately.
pf.deploy_dataflow_gen1(
	workspace=workspace_id, 
	path=f'{project_path}/workspace/Calendar.Dataflow',
)  


# Export dataflow config
# Dataflows gen1 don't have folders support on export.
# They arrive in the root of the workspace.
pf.export_all_dataflows_gen1(
	workspace=workspace_id,
				project_path=project_path,
	branches_path=branches_path,
)


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


# Deploy all the semantic models
pf.deploy_all_semantic_models(
	workspace=workspace_id, 
	project_path=project_path,
	branches_path=branches_path,
)


# Retrieving the semantic_model_details
pf.export_all_semantic_models(
	workspace=workspace_id, 
	project_path=project_path,
	branches_path=branches_path,
)


# After deploying the semantic models, we change the values to placeholders to commit the changes.
for semantic_model_path in glob.glob(f'{project_path}/**/*.SemanticModel', recursive=True):
	print(f'Processing semantic model: {semantic_model_path}')
	semantic_model_name = semantic_model_path.replace('\\', '/').split('/')[-1].split('.SemanticModel')[0] 
	print(f'Injecting placeholders into: {semantic_model_name}')  

	# Retrieve the parameters to build the placeholders
	semantic_model_config = semantic_models_config[semantic_model_name]
	semantic_model_parameters = semantic_model_config['parameters']

	# Read the current content of expressions.tmdl (with the actual values)
	expressions_path = f'{semantic_model_path}/definition/expressions.tmdl'
	with open(expressions_path, 'r', encoding='utf-8') as f:
		expressions = f.read()

	# Replace the values with placeholders
	expressions_with_placeholders = expressions

	for parameter_name, parameter_obj in semantic_model_parameters.items():
		actual_value = parameter_obj["Value"]
		# Create the pattern to replace: Param = "CurrentValue"
		pattern = rf'{parameter_name}\s*=\s*"{re.escape(actual_value)}"'
		# Replace: Param = "#{Param}#"
		replacement = f'{parameter_name} = "#{{{parameter_name}}}#"'
		expressions_with_placeholders = re.sub(pattern, replacement, expressions_with_placeholders)
		print(f"Replaced {parameter_name} value with placeholder.")

	# Write back the result on file
	with open(expressions_path, 'w', encoding='utf-8') as f:
		f.write(expressions_with_placeholders)


# For each report, we will define the report attached to the semantic model and deploy it.
for report_path in glob.glob(f'{project_path}/**/*.Report', recursive=True):
	print(f'Processing report: {report_path}')
	report_name = report_path.replace('\\', '/').split('/')[-1].split('.Report')[0] 
	print(f'Deploying report: {report_name}')

	with open(f'{report_path}/definition.pbir', 'r') as f:
		report_definition = json.load(f)

	dataset_reference = report_definition['datasetReference']

	if 'byPath' in dataset_reference:
		dataset_path = dataset_reference['byPath']['path'] 
		dataset_name = dataset_path.split('/')[-1].split('.SemanticModel')[0]

	elif 'byConnection' in dataset_reference:
		text_to_search = dataset_reference['byConnection']['connectionString']
		# Capture the value after "initial catalog="
		match = re.search(r'initial catalog=([^;]+)', text_to_search)
		if match:
			dataset_name = match.group(1)

	print(f'Semantic model: {dataset_name}')
	
	# Search for the semantic model in the config.json
	with open(config_path, 'r') as f:
		config_content = json.load(f)
	config = config_content[branch]
	semantic_model_id = config[project]['semantic_models'][dataset_name]['id'] 
	print(f'Semantic Model ID: {semantic_model_id}')  
	
	# Replace the definition.pbir with the updated template
	with open(os.path.join(repo_root, 'template_report_definition.pbir'), 'r', encoding='utf-8') as f:
		report_definition_template = f.read()

	report_definition_updated = report_definition_template.replace('{workspace_name}', workspace_name)
	report_definition_updated = report_definition_updated.replace('{semantic_model_name}', dataset_name)
	report_definition_updated = report_definition_updated.replace('{semantic_model_id}', semantic_model_id)
	
	# Write the updated report definition to the definition.pbir    
	with open(f'{report_path}/definition.pbir', 'w', encoding='utf-8') as f:
		f.write(report_definition_updated)
	
	# Deploy the report
	pf.deploy_report(
		workspace=workspace_id, 
		display_name=report_name,
		project_path=project_path,
		branches_path=branches_path,
	)
	
	# Write back the original report_definition for the definition.pbir
	with open(f'{report_path}/definition.pbir', 'w', encoding='utf-8') as f:
		json.dump(report_definition, f, indent=2)



