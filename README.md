# 3d-printer

Our 3D print files for a **Flashforge AD5X**, sliced in **Orca-Flashforge**.

The printer setup, filament temperatures, settings that work, lessons learned and the print log
are all in **[PRINTER-BRAIN.md](PRINTER-BRAIN.md)**.

To check that a file will print on the AD5X before sending it (`.stl`, `.3mf`, `.gcode.3mf` or
`.gcode`; a folder checks everything in it):

```sh
python3 tools/check_print.py "shed model 12x24 garage" --summary
```
