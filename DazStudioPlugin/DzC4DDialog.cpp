#include <QtGui/QLayout>
#include <QtGui/QLabel>
#include <QtGui/QGroupBox>
#include <QtGui/QPushButton>
#include <QtGui/QMessageBox>
#include <QtGui/QToolTip>
#include <QtGui/QWhatsThis>
#include <QtGui/qlineedit.h>
#include <QtGui/qboxlayout.h>
#include <QtGui/qfiledialog.h>
#include <QtCore/qsettings.h>
#include <QtGui/qformlayout.h>
#include <QtGui/qcombobox.h>
#include <QtGui/qdesktopservices.h>
#include <QtGui/qcheckbox.h>
#include <QtGui/qlistwidget.h>
#include <QtGui/qgroupbox.h>

#include "dzapp.h"
#include "dzscene.h"
#include "dzstyle.h"
#include "dzmainwindow.h"
#include "dzactionmgr.h"
#include "dzaction.h"
#include "dzskeleton.h"
#include "qstandarditemmodel.h"

#include "DzC4DDialog.h"
#include "DzBridgeMorphSelectionDialog.h"
#include "DzBridgeSubdivisionDialog.h"

#include "version.h"

/*****************************
Local definitions
*****************************/
#define DAZ_BRIDGE_PLUGIN_NAME "Daz To Cinema 4D"

#include "dzbridge.h"

