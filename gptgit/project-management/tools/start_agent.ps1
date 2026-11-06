[CmdletBinding()]
param(
 [Parameter(Mandatory)][ValidateSet('planner','researcher','writer','developer','reviewer','qa')][string]$Role,
 [Parameter(Mandatory)][string]$Model,
 [Parameter(Mandatory)][string]$Name,
 [switch]$CheckOnly
)
$ErrorActionPreference='Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
 $launchArgs=@('-B','-X','utf8','../tools/start_managed_agent.py','--role',$Role,'--model',$Model,'--name',$Name)
 if($CheckOnly){$launchArgs+='--check-only'}
 & python @launchArgs
 $resultCode=$LASTEXITCODE
} finally { Pop-Location }
exit $resultCode
