#ifdef UNITTEST_DZBRIDGE

#include "UnitTest_DzC4DAction.h"
#include "DzC4DAction.h"


UnitTest_DzC4DAction::UnitTest_DzC4DAction()
{
	m_testObject = (QObject*) new DzC4DAction();
}

bool UnitTest_DzC4DAction::runUnitTests()
{
	RUNTEST(_DzBridgeC4DAction);
	RUNTEST(executeAction);
	RUNTEST(createUI);
	RUNTEST(writeConfiguration);
	RUNTEST(setExportOptions);
	RUNTEST(readGuiRootFolder);

	return true;
}

bool UnitTest_DzC4DAction::_DzBridgeC4DAction(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(new DzC4DAction());
	return bResult;
}

bool UnitTest_DzC4DAction::executeAction(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DAction*>(m_testObject)->executeAction());
	return bResult;
}

bool UnitTest_DzC4DAction::createUI(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DAction*>(m_testObject)->createUI());
	return bResult;
}

bool UnitTest_DzC4DAction::writeConfiguration(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DAction*>(m_testObject)->writeConfiguration());
	return bResult;
}

bool UnitTest_DzC4DAction::setExportOptions(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	DzFileIOSettings arg;
	TRY_METHODCALL(qobject_cast<DzC4DAction*>(m_testObject)->setExportOptions(arg));
	return bResult;
}

bool UnitTest_DzC4DAction::readGuiRootFolder(UnitTest::TestResult* testResult)
{
	bool bResult = true;
	TRY_METHODCALL(qobject_cast<DzC4DAction*>(m_testObject)->readGuiRootFolder());
	return bResult;
}


#include "moc_UnitTest_DzC4DAction.cpp"

#endif