DzC4DDialog::DzC4DDialog(QWidget* parent) :
	 DzBridgeDialog(parent, DAZ_BRIDGE_PLUGIN_NAME)
{
	this->setObjectName("DzBridge_DazToC4D_Dialog");

	 intermediateFolderEdit = nullptr;
	 intermediateFolderButton = nullptr;

	 settings = new QSettings("Daz 3D", "DazToC4D");

	 // Declarations
	 int margin = style()->pixelMetric(DZ_PM_GeneralMargin);
	 int wgtHeight = style()->pixelMetric(DZ_PM_ButtonHeight);
	 int btnMinWidth = style()->pixelMetric(DZ_PM_ButtonMinWidth);

	 // Set the dialog title
	 int revision = PLUGIN_REV % 1000;
#ifdef _DEBUG
	 setWindowTitle(tr("Daz To Cinema 4D Bridge %1 v%2.%3.%4 PreRelease Build").arg(PLUGIN_MAJOR).arg(PLUGIN_MINOR).arg(revision).arg(PLUGIN_BUILD));
#else
	 setWindowTitle(tr("Daz To Cinema 4D Bridge %1 v%2.%3").arg(PLUGIN_MAJOR).arg(PLUGIN_MINOR).arg(revision));
#endif

	 // Welcome String for Setup/Welcome Mode
	 QString sDazAppDir = dzApp->getHomePath().replace("\\","/");
	 QString sPdfPath = sDazAppDir + "/docs/Plugins" + "/Daz to Cinema 4D/Daz to Cinema 4D.pdf";
	 QString sSetupModeString = tr("<h4>\
<div style=\"background-color:#282f41;\" align=center>\
<img src=\":/DazBridgeC4D/banner.jpg\" width=\"370\" height=\"95\" align=\"center\" hspace=\"0\" vspace=\"0\">\
<table width=100% cellpadding=8 cellspacing=2 style=\"vertical-align:middle; font-size:x-large; font-weight:bold; background-color:#FFAA00;foreground-color:#FFFFFF\" align=center>\
  <tr>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"https://www.daz3d.com/cinema-4d-bridge#faq\">FAQ</a></div></td>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"https://youtu.be/nAPj5_GDeyQ\">Installation Video</a></td>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"https://youtu.be/aXYEleSQrzY\">Tutorial Video</a></td>\
  </tr>\
  <tr>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"file:///") + sPdfPath + tr("\">PDF</a></td>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"https://www.daz3d.com/forums/categories/cinema-4d-discussion\">Forums</a></td>\
    <td width=33% style=\"text-align:center; background-color:#282f41;\"><div align=center><a href=\"https://github.com/daz3d/DazToC4D/issues\">Report Bug</a></td>\
  </tr>\
</table>\
</div>\
");
	 m_WelcomeLabel->setText(sSetupModeString);
	 QString sBridgeVersionString = tr("Daz To Cinema 4D Bridge %1 v%2.%3.%4").arg(PLUGIN_MAJOR).arg(PLUGIN_MINOR).arg(revision).arg(PLUGIN_BUILD);
	 setBridgeVersionStringAndLabel(sBridgeVersionString);

	 // Disable Unsupported AssetType ComboBox Options
	 QStandardItemModel* model = qobject_cast<QStandardItemModel*>(assetTypeCombo->model());
	 QStandardItem* item = nullptr;
//	 item = model->findItems("Environment").first();
//	 if (item) item->setFlags(item->flags() & ~Qt::ItemIsEnabled);
	 item = model->findItems("Pose").first();
	 if (item) item->setFlags(item->flags() & ~Qt::ItemIsEnabled);

	 // Connect new asset type handler
	 connect(assetTypeCombo, SIGNAL(activated(int)), this, SLOT(HandleAssetTypeComboChange(int)));

	 m_wC4DExecutablePathEdit = new QLineEdit(this);
//	 m_wC4DExecutablePathEdit->setValidator(&m_dzValidatorFileExists);
	 m_wC4DExecutablePathButton = new DzBridgeBrowseButton(this);
	 m_wC4DExecutablePathLayout = new QHBoxLayout();
	 m_wC4DExecutablePathLayout->setSpacing(0);
	 m_wC4DExecutablePathLayout->addWidget(m_wC4DExecutablePathEdit);
	 m_wC4DExecutablePathLayout->addWidget(m_wC4DExecutablePathButton);
	 connect(m_wC4DExecutablePathButton, SIGNAL(released()), this, SLOT(HandleSelectC4DExecutablePathButton()));
	 connect(m_wC4DExecutablePathEdit, SIGNAL(textChanged(const QString&)), this, SLOT(HandleTextChanged(const QString&)));

	 m_wC4DExecutableRowLabel = new QLabel(tr("Cinema 4D Executable"));
	 advancedLayout->insertRow(0, m_wC4DExecutableRowLabel, m_wC4DExecutablePathLayout);
	 m_aRowLabels.append(m_wC4DExecutableRowLabel);

	 // Intermediate Folder
	 QHBoxLayout* intermediateFolderLayout = new QHBoxLayout();
	 intermediateFolderEdit = new QLineEdit(this);
	 intermediateFolderButton = new QPushButton("...", this);
	 intermediateFolderLayout->addWidget(intermediateFolderEdit);
	 intermediateFolderLayout->addWidget(intermediateFolderButton);
	 connect(intermediateFolderButton, SIGNAL(released()), this, SLOT(HandleSelectIntermediateFolderButton()));

	 // Advanced Options
#if __LEGACY_PATHS__
	 intermediateFolderEdit->setVisible(false);
	 intermediateFolderButton->setVisible(false);
#else
	 if (advancedLayout)
	 {
		 QLabel* wIntermediateFolderRowLabel = new QLabel(tr("Intermediate Folder"));
		 advancedLayout->addRow(wIntermediateFolderRowLabel, intermediateFolderLayout);
		 m_aRowLabels.append(wIntermediateFolderRowLabel);
	 }
#endif

	 if (advancedLayout)
	 {
		 // reposition the Open Intermediate Folder button so it aligns with the center section
		 advancedLayout->removeWidget(m_OpenIntermediateFolderButton);
		 advancedLayout->addRow("", m_OpenIntermediateFolderButton);
	 }

	 // Configure Target Plugin Installer
	 renameTargetPluginInstaller("Cinema 4D Plugin Installer");
	 m_TargetSoftwareVersionCombo->setVisible(false);
	 //m_TargetSoftwareVersionCombo->clear();
	 //m_TargetSoftwareVersionCombo->addItem("Select Cinema 4D Version");
	 //m_TargetSoftwareVersionCombo->addItem("Cinema 4D R23");
	 //m_TargetSoftwareVersionCombo->addItem("Cinema 4D R24");
	 //m_TargetSoftwareVersionCombo->addItem("Cinema 4D R25");
	 showTargetPluginInstaller(true);

	 // Make the dialog fit its contents, with a minimum width, and lock it down
	 resize(QSize(500, 0).expandedTo(minimumSizeHint()));
	 setFixedWidth(width());
	 setFixedHeight(height());

	 update();

	 // Help
	 assetNameEdit->setWhatsThis("This is the name the asset will use in C4D.");
	 assetTypeCombo->setWhatsThis("Skeletal Mesh for something with moving parts, like a character\nStatic Mesh for things like props\nAnimation for a character animation.");
	 intermediateFolderEdit->setWhatsThis("Daz to C4D will collect the assets in a subfolder under this folder.  Cinema 4D will import them from here.");
	 intermediateFolderButton->setWhatsThis("Daz to C4D will collect the assets in a subfolder under this folder.  Cinema 4D will import them from here.");
	 m_wTargetPluginInstaller->setWhatsThis("You can install the Cinema 4D Plugin by selecting the desired Cinema 4D version and then clicking Install.");
    
	 // Set Defaults
	 resetToDefaults();

	 // Load Settings
	 loadSavedSettings();

	 // Daz Ultra
	 m_WelcomeLabel->hide();
	 setWindowTitle(tr("Cinema 4D Export Options"));
	 wHelpMenuButton->show();

	 fixRowLabelStyle();
	 fixRowLabelWidths();

}

