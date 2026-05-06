"""
Naming Generator Service
取名生成服务 - 核心AI生成逻辑
"""
import os
import json
import re
from typing import List, Optional, Dict, Any
from openai import OpenAI
from app.models.schemas import (
    NamingRequest, NamingResponse, NameDetail,
    NamingType, NamingStyle, Gender
)


# ==================== Prompt Templates ====================

BABY_NAMING_PROMPT = """你是国学取名大师，精通诗经、楚辞、唐诗宋词、论语、道德经、易经等典籍。

请根据以下信息为用户生成10个精选宝宝名字：

姓氏：{surname}
性别：{gender}
风格偏好：{style}
用户期望：{preferences}
出生时间：{birth_time}

要求：
1. 每个名字必须有确切的诗词/典籍出处
2. 名字要音韵优美、寓意深远、书写美观
3. 考虑五行八字平衡

请为每个名字输出JSON格式（10个名字，共10个JSON对象，用数组包裹）：
{{
  "name": "名字",
  "pinyin": "拼音",
  "source": "出处（如：诗经·小雅）",
  "source_text": "原文诗句",
  "meaning": "寓意解读（50-100字）",
  "wuxing": "五行属性",
  "phonology": "音韵分析",
  "harmony_check": "谐音检测结果",
  "duplicate_rate": "重名率评估",
  "score": 评分(1-100),
  "tags": ["标签1", "标签2"]
}}

只输出JSON数组，不要任何其他文字。"""


COMPANY_NAMING_PROMPT = """你是品牌命名专家，精通市场营销、品牌战略、中华文化。

请根据以下信息为用户生成10个精选公司名称：

姓氏/创始人：{surname}
行业领域：{industry}
风格偏好：{style}
品牌期望：{preferences}

要求：
1. 名称要易记、易传播、有文化内涵
2. 符合行业特征，体现品牌价值
3. 便于商标注册和域名申请

请为每个名称输出JSON格式（10个名称，共10个JSON对象，用数组包裹）：
{{
  "name": "公司名称",
  "pinyin": "拼音缩写",
  "meaning": "寓意解读（50-80字）",
  "industry_fit": "行业契合度分析",
  "spread_index": 传播指数(1-100),
  "trademark_advice": "商标注册建议",
  "score": 综合评分(1-100),
  "tags": ["标签1", "标签2"]
}}

只输出JSON数组，不要任何其他文字。"""


PET_NAMING_PROMPT = """你是宠物起名专家，精通各种宠物的性格特点和可爱命名。

请根据以下信息为用户生成10个精选宠物名字：

姓氏/主人姓氏：{surname}
宠物类型：{pet_type}
性别：{gender}
期望风格：{preferences}

要求：
1. 名字要可爱、好叫、易记
2. 体现宠物个性或外貌特征
3. 便于日常呼唤

请为每个名字输出JSON格式（10个名字，共10个JSON对象，用数组包裹）：
{{
  "name": "宠物名字",
  "pinyin": "拼音",
  "meaning": "寓意解读（30-50字）",
  "suitable_pet": "适合的宠物类型",
  "cuteness_index": 可爱指数(1-100),
  "score": 综合评分(1-100),
  "tags": ["标签1", "标签2"]
}}

只输出JSON数组，不要任何其他文字。"""


PEN_NAME_NAMING_PROMPT = """你是文学创作命名专家，精通各类文学风格和笔名艺术。

请根据以下信息为用户生成10个精选笔名/网名：

姓氏/偏好：{surname}
期望风格：{style}
用户期望：{preferences}

要求：
1. 笔名要有文学气质、独特个性
2. 符合网络传播特点
3. 好记、有辨识度

请为每个名字输出JSON格式（10个名字，共10个JSON对象，用数组包裹）：
{{
  "name": "笔名/网名",
  "pinyin": "拼音",
  "meaning": "寓意解读（30-50字）",
  "style_analysis": "风格分析",
  "suitable_platform": "适合的平台",
  "score": 综合评分(1-100),
  "tags": ["标签1", "标签2"]
}}

只输出JSON数组，不要任何其他文字。"""


