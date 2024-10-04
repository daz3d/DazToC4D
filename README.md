# Daz To Cinema 4D Bridge
A Daz Studio Plugin based on Daz Bridge Library, allowing transfer of Daz Studio characters and
props to Cinema 4D.

* Owner: [Daz 3D][OwnerURL] – [@Daz3d][TwitterURL]
* License: [Apache License, Version 2.0][LicenseURL] - see ``LICENSE`` and ``NOTICE`` for more information.
* Offical Release: [Daz to Cinema 4D Bridge][ProductURL]
* Official Project: [github.com/daz3d/DazToC4D][RepositoryURL]


## Table of Contents
1. About the Bridge
2. Prerequisites
3. How to Install
4. How to Use
5. How to Build
6. How to QA Test
7. How to Develop
8. Directory Structure

## 1. About the Bridge
This is a refactored version of the original DazToC4D Bridge using the Daz Bridge Library as a foundation. Using the Bridge Library allows it to share source code and features with other bridges such as the refactored DazToUnity and DazToBlender bridges. This will improve development time and quality of all bridges.

The Daz To Cinema 4D Bridge consists of two parts: a Daz Studio plugin which exports assets to Cinema 4D and a Cinema 4D plugin which contains scripts and other resources to help recreate the look of the original Daz Studio asset in Cinema 4D.


## 2. Prerequisites
- A compatible version of the [Daz Studio][DazStudioURL] application
  - Minimum: 4.10
- A compatible version of the [Cinema 4D][Cinema4DURL] application
  - Minimum: R21 (Older versions may work with limited capabilities)
- Operating System:
  - Windows 7 or newer
  - macOS 10.13 (High Sierra) or newer

Daz Studio 4.22+ and Cinema 4D 2023+ should be used to take full advantage of the latest features of this plugin.

## 3. How to Install
### Daz Studio ###
- You can install the Daz To Cinema 4D Bridge automatically through the Daz Install Manager.  This will automatically add a new menu option under File -> Send To -> Daz To Cinema 4D.
- Alternatively, you can manually install by downloading the latest build from Github Release Page and following the instructions there to install into Daz Studio.

### Cinema 4D ###
1. Cinema 4D no longer requires a Plugins subfolder in the location where Cinema 4D was installed.  Since R20, users should set a plugins path inside the Cinema 4D Preferences window and install plugins to that folder.  We recommend creating a "**`\Documents\Cinema4D\Plugins`**" folder in your user's home folder and selecting that as the Plugins path in Cinema 4D.  Please refer to this link for more information: [Where do I install plugins? - Cinema 4D Knowledge Base](https://support.maxon.net/hc/en-us/articles/1500006433061-Where-do-I-install-plugins-)
2. The Daz Studio Plugin comes embedded with an installer for the Cinema 4D plugin.  From the Daz To Cinema 4D Bridge Dialog, there is now section in the Advanced Settings section for Installing the Cinema 4D Plugin.
3. Click the "Install Plugin" button.  You will see a window popup to choose a folder to install the Cinema 4D plugin.  
4. Navigate to the plugins folder path which you set from the Cinema 4D Preferences window, and click "Select Folder".  You will then see a confirmation dialog stating if the plugin installation was successful.
5. If Cinema 4D is running, you will need to restart for the Daz To Cinema 4D Bridge plugin to load.
6. In Cinema 4D, you should now see "Daz 3D" in the Cinema 4D main menu.


