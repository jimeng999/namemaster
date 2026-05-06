# 取名大师 NameMaster 🎋

> AI智能取名服务 - 输入姓氏和期望，从国学典籍、诗词、五行八字中为你取好名

## ✨ 功能特点

- 🧘 **多种取名类型**：宝宝取名、公司取名、宠物取名、笔名/网名、英文名
- 📚 **国学典籍**：基于诗经、楚辞、唐诗宋词、论语、道德经等经典
- 🔮 **五行八字**：智能分析名字的五行属性
- 📊 **综合评分**：音韵、寓意、书写、重名率多维度评分
- 🎨 **中国风界面**：深色墨绿+金色主题，水墨纹理设计
- 💫 **BYOK模式**：支持用户自带API Key

## 💰 价格体系

| 套餐 | 价格 | 说明 |
|------|------|------|
| 免费体验 | 0元 | 新用户2次免费 |
| 单次取名 | ¥19 | 生成10个精选名字 |
| 月度会员 | ¥99 | 一个月内无限次取名 |

## 🚀 快速开始

### 本地开发

```bash
# 克隆项目
git clone <your-repo-url>
cd AI-NameMaster

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn api.index:app --reload --port 8000

# 访问 http://localhost:8000
```

### Vercel 部署

1. Fork 或上传代码到 GitHub
2. 在 Vercel 中导入项目
3. 部署即可（自动检测 vercel.json 配置）

### 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `OPENAI_API_KEY` | OpenAI API Key | 否（有内置备用方案）|
| `DEEPSEEK_API_KEY` | DeepSeek API Key | 否 |

## 📁 项目结构

```
AI-NameMaster/
├── api/
│   └── index.py          # Vercel Serverless 入口
├── app/
│   ├── main.py           # FastAPI 主应用入口
│   ├── models/
│   │   └── schemas.py    # Pydantic 数据模型
│   ├── routers/
│   │   ├── naming.py     # 取名 API 路由
│   │   └── user.py       # 用户/计费路由
│   └── services/
│       ├── generator.py  # AI 生成器
│       └── billing.py    # 计费服务
├── static/
│   └── index.html        # 前端页面
├── vercel.json           # Vercel 配置
├── requirements.txt     # Python 依赖
└── README.md            # 本文档
```

## 🔌 API 接口

### 取名生成
```
POST /api/naming/generate
Content-Type: application/json

{
  "surname": "李",
  "naming_type": "baby",
  "style": "classic",
  "gender": "male",
  "preferences": "希望名字大气有诗意",
  "birth_time": "2024年1月1日 10:30"
}
```

### 获取取名类型
```
GET /api/naming/types
```

### 获取取名风格
```
GET /api/naming/styles
```

### 获取价格信息
```
GET /api/user/pricing
```

## 🎨 界面预览

![取名大师界面预览](https://via.placeholder.com/800x600/0a0a0b/d4a574?text=取名大师+NameMaster)

## 🛠️ 技术栈

- **后端**：Python 3.9+ / FastAPI
- **前端**：原生 HTML5 + CSS3 + JavaScript
- **AI**：OpenAI GPT-4o-mini / DeepSeek Chat
- **部署**：Vercel Serverless

## 📝 License

MIT License

---

**Made with 🎋 by NameMaster**
