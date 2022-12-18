from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug import exceptions
from subprocess import Popen
import pathlib
import hellopy
import boto3

ec2 = boto3.resource('ec2')
app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def home():

    print('request.method')
    print(request.method)
    pathlib.Path(__file__).parent.resolve()
    return jsonify({'message': 'Hello from Flask!'}), 200

@app.route('/bucket', methods=['POST'])
def bucket():

    print('request.method')
    print(request.method)
    path =  pathlib.Path(__file__).parent.resolve()
    print(path)
    result = hellopy.hello_world()

    s3 = boto3.resource('s3',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2'
         )

    print(s3)

    for bucket in s3.buckets.all():
        print(bucket.name)

    # s3 = boto3.resource('s3')
    # for bucket in s3.buckets.all():
    #     print(bucket.name)

    # instances = ec2.create_instances(
    #         ImageId="ami-0b0ea68c435eb488",
    #         MinCount=1,
    #         MaxCount=1,
    #         InstanceType="t2.micro",
    #         KeyName="KeyPair1"
    #     )

    # print(instances)

    # p = Popen("hello.bat", cwd=path)
    # stdout, stderr = p.communicate()

    # print(stdout)
    # print(stderr)

    return jsonify({'message': result}), 200

@app.route('/ec2', methods=['POST'])
def ec():

    print('request.method')
    print(request.method)
    path =  pathlib.Path(__file__).parent.resolve()
    print(path)
    result = hellopy.hello_world()

    ec2 = boto3.resource('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2'
         )

    print(ec2)

    instance = ec2.create_instances(
            ImageId="ami-084e8c05825742534",
            MinCount=1,
            MaxCount=1,
            InstanceType="t2.micro",
            KeyName="KeyPair1"
        )

    print(instance)

    return jsonify({'message': result}), 200

@app.route('/ec2/instances', methods=['GET'])
def ec_view_instances():

    result = hellopy.hello_world()
    ec2 = boto3.resource('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2')
    
    for instance in ec2.instances.all():
        print(instance)

    return jsonify({'message': result}), 200


@app.route('/ec2/instance/stop', methods=['POST'])
def ec_stop_instances():

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2')
    
    response = ec2.stop_instances(
        InstanceIds=[
            'i-0b26f473cc31c5104',
        ],
        Hibernate=False,
        DryRun=False,
        Force=False
    )

    print(response)

    return jsonify({'message': result}), 200

@app.route('/ec2/instance/start', methods=['POST'])
def ec_start_instances():

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2')
    
    response = ec2.start_instances(
        InstanceIds=[
            'i-0b26f473cc31c5104',
        ],
        AdditionalInfo='string',
        DryRun=False
    )

    print(response)
    
    return jsonify({'message': result}), 200


@app.route('/ec2/instance/terminate', methods=['POST'])
def ec_terminate_instances():

    result = hellopy.hello_world()
    ec2 = boto3.client('ec2',
         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
         aws_secret_access_key='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',
         region_name='eu-west-2')
         
    response = ec2.terminate_instances(
            InstanceIds=[
            'i-0b26f473cc31c5104',
        ],
    )
    print(response)
    return jsonify({'message': result}), 200

@app.route('/iam/new', methods=['POST'])
def iam_new_user():

    result = hellopy.hello_world()

    iam = boto3.client('iam',
         aws_access_key_id='AKIAUCXTXAAI4YYSLVRR',
         aws_secret_access_key='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',
         region_name='eu-west-2')

    response = iam.create_user(
    UserName='student7'
    )

    print(response['User'])

    if response['User']['UserId']:
        print(response['User']['UserId'])

        response = iam.add_user_to_group(
            GroupName='student',
            UserName=response['User']['UserName'],
        )

    return jsonify({'message': result}), 200

if __name__ == "__main__":
    app.run(debug=True)