bool DzC4DDialog::loadSavedSettings()
{
	DzBridgeDialog::loadSavedSettings();

	if (!settings->value("IntermediatePath").isNull())
	{
		QString directoryName = settings->value("IntermediatePath").toString();
		intermediateFolderEdit->setText(directoryName);
	}
	else
	{
		QString DefaultPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToC4D";
		intermediateFolderEdit->setText(DefaultPath);
	}
	if (!settings->value("C4DExecutablePath").isNull())
	{
		m_wC4DExecutablePathEdit->setText(settings->value("C4DExecutablePath").toString());
	}

	return true;
}

void DzC4DDialog::saveSettings()
{
	if (settings == nullptr || m_bDontSaveSettings) return;

	DzBridgeDialog::saveSettings();

	// Intermediate Path
	QString sIntermdiateFolderpath = intermediateFolderEdit->text();
	if (sIntermdiateFolderpath == "") {
		// reset to default
		QString DefaultPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToC4D";
		sIntermdiateFolderpath = DefaultPath;
	}
	settings->setValue("IntermediatePath", sIntermdiateFolderpath);

	// C4D Executable Path
	settings->setValue("C4DExecutablePath", m_wC4DExecutablePathEdit->text());

}

void DzC4DDialog::accept()
{
	if (m_bSetupMode) {
		saveSettings();
		return DzBasicDialog::reject();
	}

	bool bResult = HandleAcceptButtonValidationFeedback();
	if (bResult == true)
	{
		saveSettings();
		return DzBasicDialog::accept();
	}

}

bool DzC4DDialog::HandleAcceptButtonValidationFeedback()
{
	// Check if Intermedia Folder and Blender Executable are valid, if not issue Error and fail gracefully
	if (
		(m_bC4DRequired) &&
		(m_wC4DExecutablePathEdit->text() == "" || isC4DTextBoxValid() == false)
		)
	{
		QMessageBox::warning(0, tr("Cinema 4D Executable Path"), tr("Cinema 4D Executable Path must be set."), QMessageBox::Ok);
		return false;
	}
	else if (assetTypeCombo->itemData(assetTypeCombo->currentIndex()).toString() == "__")
	{
		QMessageBox::warning(0, tr("Select Asset Type"), tr("Please select an asset type from the dropdown menu."), QMessageBox::Ok);
		return false;
	}

	return true;
}

