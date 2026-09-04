@echo off
REM AstroOS — scheduled backup wrapper (invoked by Windows Task Scheduler).
REM Runs the git-bash backup script and appends output to backups\backup.log.
REM Backs up BOTH databases: "astroos" (legacy/populated) and "astroos_db"
REM (the app's live DB per .env). astroos_db was previously never backed
REM up here, which meant a data-loss incident on it had no recovery path.
if not exist "D:\AstroOS_Backups" mkdir "D:\AstroOS_Backups"
"C:\Program Files\Git\bin\bash.exe" "/c/Users/rkmau/Downloads/ReplitplusClaude/AstroOS/scripts/backup_db.sh" astroos 1>> "D:\AstroOS_Backups\backup.log" 2>&1
"C:\Program Files\Git\bin\bash.exe" "/c/Users/rkmau/Downloads/ReplitplusClaude/AstroOS/scripts/backup_db.sh" astroos_db 1>> "D:\AstroOS_Backups\backup.log" 2>&1
