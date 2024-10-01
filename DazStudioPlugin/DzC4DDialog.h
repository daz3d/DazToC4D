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
class QHBoxLayout;

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

	bool isC4DTextBoxValid(const QString& text = "");
	bool disableAcceptUntilAllRequirementsValid();
	Q_INVOKABLE void requireC4DExecutableWidget(bool bRequired);


	Q_INVOKABLE void resetToDefaults() override;
	Q_INVOKABLE bool loadSavedSettings() override;
	Q_INVOKABLE void saveSettings() override;
	void accept() override;


protected:
	virtual void showEvent(QShowEvent* event) override { disableAcceptUntilAllRequirementsValid(); DzBridgeDialog::showEvent(event); }

protected slots:
	void HandleSelectIntermediateFolderButton();
	void HandleAssetTypeComboChange(int state) override;
	void HandleTargetPluginInstallerButton() override;
	void HandleOpenIntermediateFolderButton(QString sFolderPath = "") override;
	void HandlePdfButton() override;
	void HandleYoutubeButton() override;
	void HandleSupportButton() override;

	bool HandleAcceptButtonValidationFeedback();

	void HandleSelectC4DExecutablePathButton();
	void HandleTextChanged(const QString& text);
	void updateC4DExecutablePathEdit(bool isValid);

protected:
	QLineEdit* intermediateFolderEdit;
	QPushButton* intermediateFolderButton;

	QLineEdit* m_wC4DExecutablePathEdit;
	DzBridgeBrowseButton* m_wC4DExecutablePathButton;
	QHBoxLayout* m_wC4DExecutablePathLayout;
	QLabel* m_wC4DExecutableRowLabel;

	bool m_bC4DRequired = false;


#ifdef UNITTEST_DZBRIDGE
	friend class UnitTest_DzC4DDialog;
#endif
};
