"""Portable entry point; no installation or API calls during environment checks."""
import importlib.util
import sys
from pathlib import Path


def main():
    missing = [name for name in ('jsonschema', 'docx') if importlib.util.find_spec(name) is None]
    if missing:
        print('필수 Python 패키지가 없습니다: ' + ', '.join(missing))
        print('현재 Python: ' + sys.executable)
        print('설치 명령: "' + sys.executable + '" -m pip install -r "' + str(Path(__file__).with_name('requirements.txt')) + '"')
        return 2
    from analyzer.main import main as analyze_main
    return analyze_main()


if __name__ == '__main__':
    raise SystemExit(main())
