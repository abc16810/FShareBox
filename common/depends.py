from datetime import datetime, timedelta

from fastapi import HTTPException, Request

from apps.models import Set_Pydantic, Settings


class IPRateLimit:
    def __init__(self, is_error):
        self.ips = {}
        self.is_error = is_error

    async def get_settings(self, request):
        if not await Settings.exists():
            raise HTTPException(detail="System Error", status_code=500)
        self.set = await Set_Pydantic.from_queryset_single(Settings.first())
        if self.is_error:
            self.count = self.set.error_count
            self.minutes = self.set.error_minute
        else:
            self.count = self.set.upload_count
            self.minutes = self.set.upload_minute

    def add_ip(self, ip):
        ip_info = self.ips.get(ip, {'count': 0, 'time': datetime.now()})
        ip_info['count'] += 1
        ip_info['time'] = datetime.now()
        self.ips[ip] = ip_info
        return ip_info['count']

    def check_ip(self, ip):
        # 检查ip是否被禁止
        if ip in self.ips:
            if self.ips[ip]['count'] >= self.count:
                # 是否超时
                if self.ips[ip]['time'] + timedelta(minutes=self.minutes) > datetime.now():
                    return False
                else:
                    self.ips.pop(ip)
        return True

    async def remove_expired_ip(self):
        for ip in list(self.ips.keys()):
            if self.ips[ip]['time'] + timedelta(minutes=self.minutes) < datetime.now():
                self.ips.pop(ip)

    async def __call__(self, request: Request):
        await self.get_settings(request)
        ip = request.headers.get(
            'X-Real-IP', request.headers.get('X-Forwarded-For', request.client.host))
        if not self.check_ip(ip):
            raise HTTPException(status_code=400, detail=f"请求次数过多，请稍后再试")
        return (ip, self.set)
