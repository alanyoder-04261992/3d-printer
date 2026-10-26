# 3D Prints

Our 3D print files for a Flashforge AD5X, sliced in Orca-Flashforge. The full setup and
everything we've learned is in the printer brain:

@PRINTER-BRAIN.md

## Keeping the brain current
- When the setup changes (new nozzle, new filament, new firmware, a saved preset), update
  `PRINTER-BRAIN.md` and bump its "Last updated" date.
- When a print teaches us something, add a row to the **Print log** and, if it's a general
  rule, a line under **Lessons learned**.
- Read the settings saved inside a `.3mf` (`Metadata/project_settings.config`) rather than
  guessing what a file was sliced with.

## Working in this folder
- Git history is stored outside OneDrive at `%USERPROFILE%\.git-repos\3d-printer`; the `.git`
  file here points to it. Don't move it back into the folder.
- Any file over 100 MB must be tracked with Git LFS (`git lfs track --filename "<path>"`)
  before it is committed.
- The GitHub repo is public. Never commit the printer's serial number, logs, IP address or
  account details.
- Orca-Flashforge must be closed before editing anything in `%APPDATA%\Orca-Flashforge`.
