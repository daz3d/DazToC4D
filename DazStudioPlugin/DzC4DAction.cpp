#include <QtGui/qcheckbox.h>
#include <QtGui/QMessageBox>
#include <QtNetwork/qudpsocket.h>
#include <QtNetwork/qabstractsocket.h>
#include <QCryptographicHash>
#include <QtCore/qdir.h>

#include <dzapp.h>
#include <dzscene.h>
#include <dzmainwindow.h>
#include <dzshape.h>
#include <dzproperty.h>
#include <dzobject.h>
#include <dzpresentation.h>
#include <dznumericproperty.h>
#include <dzimageproperty.h>
#include <dzcolorproperty.h>
#include <dpcimages.h>

#include "QtCore/qmetaobject.h"
#include "dzmodifier.h"
#include "dzgeometry.h"
#include "dzweightmap.h"
#include "dzfacetshape.h"
#include "dzfacetmesh.h"
#include "dzfacegroup.h"
#include "dzprogress.h"
#include "dzscript.h"
#include "dzexportmgr.h"

#include "DzC4DAction.h"
#include "DzC4DDialog.h"
#include "DzBridgeMorphSelectionDialog.h"
#include "DzBridgeSubdivisionDialog.h"

#ifdef WIN32
#include <shellapi.h>
#endif

#include "dzbridge.h"

QString FindC4DPyExe(QString sC4DExecutablePath)
{
	if (sC4DExecutablePath.isEmpty()) return QString();

	if (QFileInfo(sC4DExecutablePath).exists() == false) return QString();

	if (sC4DExecutablePath.contains("c4dpy", Qt::CaseInsensitive)) return sC4DExecutablePath;

#ifdef WIN32
	QString sC4DPyExe = QString(sC4DExecutablePath).replace("Cinema 4D.exe", "c4dpy.exe", Qt::CaseInsensitive);
#elif defined(__APPLE__)
	QString sC4DPyExe = QString(sC4DExecutablePath).replace("Cinema 4D.app/Contents/MacOS/Cinema 4D", "c4dpy.app/Contents/MacOS/c4dpy", Qt::CaseInsensitive);
#endif

	if (QFileInfo(sC4DPyExe).exists() == false) return sC4DExecutablePath;

	return sC4DPyExe;
}

bool GenerateExporterBatchFile(QString batchFilePath, QString sExecutablePath, QString sCommandArgs, QString sCWD)
{
	QString sBatchFileFolder = QFileInfo(batchFilePath).dir().path().replace("\\", "/");
	QDir().mkdir(sBatchFileFolder);

	// 4. Generate manual batch file to launch exporter scripts

#ifdef WIN32
	QString sBatchString = QString("\
chcp 65001\n\n\
cd /d \"%1\"\n\n\
\"%2\"\
").arg(sCWD).arg(sExecutablePath);
#else defined(__APPLE__)
    QString sBatchString = QString("\
cd \"%1\"\n\n\
\"%2\"\
").arg(sCWD).arg(sExecutablePath);
#endif
	foreach(QString arg, sCommandArgs.split(";"))
	{
		if (arg.contains(" "))
		{
			sBatchString += QString(" \"%1\"").arg(arg);
		}
		else
		{
			sBatchString += " " + arg;
		}
	}
	// write batch
	QFile batchFileOut(batchFilePath);
	bool bResult = batchFileOut.open(QIODevice::WriteOnly | QIODevice::OpenModeFlag::Truncate);
	if (bResult) {
		batchFileOut.write(sBatchString.toUtf8().constData());
		batchFileOut.close();
	}
	else {
		dzApp->log("ERROR: GenerateExporterBatchFile(): Unable to open batch file for writing: " + batchFilePath);
	}

	return true;
}


