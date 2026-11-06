"""Use user runtime code with development-only offline test fixtures."""
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'user_app/study/study-system'
PATHS = [ROOT/'user_app/vendor', RUNTIME, ROOT/'study/study-system/tests', ROOT/'study/study-system']
sys.path[:0] = [str(p) for p in PATHS]
sys.dont_write_bytecode = True
os.environ['PYTHONPATH'] = os.pathsep.join(str(p) for p in PATHS)
os.environ['PYTHONSAFEPATH'] = '1'
os.environ['TEMP'] = os.environ['TMP'] = str(ROOT/'study/study-system/output/test_tmp')

names = ['test_user_runtime_optimization', 'test_management.ManagerTests', 'test_notion_intake',
         'test_notion_prepared', 'test_scope_review.ScopeReviewTests',
         'test_status_intake_efficiency.StatusIntakeEfficiencyTests', 'test_organizer',
         'test_notion_reader', 'test_notion_front', 'test_notion_sync', 'test_notion_delta']
suite = unittest.defaultTestLoader.loadTestsFromNames(names)
path = ROOT/'output/user_runtime_review_20261022/regression.log'
with path.open('w', encoding='utf-8', buffering=1) as stream:
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
for name, module in list(sys.modules.items()):
    if name.split('.')[0] in ('analyzer', 'collector') and getattr(module, '__file__', None):
        assert Path(module.__file__).is_relative_to(RUNTIME), name
print(f'Tests: {result.testsRun}; failures: {len(result.failures)}; errors: {len(result.errors)}')
raise SystemExit(not result.wasSuccessful())
