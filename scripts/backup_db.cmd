@echo off
REM AstroOS — scheduled backup wrapper (invoked by Windows Task Scheduler).
REM Runs the git-bash backup script and appends output to backups\backup.log.
REM Change the target DB by editing the "astroos" argument below.
if not exist "D:\AstroOS_Backups" mkdir "D:\AstroOS_Backups"
"C:\Program Files\Git\bin\bash.exe" "/c/Users/rkmau/Downloads/ReplitplusClaude/AstroOS/scripts/backup_db.sh" astroos 1>> "D:\AstroOS_Backups\backup.log" 2>&1