DzError	DzC4DExporter::write(const QString& filename, const DzFileIOSettings* options)
{
	int eAssetType = DZ_BRIDGE_NAMESPACE::DzBridgeAction::SelectBestRootNodeForTransfer(false);
	QString sC4DOutputPath = QFileInfo(filename).dir().path().replace("\\", "/");

	DzProgress exportProgress(tr("Cinema 4D Exporter starting..."), 100, false, true);
	exportProgress.setInfo(QString("Exporting to:\n    \"%1\"\n").arg(filename));
	exportProgress.setInfo("Generating intermediate file");
	exportProgress.step(25);

	DzC4DAction* pC4DAction = new DzC4DAction();
	pC4DAction->m_pSelectedNode = dzScene->getPrimarySelection();
	pC4DAction->m_sOutputC4DFilepath = QString(filename).replace("\\", "/");
	pC4DAction->setNonInteractiveMode(DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode);
	pC4DAction->createUI();
	DzC4DDialog* pDialog = qobject_cast<DzC4DDialog*>(pC4DAction->getBridgeDialog());
	if (pDialog == NULL)
	{
		exportProgress.cancel();
		dzApp->log("Cinema 4D Exporter: CRITICAL ERROR: Unable to initialize DzC4DDialog. Aborting operation.");
		return DZ_OPERATION_FAILED_ERROR;
	}
	pDialog->setEAssetType(eAssetType);
	pDialog->requireC4DExecutableWidget(true);
	pC4DAction->executeAction();
	pDialog->requireC4DExecutableWidget(false);

	if (pDialog->result() == QDialog::Rejected) {
		exportProgress.cancel();
		return DZ_USER_CANCELLED_OPERATION;
	}

	DzError nExecuteActionResult = pC4DAction->getExecutActionResult();
	if (nExecuteActionResult != DZ_NO_ERROR) {
		exportProgress.cancel();
		return nExecuteActionResult;
	}

	//////////////////////////////////////////////////////////////////////////////////////////
	QString sIntermediatePath = QFileInfo(pC4DAction->m_sDestinationFBX).dir().path().replace("\\", "/");
	QString sIntermediateScriptsPath = sIntermediatePath + "/Scripts";
	QDir().mkdir(sIntermediateScriptsPath);

	QStringList aScriptFilelist = (QStringList() <<
		"create_c4d_file.py"
		);
	// copy 
	QString sEmbeddedFolderPath = ":/DazBridgeC4D";
	foreach(auto sScriptFilename, aScriptFilelist)
	{
		bool replace = true;
		QString sEmbeddedFilepath = sEmbeddedFolderPath + "/" + sScriptFilename;
		QFile srcFile(sEmbeddedFilepath);
		QString tempFilepath = sIntermediateScriptsPath + "/" + sScriptFilename;
		DZ_BRIDGE_NAMESPACE::DzBridgeAction::copyFile(&srcFile, &tempFilepath, replace);
		srcFile.close();
	}
	QString sBinariesFile = "/c4dplugin.zip";
	DZ_BRIDGE_NAMESPACE::DzBridgeAction::InstallEmbeddedArchive(sEmbeddedFolderPath + sBinariesFile, sIntermediateScriptsPath);

	exportProgress.setInfo("Generating C4D File");
	exportProgress.step(25);

	//////////////////////////////////////////////////////////////////////////////////////////

	//QString sCommandArgs = QString("%1;%2").arg(sScriptPath).arg(pC4DAction->m_sDestinationFBX);
#ifdef WIN32
	QString sC4DLogPath = QString(".") + "/" + "create_c4d_file.log";
	QString sScriptPath = QString("./Scripts") + "/" + "create_c4d_file.py";
#else defined(__APPLE__)
    QString sC4DLogPath = sIntermediatePath + "/" + "create_c4d_file.log";
    QString sScriptPath = sIntermediateScriptsPath + "/" + "create_c4d_file.py";
#endif
	QString sCommandArgs = QString("%1;%2").arg(sScriptPath).arg(pC4DAction->m_sDestinationFBX);
#ifdef WIN32
	QString batchFilePath = sIntermediatePath + "/" + "create_c4d_file.bat";
#else defined(__APPLE__)
	QString batchFilePath = sIntermediatePath + "/" + "create_c4d_file.sh";
#endif
	QString sC4DPyExecutable = FindC4DPyExe(pC4DAction->m_sC4DExecutablePath);
	if (sC4DPyExecutable.isEmpty() || sC4DPyExecutable == "")
	{
		QString sNoC4DPyExe = tr("Daz To Cinema 4D: CRITICAL ERROR: Unable to find a valid Cinema 4D Python executable. Aborting operation.");
		dzApp->log(sNoC4DPyExe);
		QMessageBox::critical(0, tr("No Cinema 4D Py Executable Found"),
			sNoC4DPyExe, QMessageBox::Abort);
		exportProgress.cancel();
		return DZ_OPERATION_FAILED_ERROR;
	}
	GenerateExporterBatchFile(batchFilePath, sC4DPyExecutable, sCommandArgs, sIntermediatePath);

	bool result = pC4DAction->executeC4DScripts(sC4DPyExecutable, sCommandArgs, 120);

	exportProgress.step(25);
	//////////////////////////////////////////////////////////////////////////////////////////

	if (result)
	{
		exportProgress.update(100);
		QMessageBox::information(0, tr("Cinema 4D Exporter"),
			tr("Export from Daz Studio complete."), QMessageBox::Ok);

#ifdef WIN32
//		ShellExecuteA(NULL, "open", sC4DOutputPath.toLocal8Bit().data(), NULL, NULL, SW_SHOWDEFAULT);
		std::wstring wcsC4DOutputPath(reinterpret_cast<const wchar_t*>(sC4DOutputPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsC4DOutputPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		if (QFileInfo(filename).exists()) {
			args << "select POSIX file \"" + filename + "\"";
		}
		else {
			args << "select POSIX file \"" + sC4DOutputPath + "/." + "\"";
		}
		args << "-e";
		args << "end tell";
		QProcess::startDetached("osascript", args);
#endif
	}
	else
	{
		QString sErrorString;
		sErrorString += QString("An error occured during the export process (ExitCode=%1).\n").arg(pC4DAction->m_nC4DExitCode);
		sErrorString += QString("Please check log files at : %1\n").arg(pC4DAction->m_sDestinationPath);
		QMessageBox::critical(0, "Cinema 4D Exporter", tr(sErrorString.toLocal8Bit()), QMessageBox::Ok);
#ifdef WIN32
//		ShellExecuteA(NULL, "open", pC4DAction->m_sDestinationPath.toLocal8Bit().data(), NULL, NULL, SW_SHOWDEFAULT);
		std::wstring wcsDestinationPath(reinterpret_cast<const wchar_t*>(pC4DAction->m_sDestinationPath.utf16()));
		ShellExecuteW(NULL, L"open", wcsDestinationPath.c_str(), NULL, NULL, SW_SHOWDEFAULT);
#elif defined(__APPLE__)
		QStringList args;
		args << "-e";
		args << "tell application \"Finder\"";
		args << "-e";
		args << "activate";
		args << "-e";
		args << "select POSIX file \"" + batchFilePath + "\"";
		args << "-e";
		args << "end tell";
		QProcess::startDetached("osascript", args);
#endif

		exportProgress.cancel();
		return DZ_OPERATION_FAILED_ERROR;
	}

	exportProgress.finish();
	return DZ_NO_ERROR;
};

DzC4DAction::DzC4DAction() :
	DzBridgeAction(tr("Send to &Cinema 4D..."), tr("Send the selected node to Cinema 4D."))
{
	this->setObjectName("DzBridge_DazToC4D_Action");

	m_nNonInteractiveMode = 0;
	m_sAssetType = QString("SkeletalMesh");
	//Setup Icon
	QString iconName = "Daz to Cinema 4D";
	QPixmap basePixmap = QPixmap::fromImage(getEmbeddedImage(iconName.toLatin1()));
	QIcon icon;
	icon.addPixmap(basePixmap, QIcon::Normal, QIcon::Off);
	QAction::setIcon(icon);

}

bool DzC4DAction::createUI()
{
	// Check if the main window has been created yet.
	// If it hasn't, alert the user and exit early.
	DzMainWindow* mw = dzApp->getInterface();
	if (!mw)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("The main window has not been created yet."), QMessageBox::Ok);

		return false;
	}

	// m_subdivisionDialog creation REQUIRES valid Character or Prop selected
	if (dzScene->getNumSelectedNodes() != 1)
	{
		if (m_nNonInteractiveMode == 0) QMessageBox::warning(0, tr("Error"),
			tr("Please select one Character or Prop to send."), QMessageBox::Ok);

		return false;
	}

	 // Create the dialog
	if (!m_bridgeDialog)
	{
		m_bridgeDialog = new DzC4DDialog(mw);
	}
	else
	{
		DzC4DDialog* c4dDialog = qobject_cast<DzC4DDialog*>(m_bridgeDialog);
		if (c4dDialog)
		{
			c4dDialog->resetToDefaults();
			c4dDialog->loadSavedSettings();
		}
	}

	if (!m_subdivisionDialog) m_subdivisionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeSubdivisionDialog::Get(m_bridgeDialog);
	if (!m_morphSelectionDialog) m_morphSelectionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeMorphSelectionDialog::Get(m_bridgeDialog);

	return true;
}

