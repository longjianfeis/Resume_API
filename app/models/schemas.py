# from pydantic import BaseModel, Field
# from typing import Optional, List, Dict, Any
#
# # --- 通用输入模型 ---
# class TextInput(BaseModel):
#     text: str = Field(..., min_length=1)
#
# # --- 简历生成相关的结构化模型 (已更新为更宽松的验证规则) ---
# class ContactInfo(BaseModel):
#     phone: Optional[str] = None
#     email: Optional[str] = None
#
# class EducationItem(BaseModel):
#     user_university: Optional[str] = None
#     user_major: Optional[str] = None
#     degree: Optional[str] = None
#     dates: Optional[str] = None
#     details: Optional[str] = None
#     user_grade: Optional[str] = None
#     user_graduate_year: Optional[str] = None
#     user_gpa: Optional[str] = None
#     user_language_score: Optional[str] = None
#
# class ExperienceItem(BaseModel):
#     company: Optional[str] = None
#     role: Optional[str] = None
#     location: Optional[str] = None
#     dates: Optional[str] = None
#     description_points: Optional[List[str]] = []
#
# # [FIXED] 字段名从 'research project' 改为 'research_project' 并设为可选
# class ResearchItem(BaseModel):
#     research_project: Optional[str] = None
#     role: Optional[str] = None
#     location: Optional[str] = None
#     dates: Optional[str] = None
#     description_points: Optional[List[str]] = []
#
# class ActivityItem(BaseModel):
#     organization: Optional[str] = None
#     role: Optional[str] = None
#     location: Optional[str] = None
#     dates: Optional[str] = None
#     description_points: Optional[List[str]] = []
#
# # 统一的简历数据模型
# class NewResumeProfile(BaseModel):
#     user_uid: str
#     user_name: str
#     user_contact_info: Optional[ContactInfo] = None
#     user_education: Optional[List[EducationItem]] = []
#     internship_experience: Optional[List[ExperienceItem]] = []
#     user_research_experience: Optional[List[ResearchItem]] = []
#     user_extracurricular_activities: Optional[List[ActivityItem]] = []
#     user_target: Optional[str] = None

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

# --- 通用输入模型 ---
class TextInput(BaseModel):
    text: str = Field(..., min_length=1)

# 新增：用于接收文本和Prompt的模型
class PromptTextInput(BaseModel):
    text: str
    prompt: str

# --- 简历生成相关的结构化模型 ---
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
    research_project: str = Field(..., alias='research project')
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

# 统一的简历数据模型
class NewResumeProfile(BaseModel):
    user_uid: str
    user_name: str
    user_contact_info: ContactInfo
    user_education: List[EducationItem]
    internship_experience: List[ExperienceItem]
    user_research_experience: Optional[List[ResearchItem]] = []
    user_extracurricular_activities: Optional[List[ActivityItem]] = []
    user_target: Optional[str] = None