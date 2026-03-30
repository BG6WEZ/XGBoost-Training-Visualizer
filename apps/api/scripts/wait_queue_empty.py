import httpx
import time

for i in range(30):
    r = httpx.get('http://localhost:8000/api/training/status')
    data = r.json()
    queue_length = data.get('queue_length', 0)
    active = data.get('active_experiments', 0)
    print(f'队列长度: {queue_length}, 活跃实验: {active}')
    
    if queue_length == 0 and active == 0:
        print('队列已清空!')
        break
    time.sleep(5)
else:
    print('等待超时')
