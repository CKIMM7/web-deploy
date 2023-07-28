import os
from flask import Blueprint, jsonify, request
from db import conn
from models import User
import boto3
from db import conn, insert_user, update_user_iam

admin_aws_access_key_id = os.getenv('admin_aws_access_key_id')
admin_aws_secret_access_key = os.getenv('admin_aws_secret_access_key')

beanstalk = Blueprint('beanstalk', __name__)


@beanstalk.route('/beanstalk/environment', methods=['POST'])
def create_env():
    elasticbeanstalk = boto3.client('elasticbeanstalk',
                                    aws_access_key_id=admin_aws_access_key_id,
                                    aws_secret_access_key=admin_aws_secret_access_key,
                                    region_name='eu-west-2')

    response = elasticbeanstalk.create_environment(
        ApplicationName='nodejs_boto3test',
        EnvironmentName='nodejs_boto3test-env',
        Tier={
            'Name': 'WebServer',
            'Type': 'Standard'
        },
        SolutionStackName='64bit Amazon Linux 2016.03 v2.1.1 running Node.js',
        OptionSettings=[
            {
                'Namespace': 'aws:ec2:vpc',
                'OptionName': 'VPCId',
                'Value': 'vpc-07717270cbf9b79b6'
            },
            {
                'Namespace': 'aws:ec2:vpc',
                'OptionName': 'ELBSubnets',
                'Value': 'subnet-069b11dc1a760fef1,subnet-0da6c93eab8ab1e7f,subnet-01f9f26f285f8a549'
            },
        ]
    )
