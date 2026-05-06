"""
Billing Service
计费服务 - 免费次数管理、付费逻辑
"""
import os
import json
import time
from typing import Optional, Dict
from datetime import datetime, timedelta
from app.models.schemas import BillingStatus, NamingType


# 简单的内存存储（生产环境应使用数据库）
class BillingStore:
    """计费存储（内存版，生产环境请使用Redis/数据库）"""
    
    def __init__(self):
        self._data: Dict[str, Dict] = {}
        self._lock_file = ".billing.lock"  # 简单的文件锁
    
    def _get_file_path(self, user_id: str) -> str:
        return f".billing_{user_id}.json"
    
    def get(self, user_id: str) -> Dict:
        """获取用户计费信息"""
        if user_id in self._data:
            return self._data[user_id]
        
        file_path = self._get_file_path(user_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._data[user_id] = data
                    return data
            except Exception:
                pass
        
        # 默认：2次免费
        return {
            "user_id": user_id,
            "free_remaining": 2,
            "total_used": 0,
            "monthly_active": False,
            "monthly_expires": None,
            "balance": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def save(self, user_id: str, data: Dict):
        """保存用户计费信息"""
        data["updated_at"] = datetime.now().isoformat()
        self._data[user_id] = data
        
        file_path = self._get_file_path(user_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存计费信息失败: {e}")
    
    def check_and_deduct(self, user_id: str) -> tuple[bool, str, int]:
        """
        检查并扣除次数
        
        Returns:
            (是否成功, 消息, 剩余免费次数)
        """
        data = self.get(user_id)
        
        # 检查月卡
        if data.get("monthly_active"):
            monthly_expires = data.get("monthly_expires")
            if monthly_expires:
                try:
                    expires = datetime.fromisoformat(monthly_expires)
                    if expires > datetime.now():
                        return True, "月卡用户，可无限使用", -1
                    else:
                        # 月卡过期
                        data["monthly_active"] = False
                        data["monthly_expires"] = None
                        self.save(user_id, data)
                except Exception:
                    pass
        
        # 检查余额（单次购买）
        if data.get("balance", 0) > 0:
            data["balance"] -= 1
            data["total_used"] += 1
            self.save(user_id, data)
            return True, f"使用余额扣费，剩余{data['balance']}次", data["balance"]
        
        # 检查免费次数
        if data.get("free_remaining", 0) > 0:
            data["free_remaining"] -= 1
            data["total_used"] += 1
            self.save(user_id, data)
            return True, f"使用免费次数，剩余{data['free_remaining']}次", data["free_remaining"]
        
        # 无可用次数
        return False, "免费次数已用完，请购买套餐", 0
    
    def purchase_monthly(self, user_id: str, days: int = 30) -> bool:
        """购买月卡"""
        data = self.get(user_id)
        expires = datetime.now() + timedelta(days=days)
        data["monthly_active"] = True
        data["monthly_expires"] = expires.isoformat()
        self.save(user_id, data)
        return True
    
    def purchase_single(self, user_id: str, count: int = 1) -> bool:
        """购买单次"""
        data = self.get(user_id)
        data["balance"] = data.get("balance", 0) + count
        self.save(user_id, data)
        return True
    
    def add_free_usage(self, user_id: str, count: int = 2) -> bool:
        """增加免费次数（运营活动用）"""
        data = self.get(user_id)
        data["free_remaining"] = data.get("free_remaining", 0) + count
        self.save(user_id, data)
        return True


# 全局实例
billing_store = BillingStore()


class BillingService:
    """计费服务"""
    
    FREE_LIMIT = 2  # 免费次数
    SINGLE_PRICE = 19  # 单次价格
    MONTHLY_PRICE = 99  # 月卡价格
    
    def __init__(self):
        self.store = billing_store
    
    def get_status(self, user_id: str) -> BillingStatus:
        """获取用户计费状态"""
        data = self.store.get(user_id)
        
        monthly_expires = None
        if data.get("monthly_expires"):
            try:
                monthly_expires = datetime.fromisoformat(data["monthly_expires"])
            except Exception:
                monthly_expires = None
        
        return BillingStatus(
            user_id=user_id,
            free_remaining=data.get("free_remaining", self.FREE_LIMIT),
            monthly_active=data.get("monthly_active", False),
            monthly_expires=monthly_expires,
            balance=data.get("balance", 0)
        )
    
    def check_and_deduct(self, user_id: str) -> tuple[bool, str, int]:
        """
        检查是否可以进行取名操作并扣除次数
        
        Returns:
            (是否成功, 消息, 剩余次数)
        """
        return self.store.check_and_deduct(user_id)
    
    def record_usage(self, user_id: str, naming_type: NamingType, names_count: int = 10):
        """记录使用（已在check_and_deduct中处理）"""
        # 这里可以添加额外的使用记录逻辑
        pass
    
    def get_price_info(self) -> dict:
        """获取价格信息"""
        return {
            "free_limit": self.FREE_LIMIT,
            "single_price": self.SINGLE_PRICE,
            "monthly_price": self.MONTHLY_PRICE,
            "single_price_yuan": f"¥{self.SINGLE_PRICE}",
            "monthly_price_yuan": f"¥{self.MONTHLY_PRICE}",
            "free_tips": f"新用户免费{self.FREE_LIMIT}次"
        }
