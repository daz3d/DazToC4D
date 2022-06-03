#pragma once
#include <dzaction.h>
#include <dznode.h>
#include <dzjsonwriter.h>
#include <QtCore/qfile.h>
#include <QtCore/qtextstream.h>
#include <DzBridgeAction.h>
#include "DzC4DDialog.h"

class UnitTest_DzC4DAction;

#include "dzbridge.h"

class DzC4DAction : public DZ_BRIDGE_NAMESPACE::DzBridgeAction {
	 Q_OBJECT
public:
	DzC4DAction();

protected:

	 void executeAction();
	 Q_INVOKABLE bool createUI();
	 Q_INVOKABLE void writeConfiguration();
	 Q_INVOKABLE void setExportOptions(DzFileIOSettings& ExportOptions);
	 QString readGuiRootFolder();

#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzC4DAction;
#endif

};