void DzC4DDialog::resetToDefaults()
{
	m_bDontSaveSettings = true;
	DzBridgeDialog::resetToDefaults();

	QString DefaultPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToC4D";
	intermediateFolderEdit->setText(DefaultPath);

	DzNode* Selection = dzScene->getPrimarySelection();
	if (dzScene->getFilename().length() > 0)
	{
		QFileInfo fileInfo = QFileInfo(dzScene->getFilename());
		assetNameEdit->setText(fileInfo.baseName().remove(QRegExp("[^A-Za-z0-9_]")));
	}
	else if (dzScene->getPrimarySelection())
	{
		assetNameEdit->setText(Selection->getLabel().remove(QRegExp("[^A-Za-z0-9_]")));
	}

	if (qobject_cast<DzSkeleton*>(Selection))
	{
		assetTypeCombo->setCurrentIndex(0);
	}
	else
	{
		assetTypeCombo->setCurrentIndex(1);
	}
	m_bDontSaveSettings = false;
}

void DzC4DDialog::HandleSelectIntermediateFolderButton()
{
	 // DB (2021-05-15): prepopulate with existing folder string
	 QString directoryName = "/home";
	 if (settings != nullptr && settings->value("IntermediatePath").isNull() != true)
	 {
		 directoryName = settings->value("IntermediatePath").toString();
	 }
	 directoryName = QFileDialog::getExistingDirectory(this, tr("Choose Directory"),
		  directoryName,
		  QFileDialog::ShowDirsOnly
		  | QFileDialog::DontResolveSymlinks);

	 if (directoryName != NULL)
	 {
		 intermediateFolderEdit->setText(directoryName);
		 if (settings != nullptr)
		 {
			 settings->setValue("IntermediatePath", directoryName);
		 }
	 }
}

void DzC4DDialog::HandleAssetTypeComboChange(int state)
{
	QString assetNameString = assetNameEdit->text();

	// enable/disable Morphs and Subdivision only if Skeletal selected
	if (assetTypeCombo->currentText() != "Skeletal Mesh")
	{
		morphsEnabledCheckBox->setChecked(false);
		subdivisionEnabledCheckBox->setChecked(false);
	}

	// if "Animation", change assetname
	if (assetTypeCombo->currentText() == "Animation")
	{
		// check assetname is in @anim[0000] format
		if (!assetNameString.contains("@") || assetNameString.contains(QRegExp("@anim[0-9]*")))
		{
			// extract true assetName and recompose animString
			assetNameString = assetNameString.left(assetNameString.indexOf("@"));
			// get importfolder using corrected assetNameString
			QString importFolderPath = settings->value("AssetsPath").toString() + QDir::separator() + "Daz3D" + QDir::separator() + assetNameString + QDir::separator();

			// create anim filepath
			uint animCounter = 0;
			QString animString = assetNameString + QString("@anim%1").arg(animCounter, 4, 10, QChar('0'));
			QString filePath = importFolderPath + animString + ".fbx";

			// if anim file exists, then increment anim filename counter
			while (QFileInfo(filePath).exists())
			{
				if (++animCounter > 9999)
				{
					break;
				}
				animString = assetNameString + QString("@anim%1").arg(animCounter, 4, 10, QChar('0'));
				filePath = importFolderPath + animString + ".fbx";
			}
			assetNameEdit->setText(animString);
		}

	}
	else
	{
		// remove @anim if present
		if (assetNameString.contains("@")) {
			assetNameString = assetNameString.left(assetNameString.indexOf("@"));
		}
		assetNameEdit->setText(assetNameString);
	}

}

#include <QProcessEnvironment>

