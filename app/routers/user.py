"""
User Router
用户路由 - 计费、用户状态等
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import BillingStatus
from app.services.billing import BillingService

router = APIRouter(prefix="/api/user", tags=["用户服务"])

billing_service = BillingService()


@router.get("/status/{user_id}", response_model=BillingStatus)
async def get_user_status(user_id: str):
    """获取用户状态和剩余次数"""
    return billing_service.get_status(user_id)


@router.get("/pricing")
async def get_pricing():
    """获取价格和套餐信息"""
    info = billing_service.get_price_info()
    return {
        **info,
        "packages": [
            {
                "id": "single",
                "name": "单次取名",
                "price": info["single_price"],
                "price_display": info["single_price_yuan"],
                "features": [
                    "生成10个精选名字",
                    "每个名字附带详细解析",
                    "五行八字分析",
                    "谐音检测"
                ]
            },
            {
                "id": "monthly",
                "name": "月度会员",
                "price": info["monthly_price"],
                "price_display": info["monthly_price_yuan"],
                "features": [
                    "一个月内无限次取名",
                    "优先AI生成通道",
                    "专属取名顾问服务",
                    "历史取名记录保存"
                ],
                "popular": True
            }
        ]
    }


@router.post("/purchase/{user_id}")
async def purchase_package(user_id: str, package: str):
    """
    购买套餐（模拟支付回调）
    
    注意：生产环境需要接入真实支付渠道
    """
    if package == "single":
        success = billing_service.store.purchase_single(user_id, 1)
        return {"success": success, "message": "购买成功，获得1次取名机会"}
    elif package == "monthly":
        success = billing_service.store.purchase_monthly(user_id, 30)
        return {"success": success, "message": "购买成功，成为月度会员"}
    else:
        raise HTTPException(status_code=400, detail="无效的套餐类型")


@router.post("/add-free/{user_id}")
async def add_free_usage(user_id: str, count: int = 2):
    """
    增加免费次数（运营活动用）
    
    注意：生产环境需要权限验证
    """
    success = billing_service.store.add_free_usage(user_id, count)
    return {"success": success, "message": f"成功增加{count}次免费机会"}
