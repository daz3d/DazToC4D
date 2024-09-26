#pragma once
#include <dzaction.h>
#include <dznode.h>
#include <dzjsonwriter.h>
#include <QtCore/qfile.h>
#include <QtCore/qtextstream.h>
#include <dzexporter.h>

#include <DzBridgeAction.h>
#include "DzC4DDialog.h"

class UnitTest_DzC4DAction;

#include "dzbridge.h"

class DzC4DExporter : public DzExporter {
	Q_OBJECT
public:
	DzC4DExporter() : DzExporter(QString("c4d")) { this->setObjectName("DzBridge_DazToC4D_Exporter"); };

public slots:
	virtual void getDefaultOptions(DzFileIOSettings* options) const {};
	virtual QString getDescription() const override { return QString("Cinema 4D File"); };
	virtual bool isFileExporter() const override { return true; };

protected:
	virtual DzError	write(const QString& filename, const DzFileIOSettings* options) override;
};

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
