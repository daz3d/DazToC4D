#include "dzplugin.h"
#include "dzapp.h"

#include "version.h"
#include "DzC4DAction.h"
#include "DzC4DDialog.h"

#include "dzbridge.h"

CPP_PLUGIN_DEFINITION("Daz To Cinema 4D Bridge");

DZ_PLUGIN_AUTHOR("Daz 3D, Inc");

DZ_PLUGIN_VERSION(PLUGIN_MAJOR, PLUGIN_MINOR, PLUGIN_REV, PLUGIN_BUILD);

#ifdef _DEBUG
DZ_PLUGIN_DESCRIPTION(QString(
	"<b>Pre-Release Cinema 4D Bridge v%1.%2.%3.%4 </b><br>\
<a href = \"https://github.com/daz3d/DazToC4D\">Github</a><br><br>"
).arg(PLUGIN_MAJOR).arg(PLUGIN_MINOR).arg(PLUGIN_REV).arg(PLUGIN_BUILD));
#else
DZ_PLUGIN_DESCRIPTION(QString(
"This plugin provides the ability to send assets to Cinema 4D. \
Documentation and source code are available on <a href = \"https://github.com/daz3d/DazToC4D\">Github</a>.<br>"
));
#endif

DZ_PLUGIN_CLASS_GUID(DzC4DAction, 9d8e995e-e153-4c27-b3c8-6064b56d85eb);
NEW_PLUGIN_CUSTOM_CLASS_GUID(DzC4DDialog, b9ed0623-b5f8-4f5e-a031-f16027b30c59);

#ifdef UNITTEST_DZBRIDGE

#include "UnitTest_DzC4DAction.h"
#include "UnitTest_DzC4DDialog.h"

DZ_PLUGIN_CLASS_GUID(UnitTest_DzC4DAction, 4dd8714e-f912-4fb9-b1db-eef25c7df022);
DZ_PLUGIN_CLASS_GUID(UnitTest_DzC4DDialog, 846ddb32-4e16-449f-bc2a-16d999161c71);

#endif