## 4. How to Use
1. Open your character in Daz Studio.
2. Make sure any clothing or hair is parented to the main body.
3. From the main menu, select File -> Send To -> Daz To Cinema 4D.  Alternatively, you may select File -> Export and then choose "Cinema 4D" from the Save as type drop down option.
4. A dialog will pop up: choose what type of conversion you wish to do, "Static Mesh" (no skeleton), "Skeletal Mesh" (Character or with joints), "Animation", or "Environment" (all meshes in scene).
5. To enable Morphs or Subdivision levels, click the CheckBox to Enable that option, then click the "Choose Morphs" or "Bake  Subdivisions" button to configure your selections.
6. Click Accept, then wait for a dialog popup to notify you when to switch to Cinema 4D.
7. From Cinema 4D, select Daz 3D -> Daz to C4D from the main menu. A DazToC4D dialog window should appear.
8. For Daz Characters or other assets transferred with the "Skeletal Mesh" option, select `GENESIS CHARACTERS`.  For props or other assets transferred using the "Static Mesh" or "Environment" option, select `ENVIRONMENTS + PROPS`.

### Morphs ###
- If you enabled the Export Morphs option, there will be a new "Morph Controller Group" node in the Object Manager panel.  Select this node and you will see morph sliders appear in the "Attributes Manager" panel, under the "User Data" heading.

### Animation ###
- To use the "Animation" asset type option, your Figure must use animations on the Daz Studio "Timeline" system.  
- If you are using "aniMate" or "aniBlocks" based animations, you need to right-click in the "aniMate" panel and select "Bake To Studio Keyframes".  
- Once your animation is on the "Timeline" system, you can start the transfer using File -> Send To -> Daz To Cinema 4D.  
- In Cinema 4D, click the "GENESIS CHARACTERS" from the DazToC4D window.  Your character with animations should begin to import.  During the import procedure, DazToC4D will notify you that "Importing Posed Figure is not fully supported" and ask if you want to "fix bone orientation".  Click "No".  
- If you accidentally click "Yes", the animation frames will not import correctly.  To fix that, you can just restart the import by clicking the "GENESIS CHARACTERS" button from the DazToC4D window.
- The transferred animation should now be usable through the Cinema 4D Animation interface.

### Subdivision Support ###
- Daz Studio uses Catmull-Clark Subdivision Surface technology which is a mathematical way to describe an infinitely smooth surface in a very efficient manner. Similar to how an infinitely smooth circle can be described with just the radius, the base resolution mesh of a Daz Figure is actually the mathematical data in an equation to describe an infinitely smooth surface. For Software which supports Catmull-Clark Subdivision and subdivision surface-based morphs (also known as HD Morphs), there is no loss in quality or detail by exporting the base resolution mesh (subdivision level 0).
- For Software which does not fully support Catmull-Clark Subdivision or HD Morphs, we can "Bake" additional subdivision detail levels into the mesh to more closely approximate the detail of the original surface. However, baking each additional subdivision level requires exponentially more CPU time, memory, and storage space.  **If you do not have a high-end PC, it is likely that your system will run out of memory and crash if you set the exported subdivision level above 2.**
- When you enable Bake Subdivision options in the Daz To Cinema 4D bridge, the asset is transferred to Cinema 4D as a standard mesh with higher resolution vertex counts.


## 5. How to Build
Setup and configuration of the build system is done via CMake to generate project files for Windows or Mac.  The CMake configuration requires:
-	Modern CMake (tested with 3.27.2 on Win and 3.27.0-rc4 on Mac)
-	Daz Studio 4.5+ SDK (from DIM)
-	Fbx SDK 2020.1 (win) / Fbx SDK 2015.1 (mac)
-	OpenSubdiv 3.4.4

(Please note that you MUST use the Qt 4.8.1 build libraries that are built-into the Daz Studio SDK.  Using an external Qt library will result in build errors and program instability.)

Download or clone the DazToC4D github repository to your local machine. The Daz Bridge Library is linked as a git submodule to the DazBridge repository. Depending on your git client, you may have to use `git submodule init` and `git submodule update` to properly clone the Daz Bridge Library.

The build setup process is designed to be run with CMake gui in an interactive session.  After setting up the source code folder and an output folder, the user can click Configure.  CMake will stop during the configurtaion process to prompt the user for the following paths:

