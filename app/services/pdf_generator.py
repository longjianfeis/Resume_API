import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from app.models.schemas import NewResumeProfile

# 定义模板文件夹的路径 (相对于项目根目录)
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
jinja_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

def create_resume_pdf(profile: NewResumeProfile) -> bytes:
    """
    根据简历数据生成PDF文件的二进制内容。
    """
    try:
        profile_data = profile.model_dump(by_alias=True)
        
        # 根据style字段选择模板（如果未来需要）
        # 目前固定使用 resume_template.html
        resume_template = jinja_env.get_template("resume_template.html")
        css_file_path = os.path.join(TEMPLATE_DIR, 'style.css')
        
        rendered_html = resume_template.render(profile_data)
        
        css = CSS(filename=css_file_path)
        pdf_bytes = HTML(string=rendered_html, base_url=TEMPLATE_DIR).write_pdf(stylesheets=[css])
        
        return pdf_bytes
    except Exception as e:
        # 可以在这里添加更详细的日志记录
        print(f"PDF generation failed: {e}")
        raise