void DzC4DAction::executeAction()
{
	m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;

	// CreateUI() disabled for debugging -- 2022-Feb-25
	/*
		 // Create and show the dialog. If the user cancels, exit early,
		 // otherwise continue on and do the thing that required modal
		 // input from the user.
		 if (createUI() == false)
			 return;
	*/

	// Check if the main window has been created yet.
	// If it hasn't, alert the user and exit early.
	DzMainWindow* mw = dzApp->getInterface();
	if (!mw)
	{
		if (m_nNonInteractiveMode == 0)
		{
			QMessageBox::warning(0, tr("Error"),
				tr("The main window has not been created yet."), QMessageBox::Ok);
		}
		return;
	}

	if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode) {
		m_eSelectedNodeAssetType = SelectBestRootNodeForTransfer(true);
		m_pSelectedNode = dzScene->getPrimarySelection();
	}

	// Create the dialog
	if (m_bridgeDialog == nullptr)
	{
		m_bridgeDialog = new DzC4DDialog(mw);
	}
	else
	{
		if (m_nNonInteractiveMode == 0)
		{
			m_bridgeDialog->resetToDefaults();
			m_bridgeDialog->loadSavedSettings();
		}
	}

	// Prepare member variables when not using GUI
	if (isInteractiveMode() == false)
	{
//		if (m_sRootFolder != "") m_bridgeDialog->getIntermediateFolderEdit()->setText(m_sRootFolder);

		if (m_aMorphListOverride.isEmpty() == false)
		{
			m_bEnableMorphs = true;
			m_sMorphSelectionRule = m_aMorphListOverride.join("\n1\n");
			m_sMorphSelectionRule += "\n1\n.CTRLVS\n2\nAnything\n0";
			if (m_morphSelectionDialog == nullptr)
			{
				m_morphSelectionDialog = DZ_BRIDGE_NAMESPACE::DzBridgeMorphSelectionDialog::Get(m_bridgeDialog);
			}
			m_MorphNamesToExport.clear();
			foreach(QString morphName, m_aMorphListOverride)
			{
				QString label = m_morphSelectionDialog->GetMorphLabelFromName(morphName);
				m_MorphNamesToExport.append(morphName);
			}
		}
		else
		{
			m_bEnableMorphs = false;
			m_sMorphSelectionRule = "";
			m_MorphNamesToExport.clear();
		}

	}

	if (m_nNonInteractiveMode != DZ_BRIDGE_NAMESPACE::eNonInteractiveMode::DzExporterMode) {
		m_bridgeDialog->setEAssetType(m_eSelectedNodeAssetType);
	}

	// If the Accept button was pressed, start the export
	int dlgResult = -1;
	if (isInteractiveMode())
	{
		dlgResult = m_bridgeDialog->exec();
	}
	if (isInteractiveMode() == false || dlgResult == QDialog::Accepted)
	{
		// Read GUI values
		if (readGui(m_bridgeDialog) == false)
		{
			m_nExecuteActionResult = DZ_OPERATION_FAILED_ERROR;
			return;
		}

		// DB 2021-10-11: Progress Bar
		DzProgress* exportProgress = new DzProgress("Sending to Cinema 4D...", 10, false, true);

		DzError result = doPromptableObjectBaking();
		if (result != DZ_NO_ERROR) {
			exportProgress->finish();
			exportProgress->cancel();
			m_nExecuteActionResult = result;
			return;
		}
		exportProgress->step();


		//Create Daz3D folder if it doesn't exist
		QDir dir;
		dir.mkpath(m_sRootFolder);
		exportProgress->step();

		if (m_sAssetType == "Environment") {

			QDir().mkdir(m_sDestinationPath);
			m_pSelectedNode = dzScene->getPrimarySelection();

			auto objectList = dzScene->getNodeList();
			foreach(auto el, objectList) {
				DzNode* pNode = qobject_cast<DzNode*>(el);
				preProcessScene(pNode);
			}
			DzExportMgr* ExportManager = dzApp->getExportMgr();
			DzExporter* Exporter = ExportManager->findExporterByClassName("DzFbxExporter");
			DzFileIOSettings ExportOptions;
			ExportOptions.setBoolValue("IncludeSelectedOnly", false);
			ExportOptions.setBoolValue("IncludeVisibleOnly", true);
			ExportOptions.setBoolValue("IncludeFigures", true);
			ExportOptions.setBoolValue("IncludeProps", true);
			ExportOptions.setBoolValue("IncludeLights", false);
			ExportOptions.setBoolValue("IncludeCameras", false);
			ExportOptions.setBoolValue("IncludeAnimations", true);
			ExportOptions.setIntValue("RunSilent", !m_bShowFbxOptions);
			setExportOptions(ExportOptions);
			// NOTE: be careful to use m_sExportFbx and NOT m_sExportFilename since FBX and DTU base name may differ
			QString sEnvironmentFbx = m_sDestinationPath + m_sExportFbx + ".fbx";
			DzError result = Exporter->writeFile(sEnvironmentFbx, &ExportOptions);
			if (result != DZ_NO_ERROR) {
				undoPreProcessScene();
				m_nExecuteActionResult = result;
				exportProgress->finish();
				exportProgress->cancel();
				return;
			}
			exportProgress->step();

			writeConfiguration();
			exportProgress->step();

			undoPreProcessScene();
			exportProgress->step();

		}
		else
		{
			DzNode* pParentNode = NULL;
			if (m_pSelectedNode->isRootNode() == false) {
				dzApp->log("INFO: Selected Node for Export is not a Root Node, unparenting now....");
				pParentNode = m_pSelectedNode->getNodeParent();
				pParentNode->removeNodeChild(m_pSelectedNode, true);
				dzApp->log("INFO: Parent stored: " + pParentNode->getLabel() + ", New Root Node: " + m_pSelectedNode->getLabel());
			}
			exportProgress->step();
			exportHD(exportProgress);
			exportProgress->step();
			if (pParentNode) {
				dzApp->log("INFO: Restoring Parent relationship: " + pParentNode->getLabel() + ", child node: " + m_pSelectedNode->getLabel());
				pParentNode->addNodeChild(m_pSelectedNode, true);
			}
		}

		// DB 2021-10-11: Progress Bar
		exportProgress->finish();

		// DB 2021-09-02: messagebox "Export Complete"
		if (m_nNonInteractiveMode == 0)
		{
			QMessageBox::information(0, "Daz To Cinema 4D Bridge",
				tr("Export phase from Daz Studio complete. Please switch to Cinema 4D to begin Import phase."), QMessageBox::Ok);
		}

	}

	m_nExecuteActionResult = DZ_NO_ERROR;
}


