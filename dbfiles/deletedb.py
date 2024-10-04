import boto3

# Create a DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-west-1')

# Get a list of all tables
tables = dynamodb.tables.all()

# Iterate through each table
for table in tables:
    print(f"Processing Table: {table.table_name}")

    # Create a table resource
    table_resource = dynamodb.Table(table.table_name)

    # Scan the table
    response = table_resource.scan()

    # Delete each item
    for item in response['Items']:
        # Get the primary keys for this table
        primary_keys = [key_schema['AttributeName'] for key_schema in table.key_schema]

        # Create a dictionary of primary key element(s)
        key = {pk: item[pk] for pk in primary_keys}

        print(f"Deleting item: {key}")
        table_resource.delete_item(Key=key)

    print("\n\n")  # print new lines for readability
