import os
import secrets
import traceback
import json
import fitz      
import requests  
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile
from fastapi.security import APIKeyHeader
from fastapi.responses import Response, JSONResponse
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, Field
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from typing import Optional, List, Dict, Any

# --- 1. 自动加载 .env 文件 ---
load_dotenv()

# --- 2. 安全与配置 ---
api_key_header_scheme = APIKeyHeader(name="X-API-Key")
API_KEY = os.getenv("API_KEY")
DIFY_API_URL = os.getenv("DIFY_API_URL")
DIFY_API_KEY_PARSE = os.getenv("DIFY_API_KEY_PARSE")
DIFY_API_KEY_REWRITE = os.getenv("DIFY_API_KEY_REWRITE")
DIFY_API_KEY_EXPAND = os.getenv("DIFY_API_KEY_EXPAND")
DIFY_API_KEY_CONTRACT = os.getenv("DIFY_API_KEY_CONTRACT")
DIFY_API_KEY_PROCESS_TEXT = os.getenv("DIFY_API_KEY_PROCESS_TEXT")


# 启动时检查所有必需的环境变量
if not all([API_KEY, DIFY_API_URL, DIFY_API_KEY_PARSE, DIFY_API_KEY_REWRITE, DIFY_API_KEY_EXPAND, DIFY_API_KEY_CONTRACT,
            DIFY_API_KEY_PROCESS_TEXT]):
    raise ValueError("One or more environment variables are not set. Please check your .env file.")


# --- 3. Dify 调用辅助函数 ---
def clean_dify_response(text: str) -> str:
    """简单的清理函数，移除可能的前后多余字符或标记。"""
    if text.strip().startswith("```json"):
        text = text.strip()[7:]
    if text.strip().endswith("```"):
        text = text.strip()[:-3]
    return text.strip()


def call_dify_chat(query_text: str) -> dict:
    """(用于解析) 调用Dify并期望返回一个可解析为JSON的'answer'。"""
    headers = {'Authorization': f'Bearer {DIFY_API_KEY_PARSE}', 'Content-Type': 'application/json'}
    payload = {"inputs": {}, "query": query_text, "response_mode": "blocking", "user": "resume-app-user"}
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=120);
        response.raise_for_status()
        answer_text = response.json().get('answer', '{"error": "Dify未能返回有效结果。"}')
        return json.loads(clean_dify_response(answer_text))
    except Exception as e:
        return {"error": f"调用Dify服务时出错: {e}"}


# --- 其他 call_dify 函数 ---
def call_dify_rewrite(query_text: str) -> str:
    """
    调用 Dify 改写接口，将输入文本进行改写。

    Args:
        query_text (str): 原始文本
    Returns:
        str: 改写后的文本，若出错则返回错误描述
    """
    headers = {'Authorization': f'Bearer {DIFY_API_KEY_REWRITE}', 'Content-Type': 'application/json'}
    payload = {"inputs": {}, "query": query_text, "response_mode": "blocking", "user": "rewrite-app-user"}
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=120);
        response.raise_for_status()
        return response.json().get('answer', 'Dify未能返回有效结果。')
    except Exception as e:
        return f"调用Dify改写功能失败: {e}"


def call_dify_expand(query_text: str) -> str:
    """
    调用 Dify 扩写接口，将输入文本进行扩展。

    Args:
        query_text (str): 原始文本
    Returns:
        str: 扩写后的文本，若出错则返回错误描述
    """
    headers = {'Authorization': f'Bearer {DIFY_API_KEY_EXPAND}', 'Content-Type': 'application/json'}
    payload = {"inputs": {}, "query": query_text, "response_mode": "blocking", "user": "rewrite-app-user"}
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=120);
        response.raise_for_status()
        return response.json().get('answer', 'Dify未能返回有效结果。')
    except Exception as e:
        return f"调用Dify扩写功能失败: {e}"


def call_dify_contract(query_text: str) -> str:
    """
    调用 Dify 缩写接口，将输入文本进行缩写。

    Args:
        query_text (str): 原始文本
    Returns:
        str: 缩写后的文本，若出错则返回错误描述
    """
    headers = {'Authorization': f'Bearer {DIFY_API_KEY_CONTRACT}', 'Content-Type': 'application/json'}
    payload = {"inputs": {}, "query": query_text, "response_mode": "blocking", "user": "rewrite-app-user"}
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=120);
        response.raise_for_status()
        return response.json().get('answer', 'Dify未能返回有效结果。')
    except Exception as e:
        return f"调用Dify缩写功能失败: {e}"