void DzC4DAction::writeConfiguration()
{
	DzProgress* pDtuProgress = new DzProgress("Writing DTU file", 10, false, true);

	QString DTUfilename = m_sDestinationPath + m_sAssetName + ".dtu";
	QFile DTUfile(DTUfilename);
	DTUfile.open(QIODevice::WriteOnly);
	DzJsonWriter writer(&DTUfile);
	writer.startObject(true);

	writeDTUHeader(writer);
	pDtuProgress->step();

	// Plugin-specific items
	writer.addMember("Output C4D Filepath", m_sOutputC4DFilepath);
	pDtuProgress->step();

//	if (m_sAssetType.toLower().contains("mesh") || m_sAssetType == "Animation")
	if (true)
	{
		QTextStream *pCVSStream = nullptr;
		if (m_bExportMaterialPropertiesCSV)
		{
			QString filename = m_sDestinationPath + m_sAssetName + "_Maps.csv";
			QFile file(filename);
			file.open(QIODevice::WriteOnly);
			pCVSStream = new QTextStream(&file);
			*pCVSStream << "Version, Object, Material, Type, Color, Opacity, File" << endl;
		}
		pDtuProgress->update(6);
		if (m_sAssetType == "Environment") {
			writeSceneMaterials(writer, pCVSStream);
			pDtuProgress->step();
		}
		else {
			writeAllMaterials(m_pSelectedNode, writer, pCVSStream);
			pDtuProgress->step();
		}

		writeAllMorphs(writer);
		writeMorphLinks(writer);
		writeMorphNames(writer);
		pDtuProgress->step();

		DzBoneList aBoneList = getAllBones(m_pSelectedNode);

		writeSkeletonData(m_pSelectedNode, writer);
		writeHeadTailData(m_pSelectedNode, writer);
		writeJointOrientation(aBoneList, writer);
		writeLimitData(aBoneList, writer);
		writePoseData(m_pSelectedNode, writer, true);
		pDtuProgress->step();

		writeAllSubdivisions(writer);
		pDtuProgress->step();

		writeAllDforceInfo(m_pSelectedNode, writer);
		pDtuProgress->step();
	}

	writer.finishObject();
	DTUfile.close();

	pDtuProgress->finish();

}