void DzC4DDialog::HandleTargetPluginInstallerButton()
{
	// Get Software Versio
	DzBridgeDialog::m_sEmbeddedFilesPath = ":/DazBridgeC4D";
	QString sBinariesFile = "/c4dplugin.zip";
	QString sDestinationPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/cinema4d/plugins";
	if (QDir(sDestinationPath).exists() == false)
	{
		sDestinationPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/cinema4d";
	}
	if (QDir(sDestinationPath).exists() == false)
	{
		sDestinationPath = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation);
	}
	QString softwareVersion = m_TargetSoftwareVersionCombo->currentText();

	//if (softwareVersion.contains("..."))
	//{
	//	sDestinationPath += "...";
	//}
	//else
	//{
	//	// Warning, not a valid plugins folder path
	//	QMessageBox::information(0, "DazToC4D Bridge",
	//		tr("Please select a Cinema 4D version."));
	//	return;
	//}

	// Get Destination Folder
	sDestinationPath = QFileDialog::getExistingDirectory(this,
		tr("Choose a Cinema 4D Plugins Folder"),
		sDestinationPath,
		QFileDialog::ShowDirsOnly
		| QFileDialog::DontResolveSymlinks);

	if (sDestinationPath == NULL)
	{
		// User hit cancel: return without addition popups
		return;
	}

	// fix path separators
	sDestinationPath = sDestinationPath.replace("\\", "/");

	// verify plugin path
	bool bIsPluginPath = false;
	QString sPluginsPath = sDestinationPath;
	//if (sPluginsPath.endsWith("/plugins", Qt::CaseInsensitive) == false)
	//{
	//	sPluginsPath += "/plugins";
	//}
	if (QDir(sPluginsPath).exists())
	{
		bIsPluginPath = true;
	}

	if (bIsPluginPath == false)
	{
		// Warning, not a valid plugins folder path
		auto userChoice = QMessageBox::warning(0, "Daz To Cinema 4D",
			tr("The selected folder may not be a valid Cinema4D Plugins folder.  Please select a \
Plugins folder to install the plugin.\n\nYou can choose to Abort and select a new folder, \
or Ignore this warning and install the plugin anyway."),
QMessageBox::Ignore | QMessageBox::Abort,
QMessageBox::Abort);
		if (userChoice == QMessageBox::StandardButton::Abort)
			return;

	}

	// create plugins folder if does not exist
	if (QDir(sPluginsPath).exists() == false)
	{
		if (QDir().mkpath(sPluginsPath) == false)
		{
			QMessageBox::warning(0, "Daz To Cinema 4D",
				tr("Sorry, an error occured while trying to create the Plugins \
path:\n\n") + sPluginsPath + tr("\n\nPlease make sure you have write permissions to \
modify the parent folder."));
			return;
		}
	}

	bool bInstallSuccessful = false;
	bInstallSuccessful = installEmbeddedArchive(sBinariesFile, sPluginsPath);

	if (bInstallSuccessful)
	{
		QMessageBox::information(0, "Daz To Cinema 4D",
			tr("Cinema 4D Plugin successfully installed to:\n\n") + sPluginsPath +
			tr("\n\nIf Cinema 4D is running, please quit and restart Cinema 4D to continue \
Bridge Export process."));
	}
	else
	{
		QMessageBox::warning(0, "Daz To Cinema 4D",
			tr("Sorry, an unknown error occured. Unable to install Cinema 4D \
Plugin to:\n\n") + sPluginsPath + tr("\n\nPlease make sure you have write permissions to \
modify the selected folder."));
		return;
	}

	return;
}

void DzC4DDialog::HandleOpenIntermediateFolderButton(QString sFolderPath)
{
	QString sIntermediateFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToC4D";
#if __LEGACY_PATHS__
	sIntermediateFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Cinema 4D/Exports";
	if (QFile(sIntermediateFolder).exists() == false)
	{
		QDir().mkpath(sIntermediateFolder);
	}
#else
	if (intermediateFolderEdit != nullptr)
	{
		sIntermediateFolder = intermediateFolderEdit->text();
	}
#endif
	sIntermediateFolder = sIntermediateFolder.replace("\\", "/");
	DzBridgeDialog::HandleOpenIntermediateFolderButton(sIntermediateFolder);
}

#include <QUrl>
void DzC4DDialog::HandlePdfButton()
{
	QString sDazAppDir = dzApp->getHomePath().replace("\\", "/");
	QString sPdfPath = sDazAppDir + "/docs/Plugins" + "/Daz to Cinema 4D/Daz to Cinema 4D.pdf";
	QDesktopServices::openUrl(QUrl(sPdfPath));
}

void DzC4DDialog::HandleYoutubeButton()
{
	QString url = "https://youtu.be/aXYEleSQrzY";
	QDesktopServices::openUrl(QUrl(url));
}