-	DAZ_SDK_DIR – the root folder to the Daz Studio 4.5+ SDK.  This MUST be the version purchased from the Daz Store and installed via the DIM.  Any other versions will NOT work with this source code project and result in build errors and failure. example: C:/Users/Public/Documents/My DAZ 3D Library/DAZStudio4.5+ SDK
-	DAZ_STUDIO_EXE_DIR – the folder containing the Daz Studio executable file.  example: C:/Program Files/DAZ 3D/DAZStudio4
-	FBX_SDK_DIR – the root folder containing the “include” and “lib” subfolders.  example: C:/Program Files/Autodesk/FBX/FBX SDK/2020.0.1
-	OPENSUBDIV_DIR – root folder containing the “opensubdiv”, “examples”, “cmake” folders.  It assumes the output folder was set to a subfolder named “build” and that the osdCPU.lib or libosdCPU.a static library files were built at: <root>/build/lib/Release/osdCPU.lib or <root>/build/lib/Release/libosdCPU.a.  A pre-built library for Mac and Windows can be found at https://github.com/danielbui78/OpenSubdiv/releases that contains the correct location for include and prebuilt Release static library  binaries.  If you are not using this precompiled version, then you must ensure the correct location for the OPENSUBDIV_INCLUDE folder path and OPENSUBDIV_LIB filepath.

Once these paths are correctly entered into the CMake gui, the Configure button can be clicked and the configuration process should resume to completion.  The project files can then be generated and the project may be opened.  Please note that a custom version of Qt 4.8 build tools and libraries are included in the DAZ_SDK_DIR.  If another version of Qt is installed in your system and visible to CMake, it will likely cause errors with finding the correct version of Qt supplied in the DAZ_SDK_DIR and cause build errors and failure.

The resulting project files should have “DzBridge-C4D", “DzBridge Static” and "C4D Plugin ZIP" as project targets.  The DLL/DYLIB binary file produced by "DzBridge-C4D" should be a working Daz Studio plugin.  The "C4D Plugin ZIP" project contains the automation scripts which package the Cinema 4D Plugin files into a zip file and prepares it for embedding into the main Daz Studio plugin DLL/DYLIB binary.


## 6. How to QA Test
To Do:
1. Write `QA Manaul Test Cases.md` for DazToC4D using the `Example QA Manual Test Cases.md`.
2. Implement the manual tests cases as automated test scripts in `Test/TestCases`.
3. Update `Test/UnitTests` with latest changes to DazToC4D class methods.

The `QA Manaul Test Cases.md` document should contain instructions for performing manual tests.  The Test folder also contains subfolders for UnitTests, TestCases and Results. To run automated Test Cases, run Daz Studio and load the `Test/testcases/test_runner.dsa` script, configure the sIncludePath on line 4, then execute the script. Results will be written to report files stored in the `Test/Reports` subfolder.

To run UnitTests, you must first build special Debug versions of the DazToC4D and DzBridge Static sub-projects with Visual Studio configured for C++ Code Generation: Enable C++ Exceptions: Yes with SEH Exceptions (/EHa). This enables the memory exception handling features which are used during null pointer argument tests of the UnitTests. Once the special Debug version of DazToC4D dll is built and installed, run Daz Studio and load the `Test/UnitTests/RunUnitTests.dsa` script. Configure the sIncludePath and sOutputPath on lines 4 and 5, then execute the script. Several UI dialog prompts will appear on screen as part of the UnitTests of their related functions. Just click OK or Cancel to advance through them. Results will be written to report files stored in the `Test/Reports` subfolder.

For more information on running QA test scripts and writing your own test scripts, please refer to `How To Use QA Test Scripts.md` and `QA Script Documentation and Examples.dsa` which are located in the Daz Bridge Library repository: https://github.com/daz3d/DazBridgeUtils.

Special Note: The QA Report Files generated by the UnitTest and TestCase scripts have been designed and formatted so that the QA Reports will only change when there is a change in a test result.  This allows Github to conveniently track the history of test results with source-code changes, and allows developers and QA testers to notified by Github or their git client when there are any changes and the exact test that changed its result.