// Setup custom FBX export options
void DzC4DAction::setExportOptions(DzFileIOSettings& ExportOptions)
{
	//ExportOptions.setBoolValue("doEmbed", false);
	//ExportOptions.setBoolValue("doDiffuseOpacity", false);
	//ExportOptions.setBoolValue("doCopyTextures", false);
	ExportOptions.setBoolValue("doFps", true);
	ExportOptions.setBoolValue("doLocks", false);
	ExportOptions.setBoolValue("doLimits", false);
	ExportOptions.setBoolValue("doBaseFigurePoseOnly", false);
	ExportOptions.setBoolValue("doHelperScriptScripts", false);
	ExportOptions.setBoolValue("doMentalRayMaterials", false);
}

QString DzC4DAction::readGuiRootFolder()
{
	QString rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + QDir::separator() + "DazToC4D";
#if __LEGACY_PATHS__
		rootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Cinema 4D/Exports/FIG/FIG0";
		rootFolder = rootFolder.replace("\\","/");
#else
	if (m_bridgeDialog)
	{
		QLineEdit* intermediateFolderEdit = nullptr;
		DzC4DDialog* c4dDialog = qobject_cast<DzC4DDialog*>(m_bridgeDialog);

		if (c4dDialog)
			intermediateFolderEdit = c4dDialog->getAssetsFolderEdit();

		if (intermediateFolderEdit)
			rootFolder = intermediateFolderEdit->text().replace("\\", "/") + "/Daz3D";
	}
#endif

	return rootFolder;
}

