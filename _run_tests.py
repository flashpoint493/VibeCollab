import subprocess, os, sys

skip = {'test_generator.py','test_pattern_engine.py','test_cli_guide.py',
        'test_cli_lifecycle.py','test_protocol_checker.py','test_cli_ai.py'}
fs = sorted(f for f in os.listdir('tests') 
            if f.startswith('test_') and f.endswith('.py') and f not in skip)

for f in fs:
    try:
        p = subprocess.run(
            [sys.executable, '-m', 'pytest', f'tests/{f}', '-x', '--tb=line', '-q'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=60
        )
        last = p.stdout.strip().split('\n')[-1] if p.stdout.strip() else 'NO OUTPUT'
        if p.returncode != 0:
            print(f'FAIL {f}: {last}')
            # print first failure line
            for line in p.stdout.split('\n'):
                if 'FAILED' in line:
                    print(f'  {line.strip()}')
        else:
            print(f'OK   {f}: {last}')
    except subprocess.TimeoutExpired:
        print(f'TIMEOUT {f}')