def call_dify_process_text(query_text: str) -> str:
    """
    调用 Dify 文本处理接口，将 JSON 转为可读文本。

    Args:
        query_text (str): 格式化的 JSON 字符串
    Returns:
        str: 处理后的文本结果，若出错则返回错误描述
    """
    headers = {'Authorization': f'Bearer {DIFY_API_KEY_PROCESS_TEXT}', 'Content-Type': 'application/json'}
    payload = {"inputs": {}, "query": query_text, "response_mode": "blocking", "user": "json-to-text-user"}
    try:
        response = requests.post(DIFY_API_URL, headers=headers, json=payload, timeout=120);
        response.raise_for_status()
        return response.json().get('answer', 'Dify未能返回有效结果。')
    except Exception as e:
        return f"调用Dify文本处理功能失败: {e}"


# --- 4. FastAPI 应用初始化和鉴权 ---
app = FastAPI(title="文本与简历处理API")
api_key_header_scheme = APIKeyHeader(name="X-API-Key")


async def get_api_key(api_key_header: str = Depends(api_key_header_scheme)):
    """
    验证请求中的 X-API-Key 与环境变量中的 API_KEY 是否匹配。
    
    Args:
        api_key_header (str): 请求头中传递的 API Key
    Returns:
        str: 通过验证的 API Key
    Raises:
        HTTPException: 验证失败时抛出 403 错误
    """
    if secrets.compare_digest(api_key_header, API_KEY): return api_key_header
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")


# --- 5. Pydantic 数据模型 ---
class UserProfile(BaseModel):
    user_uid: str
    user_name: Optional[str] = Field("匿名用户")
    user_university: Optional[str] = Field(None)
    user_grade: Optional[str] = Field(None)
    user_graduate_year: Optional[str] = Field(None)
    user_major: Optional[str] = Field(None)
    user_gpa: Optional[str] = Field(None)
    user_language_score: Optional[str] = Field(None)
    user_internship_experience: Optional[str] = Field(None)
    user_research_experience: Optional[str] = Field(None)
    user_extracurricular_activities: Optional[str] = Field(None)
    user_target: Optional[str] = Field(None)
    user_phone: Optional[str] = None
    user_email: Optional[str] = None
    user_location: Optional[str] = None
    style: Optional[int] = Field(1, description="模板样式，1为默认单栏样式，2为两栏样式")    # style 字段，用于模板切换


class TextInput(BaseModel):
    text: str = Field(..., min_length=1)


class DifyJsonInput(BaseModel):
    inputs: Dict[str, Any] = Field(...)
    query: str = Field(...)


# --- Pydantic 数据模型 (PDF生成结构部分) ---
class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None

class EducationItem(BaseModel):
    user_university: str
    user_major: str
    degree: str
    dates: str
    details: Optional[str] = None
    user_grade: Optional[str] = None
    user_graduate_year: Optional[str] = None
    user_gpa: Optional[str] = None
    user_language_score: Optional[str] = None

class ExperienceItem(BaseModel):
    company: str
    role: str
    location: Optional[str] = None
    dates: str
    description_points: List[str]

class ResearchItem(BaseModel):
    research_project: str
    role: str
    location: Optional[str] = None
    dates: str
    description_points: List[str]

class ActivityItem(BaseModel):
    organization: str
    role: str
    location: Optional[str] = None
    dates: str
    description_points: List[str]

# --- 统一的的简历数据模型 ---
class NewResumeProfile(BaseModel):
    user_uid: str
    user_name: str
    user_contact_info: ContactInfo
    user_education: List[EducationItem]
    internship_experience: List[ExperienceItem]
    user_research_experience: Optional[List[ResearchItem]] = []
    user_extracurricular_activities: Optional[List[ActivityItem]] = []
    user_target: Optional[str] = None

# --- 6. 简历生成功能所需设置 ---
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = Environment(loader=FileSystemLoader(template_dir))


# --- 7. API 端点 ---
@app.get("/")
def read_root(): return {"message": "API已启动。"}    # 根路径健康检查接口。 Returns:dict: 服务状态信息


