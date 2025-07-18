Resume API 接口文档

一、概览

本项目提供基于 FastAPI 的简历解析与生成后端服务，集成了 Dify Chatflow（/v1/chat-messages）调用、PDF 生成、文本改写/扩展等功能。
服务容器化部署，默认监听 8699 端口，依赖运行在同一 Docker 网络中的 Dify 容器（内部端口 5001）。

二、目录结构

resume_api/                     ← 项目根目录
├── Dockerfile                  ← 后端镜像构建文件
├── docker-compose.yml          ← Docker Compose 编排
├── .env                        ← 环境变量（请根据示例填写）
├── main.py                     ← FastAPI 应用入口
├── requirements.txt            ← Python 依赖
├── templates/                  ← Jinja2 模板存放目录
    ├── resume_template.html
    └── style.css               ← PDF 渲染样式表

三、配置说明

1. .env 文件
复制一份示例 .env，填写的密钥与地址：

#Dify Chatflow API 容器的内部端口
DIFY_API_URL=http://docker-api-1:5001/v1/chat-messages

#Dify 应用程序 API 密钥（用于 Chatflow）
DIFY_API_KEY_PARSE=app-xxxxxxxxxxxx

#FastAPI 自身鉴权密钥
API_KEY=your-backend-api-key

2. docker-compose.yml
确保 services.backend 配置如下，并加入现有网络：

version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8699:8699"
    env_file:
      - .env
    networks:
      - docker_default
    restart: always

networks:
  docker_default:
    external: true
build: . 指向项目根的 Dockerfile。

ports 映射宿主机 8699 到容器内 8699。

networks 中 docker_default 必须与 Dify 容器所在网络名称一致。

四、接口列表

路径            方法            描述
POST /parse-resume-text/	POST	文本解析 → JSON （调用 Chatflow）
POST /generate-resume/	POST	结构化 JSON → 渲染 PDF
POST /rewrite-text/	POST	文本改写
POST /expand-text/	POST	文本扩写
POST /contract-text/	POST	文本缩写
POST /process_json_to_text/	POST	任意 JSON → 文本

所有 POST 接口 均需在请求头中带上 X-API-Key: <API_KEY> 进行鉴权。

API端点详解
4.1 生成PDF简历
端点: /generate-resume/

方法: POST

功能: 接收结构化的简历信息（JSON格式），并生成一个PDF文件。

请求头:

Content-Type: application/json

X-API-Key: 9589ca16aa2844de6975809fbac3891ef2a105eadcde6f56e044c60b6b774ec4

请求体 (Body):
一个包含用户信息的JSON对象。此结构为必需格式。

示例:

{
  "user_uid": "test-user-001",
  "user_name": "李欣然",
  "user_contact_info": {
    "phone": "185-7764-3281",
    "email": "xinran.li20@stu.ecnu.edu.cn"
  },
  "user_education": [
    {
      "user_university": "华东师范大学",
      "user_major": "统计学",
      "degree": "理学学士",
      "dates": "2018/09 - 2022/06",
      "details": "核心课程：高等数学、概率论与数理统计、时间序列分析、机器学习导论、R语言编程和社会调查方法等。",
      "user_grade": "大三",
      "user_graduate_year": "2022",
      "user_gpa": "4.0",
      "user_language_score": "IELTS 7.0"
    }
  ],
  "internship_experience": [
    {
      "company": "腾讯",
      "role": "产品数据实习生",
      "location": "深圳",
      "dates": "2021/12 - 2022/03",
      "description_points": [
        "负责用户行为数据的分析和产品功能优化建议。",
        "使用 SQL 和 Python 构建了用户活跃度与留存率的自动化监控报表。"
      ]
    }
  ],
  "user_research_experience": [
    {
      "research project": "大学生创新项目",
      "role": "第一作者",
      "location": "校内",
      "dates": "2020/11 - 2021/02",
      "description_points": [
        "从事字体显示研究并发表论文《数字时代的字体艺术》。"
      ]
    }
  ],
  "user_extracurricular_activities": [
    {
      "organization": "数据科学协会",
      "role": "运营部部长",
      "location": "校内",
      "dates": "2019/03 - 2020/12",
      "description_points": [
        "组织社团活动、提升成员参与度。",
        "策划微信公众号内容，定期发布数据分析相关的推文，增强社团影响力。"
      ]
    }
  ],
  "user_target": "申请剑桥大学"
}

