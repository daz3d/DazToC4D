#pragma once
#include "dzbasicdialog.h"
#include <QtGui/qcombobox.h>
#include <QtCore/qsettings.h>
#include <DzBridgeDialog.h>

class QPushButton;
class QLineEdit;
class QCheckBox;
class QComboBox;
class QGroupBox;
class QLabel;
class QWidget;
class DzC4DAction;

class UnitTest_DzC4DDialog;

#include "dzbridge.h"

class DzC4DDialog : public DZ_BRIDGE_NAMESPACE::DzBridgeDialog{
	friend DzC4DAction;
	Q_OBJECT
	Q_PROPERTY(QWidget* intermediateFolderEdit READ getIntermediateFolderEdit)
public:
	Q_INVOKABLE QLineEdit* getIntermediateFolderEdit() { return intermediateFolderEdit; }

	/** Constructor **/
	 DzC4DDialog(QWidget *parent=nullptr);

	/** Destructor **/
	virtual ~DzC4DDialog() {}

	Q_INVOKABLE void resetToDefaults() override;
	Q_INVOKABLE bool loadSavedSettings() override;

protected slots:
	void HandleSelectIntermediateFolderButton();
	void HandleAssetTypeComboChange(int state) override;
	void HandleTargetPluginInstallerButton() override;
	void HandleOpenIntermediateFolderButton(QString sFolderPath = "") override;
    void HandleAssetTypeComboChange(const QString& assetType) override;
    
protected:
	QLineEdit* intermediateFolderEdit;
	QPushButton* intermediateFolderButton;

#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzC4DDialog;
#endif
};
