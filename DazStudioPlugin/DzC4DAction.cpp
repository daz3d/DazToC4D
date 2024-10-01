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

DzError	DzC4DExporter::write(const QString& filename, const DzFileIOSettings* options)
{
	bool bDefaultToEnvironment = false;
	if (DZ_BRIDGE_NAMESPACE::DzBridgeAction::SelectBestRootNodeForTransfer() == DZ_BRIDGE_NAMESPACE::EAssetType::Other) {
		bDefaultToEnvironment = true;
	}
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

	QString scriptContents = "\
var action = new DzC4DAction;\
action.executeAction();";
	DzScript oScript;
	oScript.addCode(scriptContents);
	oScript.execute();

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
	m_eSelectedNodeAssetType = DZ_BRIDGE_NAMESPACE::EAssetType::None;

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

	m_bridgeDialog->setEAssetType(m_eSelectedNodeAssetType);

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
		//
	}
	else {
		// Issue error, fail gracefully
		dzApp->log("Daz To Maya: ERROR: C4D Dialog was not initialized.  Cancelling operation...");
	}


	return true;
}


#include "moc_DzC4DAction.cpp"