成功响应:

状态码: 200 OK

响应体: 二进制的PDF文件流。在前端，这通常被处理为一个 Blob 对象，然后可以创建一个下载链接。

4.2 上传PDF并解析
端点: /parse-resume/

方法: POST

功能: 接收一个PDF文件，提取其文本，调用Dify进行解析，并返回与2.1节中结构相同的JSON对象。

请求头:

X-API-Key: 9589ca16aa2844de6975809fbac3891ef2a105eadcde6f56e044c60b6b774ec4

注意: 不要手动设置 Content-Type。当使用 FormData 上传文件时，浏览器会自动设置正确的 multipart/form-data 类型和边界。

请求体 (Body):
必须使用 FormData 对象。

创建一个 FormData 实例。

使用 .append() 方法添加文件，键名必须为 file。

JavaScript示例:

const formData = new FormData();
const pdfFile = document.getElementById('myFileInput').files[0];
formData.append('file', pdfFile);

// 然后将 formData 作为 fetch 的 body 发送

成功响应:

状态码: 200 OK

响应体: 一个包含解析结果的JSON对象。

{
    "user_uid": "full-example-user-001",
    "user_name": "孙悦",
    "user_contact_info": {
        "phone": "",
        "email": ""
    },
    "user_education": [
        {
            "user_university": "中央美术学院",
            "user_major": "视觉传达",
            "degree": "",
            "dates": "",
            "details": "",
            "user_grade": "硕士毕业生",
            "user_graduate_year": "2024",
            "user_gpa": "3.9/4.0",
            "user_language_score": "精通英语"
        }
    ],
    "internship_experience": [
        {
            "company": "创意无限设计工作室",
            "role": "平面设计实习生",
            "location": "",
            "dates": "",
            "description_points": [
                "负责多个客户的品牌视觉设计"
            ]
        }
    ],
    "user_research_experience": [
        {
            "research_project": "毕业设计作品《数字时代的字体艺术》",
            "role": "",
            "location": "",
            "dates": "",
            "description_points": [
                "获得学院金奖"
            ]
        }
    ],
    "user_extracurricular_activities": [
        {
            "organization": "学院年度毕业设计展",
            "role": "视觉策划与执行",
            "location": "",
            "dates": "",
            "description_points": [
                "负责整体视觉策划与执行"
            ]
        }
    ],
    "user_target": "平面设计师 / 视觉设计师"
}

4.3 上传简历文本并解析
端点: /parse-resume-text/

方法: POST

功能: 接收一段简历纯文本，调用Dify进行解析，并返回与2.1节中结构相同的JSON对象。

请求头:

Content-Type: application/json

X-API-Key: 9589ca16aa2844de6975809fbac3891ef2a105eadcde6f56e044c60b6b774ec4

请求体 (Body):
一个包含 text 键的JSON对象。
示例:

{
    "text": "李欣然，华东师范大学统计学学士，GPA 4.0。曾在腾讯担任产品数据实习生..."
}

成功响应:

状态码: 200 OK

响应体: 一个包含解析结果的JSON对象。