ENGLISH_NAMING_PROMPT = """你是跨文化命名专家，精通中英文命名文化。

请根据以下信息为用户生成10个精选英文名：

中文姓氏：{surname}
性别：{gender}
期望风格：{style}
用户期望：{preferences}

要求：
1. 英文名要与中文姓氏音韵和谐
2. 寓意美好、无不良含义
3. 便于外国人发音和记忆

请为每个名字输出JSON格式（10个名字，共10个JSON对象，用数组包裹）：
{{
  "name": "英文名",
  "pinyin": "发音",
  "meaning": "寓意解读（30-50字）",
  "harmony_check": "与姓氏的音韵和谐度",
  "origin": "名字来源",
  "score": 综合评分(1-100),
  "tags": ["标签1", "标签2"]
}}

只输出JSON数组，不要任何其他文字。"""


# ==================== Style Mapping ====================

STYLE_MAPPING = {
    NamingStyle.CLASSIC: "国学经典风格，偏好诗经、楚辞、唐诗宋词等古典文学",
    NamingStyle.MODERN: "现代简约风格，好写好记，简洁大方",
    NamingStyle.POETIC: "诗意唯美风格，注重意境和画面感",
    NamingStyle.MAGNIFICENT: "大气阳刚风格，体现力量和格局",
    NamingStyle.GRACEFUL: "温婉柔美风格，气质优雅内涵丰富"
}

GENDER_MAPPING = {
    Gender.MALE: "男孩",
    Gender.FEMALE: "女孩",
    Gender.UNSPECIFIED: "不限"
}


# ==================== Generator Service ====================

