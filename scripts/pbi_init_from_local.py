import sys
import os

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts._pbi_cd_pipelines import pbi_init_from_local

pbi_init_from_local(
    project="PowerBIDemo",
    workspace_alias="PowerBIDemo",
    project_path='src/PowerBIDemo',
    dataflows_gen1=['Calendar.Dataflow'],
)
