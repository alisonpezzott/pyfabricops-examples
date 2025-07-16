from ..utils.deploy_powerbi_project import deploy_powerbi_project

deploy_powerbi_project(
    project="PowerBIDemo",
    workspace_alias="PowerBIDemo",
    mode='init_from_local',
    project_path='src/PowerBIDemo',
    dataflows_gen1=['Calendar.Dataflow'],
)
