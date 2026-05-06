"""
Pydantic Models and Schemas
取名大师数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NamingType(str, Enum):
    """取名类型枚举"""
    BABY = "baby"           # 宝宝取名
    COMPANY = "company"     # 公司取名
    PET = "pet"            # 宠物取名
    PEN_NAME = "pen_name"  # 笔名/网名
    ENGLISH = "english"    # 英文名


class NamingStyle(str, Enum):
    """取名风格枚举"""
    CLASSIC = "classic"         # 国学经典
    MODERN = "modern"           # 现代简约
    POETIC = "poetic"           # 诗意唯美
    MAGNIFICENT = "magnificent" # 大气阳刚
    GRACEFUL = "graceful"       # 温婉柔美


class Gender(str, Enum):
    """性别枚举"""
    MALE = "male"
    FEMALE = "female"
    UNSPECIFIED = "unspecified"


# ==================== Request Models ====================

class NamingRequest(BaseModel):
    """取名请求模型"""
    surname: str = Field(..., description="姓氏", min_length=1, max_length=10)
    naming_type: NamingType = Field(..., description="取名类型")
    style: NamingStyle = Field(NamingStyle.CLASSIC, description="取名风格")
    gender: Gender = Field(Gender.UNSPECIFIED, description="性别")
    preferences: Optional[str] = Field(None, description="用户偏好/期望")
    birth_time: Optional[str] = Field(None, description="出生时间(八字分析用)")
    birth_lunar: Optional[str] = Field(None, description="农历出生日期")
    industry: Optional[str] = Field(None, description="行业(公司取名用)")
    pet_type: Optional[str] = Field(None, description="宠物类型")
    api_key: Optional[str] = Field(None, description="用户自带的API Key (BYOK模式)")
    
    class Config:
        use_enum_values = True


class BillingCheckRequest(BaseModel):
    """计费检查请求"""
    user_id: str = Field(..., description="用户ID")


class UsageRecordRequest(BaseModel):
    """使用记录请求"""
    user_id: str
    naming_type: NamingType
    names_generated: int


# ==================== Response Models ====================

class NameDetail(BaseModel):
    """单个名字详情"""
    name: str = Field(..., description="名字")
    pinyin: Optional[str] = Field(None, description="拼音")
    source: Optional[str] = Field(None, description="出处")
    source_text: Optional[str] = Field(None, description="原文引用")
    meaning: str = Field(..., description="寓意解读")
    wuxing: Optional[str] = Field(None, description="五行属性")
    phonology: Optional[str] = Field(None, description="音韵分析")
    harmony_check: Optional[str] = Field(None, description="谐音检测")
    duplicate_rate: Optional[str] = Field(None, description="重名率")
    score: int = Field(..., description="综合评分(1-100)", ge=1, le=100)
    tags: Optional[List[str]] = Field(None, description="标签")
    
    # 公司取名专属
    industry_fit: Optional[str] = Field(None, description="行业契合度")
    spread_index: Optional[int] = Field(None, description="传播指数")
    trademark_advice: Optional[str] = Field(None, description="商标建议")
    
    # 宠物取名专属
    suitable_pet: Optional[str] = Field(None, description="适合品种")
    cuteness_index: Optional[int] = Field(None, description="可爱指数")


class NamingResponse(BaseModel):
    """取名响应模型"""
    success: bool
    names: List[NameDetail]
    remaining_free: int = Field(..., description="剩余免费次数")
    total_used: int = Field(..., description="已使用次数")
    message: Optional[str] = None


class BillingStatus(BaseModel):
    """计费状态"""
    user_id: str
    free_remaining: int
    monthly_active: bool
    monthly_expires: Optional[datetime]
    balance: int  # 剩余单次购买次数


class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str
    code: str
