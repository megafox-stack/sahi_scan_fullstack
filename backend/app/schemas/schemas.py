from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
class AuthRegister(BaseModel): email:str; password:str=Field(min_length=8); name:str=Field(min_length=1,max_length=120)
class AuthLogin(BaseModel): email:str; password:str
class Token(BaseModel): access_token:str; token_type:str="bearer"
class ProfileCreate(BaseModel): name:str; profile_type:str="Custom"; icon:str="👤"; sodium_mg:float|None=600; sugar_g:float|None=10; preferences:dict={}
class ProfileOut(ProfileCreate): id:int; model_config=ConfigDict(from_attributes=True)
class ProductOut(BaseModel): id:int; barcode:str; name:str; brand:str; category:str; manufacturer:str; fssai:str; image:str; nutrition:dict; ingredients:list[dict]
class ScanRequest(BaseModel): barcode:str; profile_id:int|None=None
class ScanOut(BaseModel): id:int; created_at:datetime; sahi_score:float|None; status:str; verdict:str; reason:str; product:ProductOut|None; profile_id:int|None
class ChatRequest(BaseModel): message:str; language:str="EN"; profile_id:int|None=None; scan_id:int|None=None
class QualityReportCreate(BaseModel): product_id:int|None=None; report_type:str; details:str|None=None; image_path:str|None=None
class QualityReportOut(QualityReportCreate): id:int; created_at:datetime; model_config=ConfigDict(from_attributes=True)
