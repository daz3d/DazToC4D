#pragma once
#ifdef UNITTEST_DZBRIDGE

#include <QObject>
#include <UnitTest.h>

class UnitTest_DzC4DAction : public UnitTest {
	Q_OBJECT
public:
	UnitTest_DzC4DAction();
	bool runUnitTests();

private:
	bool _DzBridgeC4DAction(UnitTest::TestResult* testResult);
	bool executeAction(UnitTest::TestResult* testResult);
	bool createUI(UnitTest::TestResult* testResult);
	bool writeConfiguration(UnitTest::TestResult* testResult);
	bool setExportOptions(UnitTest::TestResult* testResult);
	bool readGuiRootFolder(UnitTest::TestResult* testResult);

};

#endif