bool DzC4DAction::readGui(DZ_BRIDGE_NAMESPACE::DzBridgeDialog* BridgeDialog)
{
	bool bResult = DzBridgeAction::readGui(BridgeDialog);
	if (!bResult)
	{
		return false;
	}

#if __LEGACY_PATHS__
	if (m_sAssetType == "SkeletalMesh" || m_sAssetType == "Animation")
	{
		m_sRootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Cinema 4D/Exports/FIG";
		m_sRootFolder = m_sRootFolder.replace("\\", "/");
		m_sExportSubfolder = "FIG0";
		m_sExportFbx = "B_FIG";
		m_sAssetName = "FIG";
	}
	else
	{
		m_sRootFolder = QDesktopServices::storageLocation(QDesktopServices::DocumentsLocation) + "/DAZ 3D/Bridges/Daz To Cinema 4D/Exports/ENV";
		m_sRootFolder = m_sRootFolder.replace("\\", "/");
		m_sExportSubfolder = "ENV0";
		m_sExportFbx = "B_ENV";
		m_sAssetName = "ENV";
	}
	m_sDestinationPath = m_sRootFolder + "/" + m_sExportSubfolder + "/";
	m_sDestinationFBX = m_sDestinationPath + m_sExportFbx + ".fbx";
#endif

	// Read Custom GUI values
	DzC4DDialog* pC4DDialog = qobject_cast<DzC4DDialog*>(m_bridgeDialog);
	if (pC4DDialog) {

		if (m_sC4DExecutablePath == "" || isInteractiveMode()) m_sC4DExecutablePath = pC4DDialog->getC4DExecutablePath();

	}
	else {
		// Issue error, fail gracefully
		dzApp->log("Daz To Maya: ERROR: C4D Dialog was not initialized.  Cancelling operation...");
	}


	return true;
}

