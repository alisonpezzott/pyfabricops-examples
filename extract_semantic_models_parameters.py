import glob
import re
import json

def extract_semantic_models_parameters(project_path: str, workspace_alias: str, branch: str, config_path: str) -> dict:
    """
    Extract parameters from semantic model definition files to a config.json file.

    Args:
        project_path (str): The path to the project directory.
        workspace_alias (str): The alias of the workspace.
        branch (str): The branch name.
        config_path (str): The path to the config.json file.

    Returns:
        dict: The extracted parameters.

    Examples:
        ```python
        extracted_params = extract_semantic_models_parameters(
            project_path='/path/to/project',
            workspace_alias='DemoWorkspace',
            branch='main',
            config_path='/path/to/config.json'
        )
        ```
    """
    # Read the config.json retriving the parameters for the semantic model
    try:
        with open(config_path, 'r') as f:
            config_content = json.load(f)
        config = config_content[branch]

        semantic_models_config = config[workspace_alias]['semantic_models']
    except:
        config_content = {}
        semantic_models_config = {}

    for semantic_model_path in glob.glob(f'{project_path}/**/*.SemanticModel', recursive=True):
        print(f'Capturing parameters from semantic model: {semantic_model_path}')
        semantic_model_name = semantic_model_path.replace('\\', '/').split('/')[-1].split('.SemanticModel')[0]

        # Read the expressions file
        expressions_path = f'{semantic_model_path}/definition/expressions.tmdl'
        with open(expressions_path, 'r') as f:
            expressions = f.read()

        # Pattern to capture: expression VariableName = "Value"
        pattern = r'expression\s+(\w+)\s*=\s*"([^"]*)"'
        matches = re.findall(pattern, expressions)

        variables = {}

        for match in matches:
            variable_name = match[0]
            variable_value = match[1]
            variables[variable_name] = variable_value

        if semantic_model_name not in semantic_models_config:
            semantic_models_config[semantic_model_name] = {}
        if 'parameters' not in semantic_models_config[semantic_model_name]:
            semantic_models_config[semantic_model_name]['parameters'] = variables

        # Add the variables to the semantic model config
        semantic_models_config[semantic_model_name]['parameters'].update(variables)

    # Print the captured parameters
    print(f'Captured parameters for semantic models: {json.dumps(semantic_models_config, indent=2)}')

    # Write back to config json
    if not branch in config_content:
        config_content[branch] = {}
    if not workspace_alias in config_content[branch]:
        config_content[branch][workspace_alias] = {}
    if not 'semantic_models' in config_content[branch][workspace_alias]:
        config_content[branch][workspace_alias]['semantic_models'] = semantic_models_config

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config_content, f, indent=4)
