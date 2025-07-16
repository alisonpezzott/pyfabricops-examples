import sys
import os

# Add root directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts._pbi_cd_pipelines import pbi_update_from_git

pbi_update_from_git(
    project="PowerBIDemo",
    workspace_alias="PowerBIDemo",
    project_path='src/PowerBIDemo',
)