void DzC4DDialog::HandleSupportButton()
{
	QString url = "https://bugs.daz3d.com/hc/en-us/requests/new";
	QDesktopServices::openUrl(QUrl(url));
}

void DzC4DDialog::HandleSelectC4DExecutablePathButton()
{
	QString directoryName = "";
	QString sMayaExePath = m_wC4DExecutablePathEdit->text();
	directoryName = QFileInfo(sMayaExePath).dir().path();
	if (directoryName == "." || directoryName == "") {
		if (settings != nullptr && settings->value("C4DExecutablePath").isNull() != true) {
			sMayaExePath = settings->value("C4DExecutablePath").toString();
			directoryName = QFileInfo(sMayaExePath).dir().path();
		}
		if (directoryName == "." || directoryName == "") {
			// DEFAULT APPLICATION PATH
#ifdef WIN32
			directoryName = "C:/Program Files/";
#elif defined (__APPLE__)
			directoryName = "/Applications/";
#endif
		}
	}
#ifdef WIN32
	QString sExeFilter = tr("Executable Files (*.exe)");
#elif defined(__APPLE__)
	QString sExeFilter = tr("Application Bundle (*.app)");
#endif
	QString fileName = QFileDialog::getOpenFileName(this,
		tr("Select Maya Executable"),
		directoryName,
		sExeFilter,
		&sExeFilter,
		QFileDialog::ReadOnly |
		QFileDialog::DontResolveSymlinks);

#if defined(__APPLE__)
	if (fileName != "")
	{
		fileName = fileName + "/Contents/MacOS/Cinema 4D";
	}
#endif

	if (fileName != "")
	{
		m_wC4DExecutablePathEdit->setText(fileName);
		if (settings != nullptr)
		{
			settings->setValue("C4DExecutablePath", fileName);
		}
	}

}

bool DzC4DDialog::isC4DTextBoxValid(const QString& text)
{
	QString temp_text(text);

	if (temp_text == "") {
		// check widget text
		temp_text = m_wC4DExecutablePathEdit->text();
	}

	// validate c4d executable
	QFileInfo fi(temp_text);
	if (fi.exists() == false) {
		dzApp->log("DzBridge: isC4DTextBoxValid: DEBUG: file does not exist: " + temp_text);
		return false;
	}

	return true;
}

bool DzC4DDialog::disableAcceptUntilAllRequirementsValid()
{
	if (!isC4DTextBoxValid() && m_bC4DRequired)
	{
		this->setAcceptButtonText("Unable to Proceed");
		return false;
	}
	this->setAcceptButtonText("Accept");
	return true;
}


void DzC4DDialog::HandleTextChanged(const QString& text)
{
	QObject* senderWidget = sender();
	if (senderWidget == m_wC4DExecutablePathEdit) {
		updateC4DExecutablePathEdit(isC4DTextBoxValid());
	}
	disableAcceptUntilAllRequirementsValid();
}

void DzC4DDialog::updateC4DExecutablePathEdit(bool isValid)
{
	if (!isValid && m_bC4DRequired) {
		m_wC4DExecutablePathButton->setHighlightStyle(true);
	}
	else {
		m_wC4DExecutablePathButton->setHighlightStyle(false);
	}
}

void DzC4DDialog::requireC4DExecutableWidget(bool bRequired)
{
	m_bC4DRequired = bRequired;

	if (bRequired) {
		// move GUI
		advancedLayout->removeItem(m_wC4DExecutablePathLayout);
		mainLayout->insertRow(0, m_wC4DExecutableRowLabel, m_wC4DExecutablePathLayout);
//		m_wMC4DileExportOptionsGroupBox->setVisible(true);
	}
	else {
		mainLayout->removeItem(m_wC4DExecutablePathLayout);
		advancedLayout->insertRow(0, m_wC4DExecutableRowLabel, m_wC4DExecutablePathLayout);
//		m_wC4DFileExportOptionsGroupBox->setVisible(false);
	}
	updateC4DExecutablePathEdit(isC4DTextBoxValid());

}



#include "moc_DzC4DDialog.cpp"
