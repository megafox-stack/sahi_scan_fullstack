import requests
from PIL import Image, ImageDraw, ImageFont
import io

BASE='http://127.0.0.1:8000/api/v1'

# create sample image
img=Image.new('RGB',(800,400),color='white')
d=ImageDraw.Draw(img)
try:
    f=ImageFont.truetype('arial.ttf',28)
except:
    f=None
text='SAMPLE FOOD LABEL\nIngredients: Sugar, Salt, Wheat\nNutrition per 100g: Energy 400 kcal, Sugar 10g'
d.multiline_text((20,20),text,fill='black',font=f,spacing=6)
img_path='backend/tests/uploads/sample_label.png'
img.save(img_path)
print('Wrote',img_path)

# register user
reg = requests.post(BASE+'/auth/register', json={'email':'e2e@test.local','password':'Test12345!','name':'E2E Tester'})
if reg.status_code in (200,201):
    token = reg.json()['access_token']
    print('Registered, token len', len(token))
else:
    print('Register failed', reg.status_code, reg.text)
    # try login
    lg = requests.post(BASE+'/auth/login', json={'email':'e2e@test.local','password':'Test12345!'})
    if lg.status_code!=200:
        print('Login failed', lg.status_code, lg.text)
        raise SystemExit(1)
    token = lg.json()['access_token']
    print('Logged in, token len', len(token))
    headers={'Authorization':f'Bearer {token}'}
    # get profiles
    profiles = requests.get(BASE+'/profiles', headers=headers).json()
    profile_id = profiles[0]['id'] if profiles else None
    print('Profiles:', profiles)
    # upload image
    files={'file': ('sample_label.png', open(img_path,'rb'), 'image/png')}
    data={'profile_id': profile_id} if profile_id else {}
    resp = requests.post(BASE+'/scans/image', headers=headers, files=files, data=data)
    print('Upload status', resp.status_code)
    try:
        print(resp.json())
    except Exception as e:
        print(resp.text)
