# @app.route('/bucket', methods=['POST'])
# def bucket():

#     print('request.method')
#     print(request.method)
#     path = pathlib.Path(__file__).parent.resolve()
#     print(path)
#     result = hellopy.hello_world()

#     s3 = boto3.resource('s3',
#                         aws_access_key_id='AKIAUCXTXAAIXQCVARSC',
#                         aws_secret_access_key='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',
#                         region_name='eu-west-2'
#                         )

#     print(s3)

#     for bucket in s3.buckets.all():
#         print(bucket.name)

#     return jsonify({'message': result}), 200