## 7. How to Modify and Develop
The Daz Studio Plugin source code is contained in the `DazStudioPlugin` folder.  The main C++ class entrypoint for the plugin is "DzC4DAction" (.cpp/.h).   The Cinema 4D Plugin source code and resources are available in the `/Cinema 4D/appdir_common/plugins/DazToC4D` folder.  Daz Studio SDK API and Qt API reference information can be found within the "DAZ Studio SDK Docs" package.  On Windows, the main page of this documentation is installed by default to: `C:\Users\Public\Documents\My DAZ 3D Library\DAZStudio4.5+ SDK\docs\index.html`.

**DZ_BRIDGE_NAMESPACE**: The DazToC4D Bridge is derived from base classes in the Daz Bridge Library that are within the DZ_BRIDGE_NAMESPACE (see bridge.h). Prior published versions of the official Daz Bridge plugins used custom namespaces to isolate shared class names from each plugin.  While this theoretically works to prevent namespace collisions for platforms that adhere to C++ namespaces, it may not hold true for some implementations of Qt and the Qt meta-object programming model, which is heavily used by Daz Studio and the Bridge plugins.  Notably, C++ namespaces may not be isolating code on the Mac OS implementation of Qt.  With these limitations in mind, I have decided to remove the recommendation to rename the DZ_BRIDGE_NAMESPACE in order to streamline and reduce deployment complexity for potential bridge plugin developers.

In order to link and share C++ classes between this plugin and the Daz Bridge Library, a custom `CPP_PLUGIN_DEFINITION()` macro is used instead of the standard DZ_PLUGIN_DEFINITION macro and usual .DEF file. NOTE: Use of the DZ_PLUGIN_DEFINITION macro and DEF file use will disable C++ class export in the Visual Studio compiler.


## 8. Directory Structure
Within the `Cinema 4D` directory are hierarchies of subdirectories that correspond to locations on the target machine. Portions of the hierarchy are consistent between the supported platforms and should be replicated exactly while others serve as placeholders for locations that vary depending on the platform of the target machine.

Placeholder directory names used in this repository are:

Name  | Windows  | macOS
------------- | ------------- | -------------
appdata_common  | Equivalent to the expanded form of the `%AppData%` environment variable.  Sub-hierarchy is common between 32-bit and 64-bit architectures. | Equivalent to the `~/Library/Application Support` directory.  Sub-hierarchy is common between 32-bit and 64-bit architectures.
appdir_common  | The directory containing the primary executable (.exe) for the target application.  Sub-hierarchy is common between 32-bit and 64-bit architectures.  | The directory containing the primary application bundle (.app) for the target application.  Sub-hierarchy is common between 32-bit and 64-bit architectures.

The directory structure is as follows:
- `Cinema 4D`:                Files that pertain to the _Cinema 4D_ side of the bridge
  - `appdir_common`:          See table above
    - `plugins`:              Application data specific to the organization
      - `DazToC4D`:           Application data specific to the application
- `DazStudioPlugin`:          Files that pertain to the _Daz Studio_ side of the DazToC4D bridge
  - `Resources` :             Data files to be embedded into the Daz Studio Plugin and support scripts to facilitate this build stage.
- `dzbridge-common`:          Files from the Daz Bridge Library used by DazStudioPlugin
  - `Extras` :                Supplemental scripts and support files to help the conversion process, especially for game-engines and other real-time appllications.
- `Test`:                     Scripts and generated output (reports) used for Quality Assurance Testing.



[OwnerURL]: https://www.daz3d.com
[TwitterURL]: https://twitter.com/Daz3d
[LicenseURL]: http://www.apache.org/licenses/LICENSE-2.0
[ProductURL]: https://www.daz3d.com/cinema-4d-bridge
[RepositoryURL]: https://github.com/daz3d/DazToC4D/
[DazStudioURL]: https://www.daz3d.com/get_studio
[ReleasesURL]: https://github.com/daz3d/DazToC4D/releases
[Cinema4DURL]: https://www.maxon.net/en/cinema-4d

