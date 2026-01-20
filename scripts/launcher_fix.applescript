-- Forensic Auditor: macOS Sovereign Launcher
-- This script launches the orchestrator in the background, bypassing all AppleEvents automation

set projectDir to do shell script "dirname " & quoted form of POSIX path of (path to me)
set launchScript to quoted form of (projectDir & "/launch.sh")

-- Run in background and redirect logs
do shell script "cd " & quoted form of projectDir & " && nohup ./launch.sh > app_launch.log 2>&1 &"

-- Optionally notify user
display notification "Financial Compliance Auditor is starting..." with title "Auditor Launcher"
