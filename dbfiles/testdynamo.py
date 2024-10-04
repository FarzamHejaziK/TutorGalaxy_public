import boto3

# Create a DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')

# Print out each DynamoDB table name
try:
    tables = dynamodb.tables.all()
    for table in tables:
        print(table.table_name)
except Exception as e:
    print("Error occurred:", e)
