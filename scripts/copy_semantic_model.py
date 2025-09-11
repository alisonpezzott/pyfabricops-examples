# pip install -U pyfabricops
import pyfabricops as pf

pf.set_auth_provider('oauth')
pf.setup_logging(level='info', format_style='minimal')

ws_src = 'PyFabricOps'
ws_tgt = 'PyFabricOps_Copy'
sm_name = 'Sales'
path = './src'

# Get semantic model from source workspace
pf.export_semantic_model(
    workspace=ws_src, 
    semantic_model=sm_name, 
    path=path, 
)

# Create target workspace if it does not exist
pf.create_workspace(display_name=ws_tgt)

# Deploy semantic model to target workspace
pf.deploy_semantic_model(
    workspace=ws_tgt, 
    path=f'{path}/{sm_name}.SemanticModel', 
    start_path=path,
)