@app.post("/generate-resume/", response_class=Response)
async def generate_resume(
    profile: NewResumeProfile, 
    api_key: str = Depends(get_api_key)
) -> Response:
    """
    根据结构化简历数据生成 PDF。

    Args:
        profile (NewResumeProfile): 完整的简历数据模型
        api_key (str): 用于鉴权的 API Key
    Returns:
        Response: 包含 PDF bytes 的 HTTP 响应，包含下载头
    """
    try:
        profile_data = profile.model_dump()
        resume_template = jinja_env.get_template("resume_template.html")
        css_file_path = os.path.join(template_dir, 'style.css')
        rendered_html = resume_template.render(profile_data)
        css = CSS(filename=css_file_path)
        pdf_bytes = HTML(string=rendered_html, base_url=template_dir).write_pdf(stylesheets=[css])
        headers = {'Content-Disposition': f'attachment; filename="resume_{profile.user_uid}.pdf"'}
        return Response(content=pdf_bytes, media_type='application/pdf', headers=headers)
    except Exception as e:
        traceback.print_exc()
        return Response(content=f"生成PDF时发生内部错误: {e}", status_code=500)

@app.post("/parse-resume/")
async def parse_resume(
    api_key: str = Depends(get_api_key), 
    file: UploadFile = File(...)
) -> JSONResponse:
    """
    上传并解析 PDF 简历，将其文本内容发送给 Dify Chatflow，并返回结构化 JSON。

    Args:
        api_key (str): 鉴权用的 API Key
        file (UploadFile): 上传的 PDF 文件
    Returns:
        JSONResponse: Dify 返回的结构化 JSON
    Raises:
        HTTPException: 解析失败或调用 Dify 失败时抛出对应 HTTP 错误
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Invalid file type.")
    try:
        pdf_bytes = await file.read()
        extracted_text = ""
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                extracted_text += page.get_text()
        if not extracted_text.strip():
            raise ValueError("Could not extract text.")
        dify_result_json = await run_in_threadpool(call_dify_chat, query_text=extracted_text)
        if "error" in dify_result_json:
            raise HTTPException(status_code=502, detail=dify_result_json)
        return JSONResponse(content=dify_result_json)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/parse-resume-text/")
async def parse_resume_text(
    input_data: TextInput, 
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """
    接收纯文本解析请求，将文本发送给 Dify Chatflow 并返回结构化结果。

    Args:
        input_data (TextInput): 包含 text 字段的请求体
        api_key (str): 鉴权用的 API Key
    Returns:
        JSONResponse: Dify 返回的结构化 JSON
    """
    try:
        dify_result_json = await run_in_threadpool(call_dify_chat, query_text=input_data.text)
        if "error" in dify_result_json:
            raise HTTPException(status_code=502, detail=dify_result_json)
        return JSONResponse(content=dify_result_json)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/rewrite-text/")
async def rewrite_text(
    input_data: TextInput,
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """
    调用 Dify 改写接口，实现文本改写功能。

    Args:
        input_data (TextInput): 包含 text 字段的请求体
        api_key (str): 鉴权用的 API Key
    Returns:
        JSONResponse: 包含改写后文本的 JSON
    """
    try:
        rewritten_text = await run_in_threadpool(call_dify_rewrite, query_text=input_data.text)
        return JSONResponse(content={"rewritten_text": rewritten_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/expand-text/")
async def expand_text(
    input_data: TextInput,
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """
    调用 Dify 扩写接口，实现文本扩充功能。

    Args:
        input_data (TextInput): 包含 text 字段的请求体
        api_key (str): 鉴权用的 API Key
    Returns:
        JSONResponse: 包含扩写后文本的 JSON
    """
    try:
        expanded_text = await run_in_threadpool(call_dify_expand, query_text=input_data.text)
        return JSONResponse(content={"expanded_text": expanded_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/contract-text/")
async def contract_text(
    input_data: TextInput,
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """
    调用 Dify 缩写接口，实现文本压缩功能。

    Args:
        input_data (TextInput): 包含 text 字段的请求体
        api_key (str): 鉴权用的 API Key
    Returns:
        JSONResponse: 包含缩写后文本的 JSON
    """
    try:
        contracted_text = await run_in_threadpool(call_dify_contract, query_text=input_data.text)
        return JSONResponse(content={"contracted_text": contracted_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

@app.post("/process_json_to_text/")
async def process_json_to_text(
    input_data: Dict[str, Any],
    api_key: str = Depends(get_api_key)
) -> JSONResponse:
    """
    将任意 JSON 转为文本，并调用 Dify 文本处理接口。

    Args:
        input_data (Dict[str, Any]): 任意 JSON 对象
        api_key (str): 鉴权用的 API Key
    Returns:
        JSONResponse: 包含处理后文本的 JSON
    """
    try:
        json_as_text = json.dumps(input_data, indent=2, ensure_ascii=False)
        print(f"--- Start of Text ---\n{json_as_text}\n--- End of Text ---")
        response_text = await run_in_threadpool(call_dify_process_text, query_text=json_as_text)
        return JSONResponse(content={"processed_text": response_text})
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"An internal error occurred: {str(e)}")