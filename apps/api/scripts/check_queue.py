import httpx
from collections import Counter

r = httpx.get('http://localhost:8000/api/training/status')
print('队列状态:', r.json())

r = httpx.get('http://localhost:8000/api/experiments/')
experiments = r.json()
print(f'\n实验总数: {len(experiments)}')

statuses = Counter(e.get('status') for e in experiments)
print(f'状态分布: {dict(statuses)}')

queued_running = [e for e in experiments if e.get('status') in ['queued', 'running']]
print(f'\n排队/运行中的实验: {len(queued_running)}')
for e in queued_running[:5]:
    print(f"  - {e.get('id')}: {e.get('status')} - {e.get('name', 'N/A')}")
