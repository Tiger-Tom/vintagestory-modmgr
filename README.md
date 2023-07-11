# vintagestory-modmgr
A simple script to easily update and share lists of mods for Vintage Story. Note that there are several ways to have the script (such as when [bundled](#a-word-of-warning-for-bundled-scripts)), and two main ways to use it:
- [CLI Mode](#cli-mode), which is faster and more stable, but less user-friendly than the
- [GUI Mode](#gui-mode), which is unfortunately less stable, but more user-friendly

## A word of warning for bundled scripts
The MacOS bundled executables are completely untested. I neither have a Mac, nor am able to test it myself through virtual machines.  
The Windows `.exe`s I can test, but are noticable slower and bulkier than simply running the script through an installed Python runtime.  
The `.pyz` "zipapps" are the recommended way to use a "bundled" version of the script, but will require that you install Python libraries and Python itself manually. 

## CLI Mode
*Note: The CLI mode is faster and more stable than the GUI mode, but is less user-friendly to less technical users.*  

When using the CLI mode, each mode is a subcommand. The following subcommands and their usage is listed below:
|     Subcommand     | Purpose
| :----------------: | :------
| [`gui`](#gui-mode)              | The default mode. Invokes [GUI mode](#gui-mode)
| [`update`](#cli---updating-mods)  | Used to update mods in a folder
| [`import`](#cli---importing-mods) | Used to import a `.vsmmgr` "modpack" file into a folder
| [`export`](#cli---exporting-mods) | Used to export mods from a folder into a `.vsmmgr` "modpack" file

Below, in each section, each command example will be given as `[subcommand] [...args]`. Keep in mind that the main program must be invoke -- whether through `./main.py`, `python3 main.py`, or however, so that the complete command looks something like: `./main.py [subcommand] [...args]`. 

### CLI - Updating mods
### CLI - Importing mods
### CLI - Exporting mods


## GUI Mode
*Note: The GUI mode is slower and more unstable than the CLI mode, but is more user-friendly to less technical users.*  
**This covers usage of the basic, built-in GUI mode. Other GUIs can be used as well, but will behave differently!**

### THE GUI MODE IS NOT READY FOR USE AND IS UNDER HEAVY DEVELOPMENT