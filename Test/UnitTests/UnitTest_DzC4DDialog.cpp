#ifdef UNITTEST_DZBRIDGE

#include "UnitTest_DzC4DDialog.h"
#include "DzC4DDialog.h"


UnitTest_DzC4DDialog::UnitTest_DzC4DDialog()
{
	m_testObject = (QObject*) new DzC4DDialog();
}

bool UnitTest_DzC4DDialog::runUnitTests()
{
	RUNTEST(_DzBridgeC4DDialog);
	RUNTEST(getIntermediateFolderEdit);
	RUNTEST(resetToDefaults);
	RUNTEST(loadSavedSettings);
	RUNTEST(HandleSelectIntermediateFolderButton);
	RUNTEST(HandleAssetTypeComboChange);

	return true;
}

bool UnitTest_DzC4DDialog::_DzBridgeC4DDialog(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(new DzC4DDialog());
	return bResult;
}

bool UnitTest_DzC4DDialog::getIntermediateFolderEdit(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DDialog*>(m_testObject)->getIntermediateFolderEdit());
	return bResult;
}

bool UnitTest_DzC4DDialog::resetToDefaults(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DDialog*>(m_testObject)->resetToDefaults());
	return bResult;
}

bool UnitTest_DzC4DDialog::loadSavedSettings(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DDialog*>(m_testObject)->loadSavedSettings());
	return bResult;
}

bool UnitTest_DzC4DDialog::HandleSelectIntermediateFolderButton(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DDialog*>(m_testObject)->HandleSelectIntermediateFolderButton());
	return bResult;
}

bool UnitTest_DzC4DDialog::HandleAssetTypeComboChange(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DDialog*>(m_testObject)->HandleAssetTypeComboChange(0));
	return bResult;
}


#include "moc_UnitTest_DzC4DDialog.cpp"
#endif
