# Daz To Cinema 4D Bridge
A Daz Studio Plugin based on Daz Bridge Library, allowing transfer of Daz Studio characters and
props to Cinema 4D.

# Table of Contents
1. About the Bridge
2. How to Install
3. How to Use
4. How to Build
5. How to QA Test
6. How to Develop

# 1. About the Bridge
This is a refactored version of the original DazToC4D Bridge using the Daz Bridge Library as a foundation. Using the Bridge Library allows it to share source code and features with other bridges such as the refactored DazToUnity and DazToBlender bridges. This will improve development time and quality of all bridges.

The Daz To Cinema 4D Bridge consists of two parts: a Daz Studio plugin which exports assets to Cinema 4D and a Cinema 4D Plugin which contains scripts and other resources to help recreate the look of the original Daz Studio asset in Cinema 4D.


# 2. How to Install
### Daz Studio ###
- You can install the Daz To Cinema 4D Bridge automatically through the Daz Install Manager or Daz Central.  This will automatically add a new menu option under File -> Send To -> Daz To Cinema 4D.
- Alternatively, you can manually install by downloading the latest build from Github Release Page and following the instructions there to install into Daz Studio.

### Cinema 4D ###
1. Cinema 4D no longer requires a Plugins subfolder in the location where Cinema 4D was installed.  Since R20, users should set a plugins path inside the Cinema 4D Preferences window and install plugins to that folder.  We recommend creating a "**`\Documents\Cinema4D\Plugins`**" folder in your user's home folder and selecting that as the Plugins path in Cinema 4D.  Please refer to this link for more information: [Where do I install plugins? - Cinema 4D Knowledge Base](https://support.maxon.net/hc/en-us/articles/1500006433061-Where-do-I-install-plugins-)
2. The Daz Studio Plugin comes embedded with an installer for the Cinema 4D plugin.  From the Daz To Cinema 4D Bridge Dialog, there is now section in the Advanced Settings section for Installing the Cinema 4D Plugin.
3. Click the "Install Plugin" button.  You will see a window popup to choose a folder to install the Cinema 4D plugin.  
4. Navigate to the plugins folder path which you set from the Cinema 4D Preferences window, and click "Select Folder".  You will then see a confirmation dialog stating if the plugin installation was successful.
5. If Cinema 4D is running, you will need to restart for the Daz To Cinema 4D Bridge plugin to load.
6. In Cinema 4D, you should now see "Daz 3D" in the Cinema 4D main menu.


# 3. How to Use
1. Open your character in Daz Studio.
2. Make sure any clothing or hair is parented to the main body.
3. From the main menu, select File -> Send To -> Daz To Cinema 4D.
4. A dialog will pop up: choose what type of conversion you wish to do, "Static Mesh" (no skeleton), "Skeletal Mesh" (Character or with joints), or "Animation".
5. To enable Morphs or Subdivision levels, click the CheckBox to Enable that option, then click the "Choose Morphs" or "Bake  Subdivisions" button to configure your selections.
6. Click Accept, then wait for a dialog popup to notify you when to switch to Cinema 4D.
7. From Cinema 4D, select Daz 3D -> Daz to C4D from the main menu. A DazToC4D dialog window should appear.
8. For Daz Characters or other assets transferred with the "Skeletal Mesh" option, select `GENESIS CHARACTERS`.  For props or other assets transferred using the "Static Mesh" option, select `ENVIRONMENTS + PROPS`.

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
- For Software which does not fully support Catmull-Clark Subdivision or HD Morphs, we can "Bake" additional subdivision detail levels into the mesh to more closely approximate the detail of the original surface. However, baking each additional subdivision level requires exponentially more CPU time, memory, and storage space.
- When you enable Bake Subdivision options in the Daz To Cinema 4D bridge, the asset is transferred to Cinema 4D as a standard mesh with higher resolution vertex counts.


# 4. How to Build
Requirements: Daz Studio 4.5+ SDK, Qt 4.8.1, Autodesk Fbx SDK, Pixar OpenSubdiv Library, CMake, C++ development environment

Download or clone the DazToC4D github repository to your local machine. The Daz Bridge Library is linked as a git submodule to the DazBridge repository. Depending on your git client, you may have to use `git submodule init` and `git submodule update` to properly clone the Daz Bridge Library.

Use CMake to configure the project files. Daz Bridge Library will be automatically configured to static-link with DazToC4D. If using the CMake gui, you will be prompted for folder paths to dependencies: Daz SDK, Qt 4.8.1, Fbx SDK and OpenSubdiv during the Configure process.


# 5. How to QA Test
To Do:
1. Write `QA Manaul Test Cases.md` for DazToC4D using the `Example QA Manual Test Cases.md`.
2. Implement the manual tests cases as automated test scripts in `Test/TestCases`.
3. Update `Test/UnitTests` with latest changes to DazToC4D class methods.

The `QA Manaul Test Cases.md` document should contain instructions for performing manual tests.  The Test folder also contains subfolders for UnitTests, TestCases and Results. To run automated Test Cases, run Daz Studio and load the `Test/testcases/test_runner.dsa` script, configure the sIncludePath on line 4, then execute the script. Results will be written to report files stored in the `Test/Reports` subfolder.

To run UnitTests, you must first build special Debug versions of the DazToC4D and DzBridge Static sub-projects with Visual Studio configured for C++ Code Generation: Enable C++ Exceptions: Yes with SEH Exceptions (/EHa). This enables the memory exception handling features which are used during null pointer argument tests of the UnitTests. Once the special Debug version of DazToC4D dll is built and installed, run Daz Studio and load the `Test/UnitTests/RunUnitTests.dsa` script. Configure the sIncludePath and sOutputPath on lines 4 and 5, then execute the script. Several UI dialog prompts will appear on screen as part of the UnitTests of their related functions. Just click OK or Cancel to advance through them. Results will be written to report files stored in the `Test/Reports` subfolder.

For more information on running QA test scripts and writing your own test scripts, please refer to `How To Use QA Test Scripts.md` and `QA Script Documentation and Examples.dsa` which are located in the Daz Bridge Library repository: https://github.com/daz3d/DazBridgeUtils.

Special Note: The QA Report Files generated by the UnitTest and TestCase scripts have been designed and formatted so that the QA Reports will only change when there is a change in a test result.  This allows Github to conveniently track the history of test results with source-code changes, and allows developers and QA testers to notified by Github or their git client when there are any changes and the exact test that changed its result.

# 6. How to Modify and Develop
The Daz Studio Plugin source code is contained in the `DazStudioPlugin` folder. The Cinema 4D Plugin source code and resources are available in the `/Cinema 4D/appdir_common/plugins/DazToC4D` folder.

The DazToC4D Bridge uses a branch of the Daz Bridge Library which is modified to use the `DzC4DNS` namespace. This ensures that there are no C++ Namespace collisions when other plugins based on the Daz Bridge Library are also loaded in Daz Studio. In order to link and share C++ classes between this plugin and the Daz Bridge Library, a custom `CPP_PLUGIN_DEFINITION()` macro is used instead of the standard DZ_PLUGIN_DEFINITION macro and usual .DEF file. NOTE: Use of the DZ_PLUGIN_DEFINITION macro and DEF file use will disable C++ class export in the Visual Studio compiler.