{
    "user_uid": "full-example-user-001",
    "user_name": "孙悦",
    "user_contact_info": {
        "phone": "",
        "email": ""
    },
    "user_education": [
        {
            "user_university": "中央美术学院",
            "user_major": "视觉传达",
            "degree": "",
            "dates": "",
            "details": "",
            "user_grade": "硕士毕业生",
            "user_graduate_year": "2024",
            "user_gpa": "3.9/4.0",
            "user_language_score": "精通英语"
        }
    ],
    "internship_experience": [
        {
            "company": "创意无限设计工作室",
            "role": "平面设计实习生",
            "location": "",
            "dates": "",
            "description_points": [
                "负责多个客户的品牌视觉设计"
            ]
        }
    ],
    "user_research_experience": [
        {
            "research_project": "毕业设计作品《数字时代的字体艺术》",
            "role": "",
            "location": "",
            "dates": "",
            "description_points": [
                "获得学院金奖"
            ]
        }
    ],
    "user_extracurricular_activities": [
        {
            "organization": "学院年度毕业设计展",
            "role": "视觉策划与执行",
            "location": "",
            "dates": "",
            "description_points": [
                "负责整体视觉策划与执行"
            ]
        }
    ],
    "user_target": "平面设计师 / 视觉设计师"
}

4.4 文本处理API (改写/扩写/缩写)
以下API的调用方式完全相同，它们都接收一个包含文本的JSON对象。

/rewrite-text/ (润色文本)

/expand-text/ (扩写文本)

/contract-text/ (缩写文本)

方法: POST

请求头:

Content-Type: application/json

X-API-Key: 9589ca16aa2844de6975809fbac3891ef2a105eadcde6f56e044c60b6b774ec4

请求体 (Body):
一个包含 text 键的JSON对象。
示例:

{
    "text": "这是需要被处理的原始文本内容。"
}

成功响应:

状态码: 200 OK

响应体: 一个JSON对象，根据调用的端点不同，键名也不同。

/rewrite-text/: {"rewritten_text": "..."}

/expand-text/: {"expanded_text": "..."}

/contract-text/: {"contracted_text": "..."}

4.5 简历评估API
端点: /process_json_to_text/

方法: POST

功能: 接收一个简历的任意结构的JSON对象，并返回对简历的评估文本。

请求头:

Content-Type: application/json

X-API-Key: 9589ca16aa2844de6975809fbac3891ef2a105eadcde6f56e044c60b6b774ec4

请求体 (Body):
简历的任何合法的JSON对象。
示例:

{
  "user_uid": "test-user-001",
  "user_name": "李欣然",
  "user_contact_info": {
    "phone": "185-7764-3281",
    "email": "xinran.li20@stu.ecnu.edu.cn"
  },
  "user_education": [
    {
      "user_university": "华东师范大学",
      "user_major": "统计学",
      "degree": "理学学士",
      "dates": "2018/09 - 2022/06",
      "details": "核心课程：高等数学、概率论与数理统计、时间序列分析、机器学习导论、R语言编程和社会调查方法等。",
      "user_grade": "大三",
      "user_graduate_year": "2022",
      "user_gpa": "4.0",
      "user_language_score": "IELTS 7.0"
    }
  ],
  "internship_experience": [
    {
      "company": "腾讯",
      "role": "产品数据实习生",
      "location": "深圳",
      "dates": "2021/12 - 2022/03",
      "description_points": [
        "负责用户行为数据的分析和产品功能优化建议。",
        "使用 SQL 和 Python 构建了用户活跃度与留存率的自动化监控报表。"
      ]
    }
  ],
  "user_research_experience": [
    {
      "research project": "大学生创新项目",
      "role": "第一作者",
      "location": "校内",
      "dates": "2020/11 - 2021/02",
      "description_points": [
        "从事字体显示研究并发表论文《数字时代的字体艺术》。"
      ]
    }
  ],
  "user_extracurricular_activities": [
    {
      "organization": "数据科学协会",
      "role": "运营部部长",
      "location": "校内",
      "dates": "2019/03 - 2020/12",
      "description_points": [
        "组织社团活动、提升成员参与度。",
        "策划微信公众号内容，定期发布数据分析相关的推文，增强社团影响力。"
      ]
    }
  ],
  "user_target": "申请剑桥大学"
}

成功响应:

状态码: 200 OK

响应体: 一个包含处理后文本的JSON对象。

{
    "processed_text": "根据整个输入的简历JSON生成的评估文本会在这里..."
}
