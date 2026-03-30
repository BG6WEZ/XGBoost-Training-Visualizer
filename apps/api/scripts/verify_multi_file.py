import httpx

r = httpx.get('http://localhost:8000/api/datasets/4616e4d8-24c7-4e6c-8f30-e5ee909f204b')
d = r.json()
print(f"名称: {d['name']}")
print(f"文件数: {len(d.get('files', []))}")
for f in d.get('files', []):
    print(f"  - {f['file_name']} ({f.get('role', 'unknown')})")