bool DzC4DAction::executeC4DScripts(QString sFilePath, QString sCommandlineArguments, float fTimeoutInSeconds)
{
	// fork or spawn child process
	QString sWorkingPath = m_sDestinationPath;
	QStringList args = sCommandlineArguments.split(";");

	//	float fTimeoutInSeconds = 2 * 60;
	float fMilliSecondsPerTick = 200;
	int numTotalTicks = fTimeoutInSeconds * 1000 / fMilliSecondsPerTick;
	DzProgress* progress = new DzProgress("Running Cinema 4D Script", numTotalTicks, false, true);
	progress->enable(true);
	QProcess* pToolProcess = new QProcess(this);
	pToolProcess->setWorkingDirectory(sWorkingPath);
	pToolProcess->start(sFilePath, args);
	int currentTick = 0;
	int timeoutTicks = numTotalTicks;
	bool bUserInitiatedTermination = false;
	while (pToolProcess->waitForFinished(fMilliSecondsPerTick) == false) {
		// if timeout reached, then terminate process
		if (currentTick++ > timeoutTicks) {
			if (!bUserInitiatedTermination)
			{
				QString sTimeoutText = tr("\
The current Cinema 4D operation is taking a long time.\n\
Do you want to Ignore this time-out and wait a little longer, or \n\
Do you want to Abort the operation now?");
				int result = QMessageBox::critical(0,
					tr("Daz To Maya: Maya Timout Error"),
					sTimeoutText,
					QMessageBox::Ignore,
					QMessageBox::Abort);
				if (result == QMessageBox::Ignore) {
					int snoozeTime = 60 * 1000 / fMilliSecondsPerTick;
					timeoutTicks += snoozeTime;
				}
				else {
					bUserInitiatedTermination = true;
				}
			}
			else
			{
				if (currentTick - timeoutTicks < 5) {
					pToolProcess->terminate();
				}
				else {
					pToolProcess->kill();
				}
			}
		}
		if (pToolProcess->state() == QProcess::Running) {
			progress->step();
		}
		else {
			break;
		}
	}
	progress->setCurrentInfo("Maya Script Completed.");
	progress->finish();
	delete progress;
	m_nC4DExitCode = pToolProcess->exitCode();
//#ifdef __APPLE__
//	if (m_nC4DExitCode != 0 && m_nC4DExitCode != 120)
#//else
	if (m_nC4DExitCode != 0)
		//#endif
	{
		//if (m_nMayaExitCode == m_nPythonExceptionExitCode) {
		//	dzApp->log(QString("Daz To Maya: ERROR: Python error:.... %1").arg(m_nMayaExitCode));
		//}
		//else {
		//	dzApp->log(QString("Daz To Maya: ERROR: exit code = %1").arg(m_nMayaExitCode));
		//}
		dzApp->log(QString("Daz To Maya: ERROR: exit code = %1").arg(m_nC4DExitCode));
		return false;
	}

	return true;
}


#include "moc_DzC4DAction.cpp"
