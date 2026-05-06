"""
Naming Router
取名路由 - 核心取名API
"""
from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from app.models.schemas import (
    NamingRequest, NamingResponse, NameDetail,
    ErrorResponse, NamingType, NamingStyle, Gender
)
from app.services.generator import NamingGenerator
from app.services.billing import BillingService

router = APIRouter(prefix="/api/naming", tags=["取名服务"])

# 服务实例
generator_service = NamingGenerator()
billing_service = BillingService()


@router.post("/generate", response_model=NamingResponse)
async def generate_names(request: NamingRequest):
    """
    生成名字
    
    核心API：根据姓氏、类型、风格等参数生成10个精选名字
    """
    # 获取用户ID（从Header或生成临时ID）
    user_id = request.api_key[:8] if request.api_key else "anonymous"
    
    # 检查计费状态
    success, message, remaining = billing_service.check_and_deduct(user_id)
    
    if not success:
        return NamingResponse(
            success=False,
            names=[],
            remaining_free=remaining,
            total_used=0,
            message=message
        )
    
    # 使用用户提供的API Key或环境变量中的Key
    if request.api_key:
        generator_service.client = None  # 重置客户端，让generator使用request中的key
    
    # 生成名字
    try:
        names = await generator_service.generate(request)
        
        return NamingResponse(
            success=True,
            names=names,
            remaining_free=remaining if remaining >= 0 else 999,
            total_used=billing_service.get_status(user_id).free_remaining,
            message="取名成功！" if names else "未能生成名字，请稍后重试"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成名字失败: {str(e)}")


@router.get("/types")
async def get_naming_types():
    """获取取名类型列表"""
    return {
        "types": [
            {
                "value": NamingType.BABY.value,
                "label": "👶 宝宝取名",
                "description": "五行八字+诗词典故，为宝宝取个好名字",
                "icon": "👶"
            },
            {
                "value": NamingType.COMPANY.value,
                "label": "🏢 公司取名",
                "description": "行业+寓意+易传播，打造品牌名称",
                "icon": "🏢"
            },
            {
                "value": NamingType.PET.value,
                "label": "🐱 宠物取名",
                "description": "可爱+个性+好叫，给萌宠取个名字",
                "icon": "🐱"
            },
            {
                "value": NamingType.PEN_NAME.value,
                "label": "✍️ 笔名/网名",
                "description": "文学气质+独特个性，打造个人品牌",
                "icon": "✍️"
            },
            {
                "value": NamingType.ENGLISH.value,
                "label": "🌍 英文名",
                "description": "音韵和谐+美好寓意，起个英文名",
                "icon": "🌍"
            }
        ]
    }


@router.get("/styles")
async def get_naming_styles():
    """获取取名风格列表"""
    return {
        "styles": [
            {
                "value": NamingStyle.CLASSIC.value,
                "label": "📜 国学经典",
                "description": "诗经/楚辞/唐诗宋词，古典韵味",
                "color": "#d4a574"
            },
            {
                "value": NamingStyle.MODERN.value,
                "label": "✨ 现代简约",
                "description": "好写好记，简洁大方",
                "color": "#64748b"
            },
            {
                "value": NamingStyle.POETIC.value,
                "label": "🎨 诗意唯美",
                "description": "意境+画面感，诗情画意",
                "color": "#8b5cf6"
            },
            {
                "value": NamingStyle.MAGNIFICENT.value,
                "label": "🔥 大气阳刚",
                "description": "力量+格局，气势磅礴",
                "color": "#ef4444"
            },
            {
                "value": NamingStyle.GRACEFUL.value,
                "label": "🌸 温婉柔美",
                "description": "气质+内涵，优雅动人",
                "color": "#ec4899"
            }
        ]
    }


@router.get("/genders")
async def get_genders():
    """获取性别选项"""
    return {
        "genders": [
            {"value": Gender.MALE.value, "label": "男孩 👦"},
            {"value": Gender.FEMALE.value, "label": "女孩 👧"},
            {"value": Gender.UNSPECIFIED.value, "label": "不限 👤"}
        ]
    }


@router.get("/pricing")
async def get_pricing():
    """获取价格信息"""
    return billing_service.get_price_info()