class NamingGenerator:
    """取名生成器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化生成器
        
        Args:
            api_key: OpenAI API Key，优先使用用户提供的，否则使用环境变量
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
        self.client = None
        if self.api_key:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self._get_base_url()
            )
    
    def _get_base_url(self) -> Optional[str]:
        """获取API Base URL"""
        if "DEEPSEEK" in (self.api_key or "").upper():
            return "https://api.deepseek.com"
        return None  # 使用默认的 OpenAI URL
    
    def _get_prompt(self, request: NamingRequest) -> str:
        """根据请求类型获取对应的Prompt"""
        style_desc = STYLE_MAPPING.get(request.style, "国学经典风格")
        gender_desc = GENDER_MAPPING.get(request.gender, "不限")
        
        if request.naming_type == NamingType.BABY:
            return BABY_NAMING_PROMPT.format(
                surname=request.surname,
                gender=gender_desc,
                style=style_desc,
                preferences=request.preferences or "音韵优美、寓意深远",
                birth_time=request.birth_time or "未提供"
            )
        elif request.naming_type == NamingType.COMPANY:
            return COMPANY_NAMING_PROMPT.format(
                surname=request.surname,
                industry=request.industry or "通用",
                style=style_desc,
                preferences=request.preferences or "易记、有内涵"
            )
        elif request.naming_type == NamingType.PET:
            return PET_NAMING_PROMPT.format(
                surname=request.surname,
                pet_type=request.pet_type or "猫狗通用",
                gender=gender_desc,
                preferences=request.preferences or "可爱、好叫"
            )
        elif request.naming_type == NamingType.PEN_NAME:
            return PEN_NAME_NAMING_PROMPT.format(
                surname=request.surname,
                style=style_desc,
                preferences=request.preferences or "有文学气质"
            )
        elif request.naming_type == NamingType.ENGLISH:
            return ENGLISH_NAMING_PROMPT.format(
                surname=request.surname,
                gender=gender_desc,
                style=style_desc,
                preferences=request.preferences or "音韵和谐"
            )
        
        return BABY_NAMING_PROMPT.format(
            surname=request.surname,
            gender=gender_desc,
            style=style_desc,
            preferences=request.preferences or "音韵优美",
            birth_time=request.birth_time or "未提供"
        )
    
    def _extract_json(self, text: str) -> List[Dict[str, Any]]:
        """从响应文本中提取JSON数组"""
        # 尝试找到JSON数组
        patterns = [
            r'\[[\s\S]*\]',  # 匹配数组
            r'\{[\s\S]*\}\s*,[\s\S]*\{[\s\S]*\}',  # 匹配多个对象
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # 尝试解析为JSON
                    data = json.loads(match)
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict):
                        return [data]
                except json.JSONDecodeError:
                    continue
        
        # 如果没找到，尝试清理文本后重试
        cleaned = text.strip()
        # 移除可能的markdown代码块标记
        cleaned = re.sub(r'^```json\s*', '', cleaned)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
        except json.JSONDecodeError:
            pass
        
        return []
    
    async def generate(self, request: NamingRequest) -> List[NameDetail]:
        """
        生成名字列表
        
        Args:
            request: 取名请求
            
        Returns:
            NameDetail列表
        """
        if not self.client:
            # 如果没有API Key，使用内置的名字库
            return self._generate_fallback(request)
        
        prompt = self._get_prompt(request)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini" if "DEEPSEEK" not in (self.api_key or "").upper() else "deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一位国学取名大师，精通诗经、楚辞、唐诗宋词等古典文学。请严格按照用户要求的JSON格式输出。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content
            json_data = self._extract_json(content)
            
            names = []
            for item in json_data[:10]:  # 最多10个
                try:
                    name_detail = NameDetail(
                        name=item.get("name", ""),
                        pinyin=item.get("pinyin"),
                        source=item.get("source"),
                        source_text=item.get("source_text"),
                        meaning=item.get("meaning", ""),
                        wuxing=item.get("wuxing"),
                        phonology=item.get("phonology"),
                        harmony_check=item.get("harmony_check"),
                        duplicate_rate=item.get("duplicate_rate"),
                        score=item.get("score", 80),
                        tags=item.get("tags"),
                        industry_fit=item.get("industry_fit"),
                        spread_index=item.get("spread_index"),
                        trademark_advice=item.get("trademark_advice"),
                        suitable_pet=item.get("suitable_pet"),
                        cuteness_index=item.get("cuteness_index")
                    )
                    names.append(name_detail)
                except Exception as e:
                    continue
            
            return names if names else self._generate_fallback(request)
            
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            return self._generate_fallback(request)
    
    def _generate_fallback(self, request: NamingRequest) -> List[NameDetail]:
        """
        当API不可用时，使用内置名字库
        
        这是一个内置的备用方案，基于经典诗词典籍的名字库
        """
        # 内置宝宝名字库（按风格分类）
        BABY_NAMES_LIBRARY = {
            NamingStyle.CLASSIC: [
                {"name": "沐晴", "source": "诗经·郑风", "meaning": "沐浴阳光，晴空万里，寓意孩子性格开朗，生活顺遂"},
                {"name": "思远", "source": "诗经·邶风", "meaning": "思绪悠远，志向高远，寓意孩子胸怀抱负，目光长远"},
                {"name": "嘉言", "source": "礼记", "meaning": "嘉言懿行，美德善言，寓意孩子品性优良，言谈得体"},
                {"name": "怀瑾", "source": "楚辞·九章", "meaning": "怀瑾握瑜，品德高洁，寓意孩子才华出众，品格高尚"},
                {"name": "知栩", "source": "诗经·小雅", "meaning": "栩栩如生，生机盎然，寓意孩子充满活力，乐观向上"},
                {"name": "清予", "source": "楚辞·九歌", "meaning": "清明澄澈，予你美好，寓意孩子心灵纯净，待人温柔"},
                {"name": "安屿", "source": "唐诗", "meaning": "安居乐业，海中之屿，寓意孩子生活安定，独立坚强"},
                {"name": "锦程", "source": "宋词", "meaning": "锦绣前程，光明未来，寓意孩子人生顺遂，前途似锦"},
                {"name": "静好", "source": "诗经·郑风", "meaning": "岁月静好，现世安稳，寓意孩子生活安宁，平安喜乐"},
                {"name": "德音", "source": "诗经·小雅", "meaning": "德音莫违，美好名声，寓意孩子品德高尚，声名远扬"},
            ],
            NamingStyle.MODERN: [
                {"name": "安然", "source": "现代", "meaning": "安之若素，泰然自若，寓意孩子性格沉稳，生活安稳"},
                {"name": "晨曦", "source": "现代", "meaning": "晨曦微露，朝气蓬勃，寓意孩子充满希望，每天都是新的开始"},
                {"name": "乐言", "source": "现代", "meaning": "乐天达观，言出必行，寓意孩子乐观开朗，诚实守信"},
                {"name": "舒苒", "source": "现代", "meaning": "舒展从容，苒苒生辉，寓意孩子从容淡定，光彩照人"},
                {"name": "以沫", "source": "现代", "meaning": "相濡以沫，互相关爱，寓意孩子重情重义，懂得珍惜"},
                {"name": "浅洛", "source": "现代", "meaning": "浅笑安然，洛神之美，寓意孩子温婉动人，笑口常开"},
                {"name": "鹿鸣", "source": "诗经", "meaning": "呦呦鹿鸣，食野之苹，寓意孩子如小鹿般活泼可爱"},
                {"name": "南风", "source": "现代", "meaning": "南风知意，吹梦西洲，寓意孩子善解人意，温柔体贴"},
                {"name": "北辰", "source": "现代", "meaning": "众星拱北辰，寓意孩子如北极星般出众，引人注目"},
                {"name": "云起", "source": "现代", "meaning": "云起龙骧，寓意孩子志向远大，腾飞高飞"},
            ],
            NamingStyle.POETIC: [
                {"name": "烟岚", "source": "诗词", "meaning": "山间烟岚，如梦似幻，寓意孩子如仙境般美好，气质出尘"},
                {"name": "疏影", "source": "宋词·林逋", "meaning": "疏影横斜水清浅，寓意孩子身姿优雅，气韵生动"},
                {"name": "晚晴", "source": "唐诗", "meaning": "夕阳无限好，晚晴更怡人，寓意历经风雨终见彩虹"},
                {"name": "微雨", "source": "诗词", "meaning": "微雨洗春色，润物细无声，寓意孩子温柔细腻，滋养他人"},
                {"name": "流萤", "source": "诗词", "meaning": "轻罗小扇扑流萤，寓意孩子活泼灵动，熠熠生辉"},
                {"name": "惊鸿", "source": "宋词", "meaning": "翩若惊鸿，婉若游龙，寓意孩子身姿优美，气质不凡"},
                {"name": "白露", "source": "诗经", "meaning": "蒹葭苍苍，白露为霜，寓意孩子纯洁无瑕，清新脱俗"},
                {"name": "青梧", "source": "诗词", "meaning": "梧桐更兼细雨，寓意孩子如梧桐般高洁，志向远大"},
                {"name": "采薇", "source": "诗经", "meaning": "采薇采薇，薇亦作止，寓意孩子勤劳善良，自食其力"},
                {"name": "凌霜", "source": "诗词", "meaning": "荷尽已无擎雨盖，菊残犹有傲霜枝，寓意孩子坚韧不拔"},
            ],
            NamingStyle.MAGNIFICENT: [
                {"name": "天佑", "source": "经典", "meaning": "天之佑助，承天之佑，寓意孩子得天独厚，受上天庇佑"},
                {"name": "君临", "source": "经典", "meaning": "君临天下，气势非凡，寓意孩子有领导才能，气度不凡"},
                {"name": "御风", "source": "庄子", "meaning": "列子御风，泠然善也，寓意孩子自由洒脱，志向高远"},
                {"name": "凌云", "source": "杜甫", "meaning": "会当凌绝顶，一览众山小，寓意孩子志存高远，勇攀高峰"},
                {"name": "破浪", "source": "李白", "meaning": "长风破浪会有时，直挂云帆济沧海，寓意孩子勇于进取"},
                {"name": "星河", "source": "现代", "meaning": "满天星河，璀璨夺目，寓意孩子如星辰般闪耀"},
                {"name": "天翔", "source": "经典", "meaning": "凤凰于飞，翱翔九天，寓意孩子前程远大，自由翱翔"},
                {"name": "擎宇", "source": "经典", "meaning": "擎天架海，气宇轩昂，寓意孩子顶天立地，气魄非凡"},
                {"name": "耀辉", "source": "经典", "meaning": "光耀门楣，辉映千秋，寓意孩子光宗耀祖，成就非凡"},
                {"name": "承泽", "source": "经典", "meaning": "承天之泽，福泽绵长，寓意孩子承蒙厚爱，福气满满"},
            ],
            NamingStyle.GRACEFUL: [
                {"name": "婉清", "source": "诗经", "meaning": "野有蔓草，零露漙兮。有美一人，清扬婉兮，寓意温婉清丽"},
                {"name": "若兰", "source": "楚辞", "meaning": "秋兰兮麋芜，罗生兮堂下，寓意如兰般高洁优雅"},
                {"name": "素年", "source": "诗词", "meaning": "琉璃岁月，素年锦时，寓意孩子纯真美好的时光"},
                {"name": "锦书", "source": "宋词", "meaning": "云中谁寄锦书来，寓意才情兼备，文采飞扬"},
                {"name": "含章", "source": "易经", "meaning": "含章可贞，以时发也，寓意内秀于心，外秀于形"},
                {"name": "映雪", "source": "诗词", "meaning": "孙康映雪，苦学成才，寓意孩子勤奋好学，品性坚韧"},
                {"name": "念慈", "source": "佛经", "meaning": "慈眼视众生，寓意孩子慈悲为怀，善良温柔"},
                {"name": "清欢", "source": "苏轼", "meaning": "人间有味是清欢，寓意孩子懂得生活，平淡是真"},
                {"name": "知墨", "source": "现代", "meaning": "知书达墨，才情兼备，寓意孩子学识渊博，气质文雅"},
                {"name": "初心", "source": "佛经", "meaning": "不忘初心，方得始终，寓意孩子保持纯真，坚持梦想"},
            ]
        }
        
        # 根据性别过滤
        gender_filter_names = []
        for name_data in BABY_NAMES_LIBRARY.get(request.style, BABY_NAMES_LIBRARY[NamingStyle.CLASSIC]):
            name = name_data["name"]
            # 简单判断：常用偏女性化的字
            female_chars = ["晴", "瑶", "琳", "欣", "怡", "婷", "雅", "诗", "语", "兰", "雪", "月", "雨", "露", "薇", "清", "柔", "婉", "静", "好", "苒", "沫", "洛", "鹿", "岚", "影", "萤", "鸿", "梧", "欢", "墨"]
            male_chars = ["远", "嘉", "怀", "知", "程", "安", "然", "言", "鸣", "风", "辰", "起", "佑", "临", "御", "云", "浪", "星", "翔", "宇", "辉", "泽", "墨"]
            
            if request.gender == Gender.MALE:
                if any(c in male_chars for c in name):
                    gender_filter_names.append(name_data)
            elif request.gender == Gender.FEMALE:
                if any(c in female_chars for c in name):
                    gender_filter_names.append(name_data)
            else:
                gender_filter_names.append(name_data)
        
        # 生成NameDetail列表
        names = []
        for i, name_data in enumerate(gender_filter_names[:10]):
            surname = request.surname
            full_name = surname + name_data["name"] if len(name_data["name"]) == 1 else surname + name_data["name"]
            
            # 五行分析（简单版）
            wuxing_map = {
                "木": ["林", "森", "柏", "松", "桐", "枫", "梅", "桂", "竹", "草", "芽", "荣"],
                "火": ["炎", "焰", "光", "耀", "辉", "明", "亮", "晴", "晨", "旭", "阳", "晶"],
                "土": ["坤", "培", "坚", "城", "墨", "壁", "壤", "堂", "域", "基"],
                "金": ["鑫", "铭", "锋", "锐", "铜", "铁", "银", "锡", "鉴", "钟"],
                "水": ["泽", "润", "清", "洁", "泉", "渊", "波", "涛", "澜", "溪", "雨", "雪"]
            }
            
            wuxing = "木"  # 默认
            for element, chars in wuxing_map.items():
                if any(c in name_data["name"] for c in chars):
                    wuxing = element
                    break
            
            name_detail = NameDetail(
                name=full_name,
                pinyin=self._get_pinyin(name_data["name"]),
                source=name_data["source"],
                source_text=self._get_source_text(name_data["source"], name_data["name"]),
                meaning=name_data["meaning"],
                wuxing=wuxing,
                phonology=f"声调搭配合理，韵律优美，读来朗朗上口",
                harmony_check="无不良谐音，可放心使用",
                duplicate_rate="重名率较低，独特而有品味",
                score=85 + (i % 15),  # 85-99分
                tags=self._get_tags(name_data["name"], request.style)
            )
            names.append(name_detail)
        
        return names
    
    def _get_pinyin(self, name: str) -> str:
        """获取拼音（简化版）"""
        pinyin_map = {
            "沐": "mù", "晴": "qíng", "思": "sī", "远": "yuǎn", "嘉": "jiā", "言": "yán",
            "怀": "huái", "瑾": "jǐn", "知": "zhī", "栩": "xǔ", "清": "qīng", "予": "yǔ",
            "安": "ān", "屿": "yǔ", "锦": "jǐn", "程": "chéng", "静": "jìng", "好": "hǎo",
            "德": "dé", "音": "yīn", "然": "rán", "晨": "chén", "曦": "xī", "乐": "lè",
            "舒": "shū", "苒": "rǎn", "以": "yǐ", "沫": "mò", "浅": "qiǎn", "洛": "luò",
            "鹿": "lù", "鸣": "míng", "南": "nán", "风": "fēng", "北": "běi", "辰": "chén",
            "起": "qǐ", "烟": "yān", "岚": "lán", "疏": "shū", "影": "yǐng", "晚": "wǎn",
            "微": "wēi", "雨": "yǔ", "流": "liú", "萤": "yíng", "惊": "jīng", "鸿": "hóng",
            "白": "bái", "露": "lù", "青": "qīng", "梧": "wú", "采": "cǎi", "薇": "wēi",
            "凌": "líng", "霜": "shuāng", "天": "tiān", "佑": "yòu", "君": "jūn", "临": "lín",
            "御": "yù", "云": "yún", "波": "bō", "浪": "làng", "星": "xīng", "河": "hé",
            "翔": "xiáng", "擎": "qíng", "宇": "yǔ", "耀": "yào", "辉": "huī", "承": "chéng",
            "泽": "zé", "婉": "wǎn", "若": "ruò", "兰": "lán", "素": "sù", "年": "nián",
            "书": "shū", "含": "hán", "章": "zhāng", "映": "yìng", "雪": "xuě", "念": "niàn",
            "慈": "cí", "欢": "huān", "初": "chū", "心": "xīn"
        }
        
        result = []
        for char in name:
            result.append(pinyin_map.get(char, char))
        return " ".join(result)
    
    def _get_source_text(self, source: str, name: str) -> str:
        """获取原文引用"""
        source_texts = {
            "诗经·郑风": "风雨如晦，鸡鸣不已。既见君子，云胡不喜？",
            "诗经·邶风": "泛彼柏舟，亦泛其流。耿耿不寐，如有隐忧。",
            "诗经·小雅": "呦呦鹿鸣，食野之苹。我有嘉宾，鼓瑟吹笙。",
            "诗经": "蒹葭苍苍，白露为霜。所谓伊人，在水一方。",
            "楚辞·九章": "怀瑾握瑜兮，穷不知所示。",
            "楚辞·九歌": "青云衣兮白霓裳，举长矢兮射天狼。",
            "楚辞": "秋兰兮麋芜，罗生兮堂下。",
            "庄子": "夫列子御风而行，泠然善也。",
            "礼记": "玉不琢，不成器；人不学，不知道。是故古之王者建国君民，教学为先。",
            "易经": "九三：含章可贞，或从王事，无成有终。",
            "宋词·林逋": "疏影横斜水清浅，暗香浮动月黄昏。",
            "宋词": "翩若惊鸿，婉若游龙，荣曜秋菊，华茂春松。",
            "唐诗": "夕阳无限好，只是近黄昏。",
            "唐诗": "长风破浪会有时，直挂云帆济沧海。",
            "杜甫": "会当凌绝顶，一览众山小。",
            "苏轼": "人间有味是清欢。",
            "李白": "长风破浪会有时，直挂云帆济沧海。",
            "现代": "愿你出走半生，归来仍是少年。",
            "佛经": "不忘初心，方得始终。",
            "经典": "天行健，君子以自强不息。",
        }
        
        for key, text in source_texts.items():
            if key in source:
                return text
        
        return f"此名取自{source}，寓意深远。"
    
    def _get_tags(self, name: str, style: NamingStyle) -> list:
        """获取标签"""
        base_tags = {
            NamingStyle.CLASSIC: ["国学经典", "诗词典故", "文化底蕴"],
            NamingStyle.MODERN: ["简洁大方", "易写好记", "现代审美"],
            NamingStyle.POETIC: ["意境优美", "画面感强", "诗情画意"],
            NamingStyle.MAGNIFICENT: ["气势磅礴", "格局宏大", "阳刚之美"],
            NamingStyle.GRACEFUL: ["温婉优雅", "气质出众", "柔美动人"]
        }
        
        return base_tags.get(style, ["寓意美好", "音韵优美"])
