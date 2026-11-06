"""User entry point. Uses only the adjacent application and libraries."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parent
RUNTIME = ROOT/'study/study-system'
if sys.version_info[:2] != (3, 14):
    raise SystemExit('이 사용자용 폴더는 Python 3.14가 필요합니다.')
sys.path[:0] = [str(ROOT/'vendor'), str(RUNTIME)]
os.environ['PYTHONPATH'] = os.pathsep.join([str(ROOT/'vendor'), str(RUNTIME)])
sys.dont_write_bytecode = True
os.chdir(RUNTIME)
if __name__ == '__main__':
    from analyzer.management import main
    main()
