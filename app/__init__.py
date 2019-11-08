from flask import Flask, request, redirect
from uuid import uuid4
import boto3, os, json


app = Flask(__name__)
with open('.config.json', 'r+') as jsonf:
    conf = json.load(jsonf)
    app.config['AWS_ACCESS'] = conf['AWS_ACCESS_KEY']
    app.config['AWS_SECRET_KEY'] = conf['AWS_SECRET_KEY']
app.config['S3_UPLOAD_DIR'] = 'psty'
app.config['S3_BUCKET_NAME'] = 'mbcdn'
app.config['BASE_URL'] = 'https://up.psty.io'

boto3s = boto3.session.Session()
client = boto3s.client('s3', region_name='sfo2', endpoint_url='https://sfo2.digitaloceanspaces.com',
                       aws_access_key_id=app.config['AWS_ACCESS'], aws_secret_access_key=app.config['AWS_SECRET_KEY'])

@app.errorhandler(500)
def error(e):
    return '''
  __  ____       ____  __ 
 / / / / /  ____/ __ \\/ / 
/ /_/ / _ \\/___/ /_/ / _ \\
\\____/_//_/    \\____/_//_/
                          
Something went wrong!'''

def upload_file(filename):
    try:
        client.upload_file('tmp/{filename}'.format(filename=filename), app.config['S3_BUCKET_NAME'], '{}/{}'.format(app.config['S3_UPLOAD_DIR'], filename), ExtraArgs={'ACL':'public-read'})
        return True, 'Success'
    except Exception as e:
        return False, e
    
def gen_uid():
    uid_base = str(uuid4()).split('-')[0]
    return str(uid_base[0:3])

@app.route('/')
def redir():
    return redirect('https://psty.io', 302)
    
@app.route('/<filename>', methods=['PUT'])
def upload(filename):
    file = request.data
    uid = gen_uid()
    with open('tmp/{uid}_{filename}'.format(uid=uid, filename=filename), 'wb') as sfile:
        sfile.write(file)
    result, msg = upload_file(str(uid + '_' + filename))
    os.remove('tmp/{uid}_{filename}'.format(uid=uid, filename=filename))
    if result:
        return '''
   ____                       
  / __/_ _____________ ___ ___
 _\\ \\/ // / __/ __/ -_|_-<(_-<
/___/\\_,_/\\__/\\__/\\__/___/___/
                              
File Available At: {base_url}/{uid}/{filename}'''.format(base_url=app.config['BASE_URL'], uid=uid, filename=filename)
    else:
        return '''
  __  ____       ____  __ 
 / / / / /  ____/ __ \\/ / 
/ /_/ / _ \\/___/ /_/ / _ \\
\\____/_//_/    \\____/_//_/
                          
Something went wrong when trying to upload your file!
Error: {msg}'''.format(msg=msg)
    
@app.route('/<uid>/<filename>', methods=['GET'])
def send(uid, filename):
    url = client.generate_presigned_url(ClientMethod="get_object",
                                        Params={'Bucket': 'mbcdn',
                                                'Key': 'psty/{uid}_{filename}'.format(uid=uid, filename=filename),
                                                'ResponseContentDisposition': 'attachment; filename = {filename}'.format(filename=filename)})
    return redirect(url, 302)