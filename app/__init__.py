from flask import Flask, request, redirect
from uuid import uuid4
import boto3, os


app = Flask(__name__)
app.config['AWS_ACCESS'] = os.environ.get('AWS_ACCESS_KEY')
app.config['AWS_SECRET_KEY'] = os.environ.get('AWS_SECRET_KEY')
app.config['S3_UPLOAD_DIR'] = 'psty'
app.config['S3_BUCKET_NAME'] = 'mbcdn'
app.config['BASE_URL'] = 'https://up.psty.io'

boto3s = boto3.session.Session()
client = boto3s.client('s3', region_name='sfo2', endpoint_url='https://sfo2.digitaloceanspaces.com',
                       aws_access_key_id=app.config['AWS_ACCESS'], aws_secret_access_key=app.config['AWS_SECRET_KEY'])

def upload_file(filename):
    try:
        client.upload_file(f'tmp/{filename}', app.config['S3_BUCKET_NAME'], '{}/{}'.format(app.config['S3_UPLOAD_DIR'], filename))
        return True, 'Success'
    except Exception as e:
        return False, e
    
def gen_uid():
    uid_base = str(uuid4()).split('-')[0]
    return str(uid_base[0:3])
    
@app.route('/<filename>', methods=['PUT'])
def upload(filename):
    base_url = app.config['BASE_URL']
    file = request.data
    uid = gen_uid()
    with open(f'tmp/{uid}_{filename}', 'wb') as sfile:
        sfile.write(file)
    result, msg = upload_file(str(uid + '_' + filename))
    os.remove(f'tmp/{uid}_{filename}')
    if result:
        return f'''
   ▄▄▄▄▄   ▄   ▄█▄    ▄█▄    ▄███▄     ▄▄▄▄▄    ▄▄▄▄▄   
  █     ▀▄  █  █▀ ▀▄  █▀ ▀▄  █▀   ▀   █     ▀▄ █     ▀▄ 
▄  ▀▀▀▀▄ █   █ █   ▀  █   ▀  ██▄▄   ▄  ▀▀▀▀▄ ▄  ▀▀▀▀▄   
 ▀▄▄▄▄▀  █   █ █▄  ▄▀ █▄  ▄▀ █▄   ▄▀ ▀▄▄▄▄▀   ▀▄▄▄▄▀    
         █▄ ▄█ ▀███▀  ▀███▀  ▀███▀                      
          ▀▀▀                                           

File Available At: {base_url}/{uid}/{filename}'''
    else:
        return f'''
  ▄    ▄  █ ████▄  ▄  █ 
   █  █   █ █   █ █   █ 
█   █ ██▀▀█ █   █ ██▀▀█ 
█   █ █   █ ▀████ █   █ 
█▄ ▄█    █           █  
 ▀▀▀    ▀           ▀   

Something went wrong when trying to upload your file!
Error: {msg}'''
    
@app.route('/<uid>/<filename>', methods=['GET'])
def send(uid, filename):
    upload_dir = app.config['S3_UPLOAD_DIR']
    url = client.generate_presigned_url(ClientMethod="get_object",
                                        Params={'Bucket': 'mbcdn',
                                                'Key': f'{upload_dir}/{uid}_{filename}',
                                                'ResponseContentDisposition': f'attachment; filename = {filename}'})
    return redirect(url, 302)