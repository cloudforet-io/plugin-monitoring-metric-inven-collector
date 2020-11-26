# plugin-aws-power-state

Plugin for AWS Power State
- Collecting Instance State
- Collecting RDS Instance State
- Collecting Auto Scaling Group State

# Data Sample

## EC2

~~~
"data": {
	"compute": {
		"instance_state": "RUNNING",
			...
		},
	"power_state": {
		"instance_state": "passed",
		"system_state": "passed"
	},

	....
		
}
~~~

## Auto Scaling Group

- cloud_service_type: AutoScalingGroup
- cloud_service_group: AutoScaling
- provider: aws

~~~
'data': {
	'auto_scaling_group_arn': 'arn:aws:autoscaling:ap-northeast-2:257706363616:autoScalingGroup:0c9774b0-c96a-4cea-9326-e1f3acfd6eec:autoScalingGroupName/eks-c2b977fd-fb2c-2e2f-fbac-f9ea109b1d89',
	'auto_scaling_group_name': 'eks-c2b977fd-fb2c-2e2f-fbac-f9ea109b1d89',
	'desired_capacity': 8.0,
	'max_size': 10.0,
	'min_size': 8.0
	...
	},

~~~

## RDS

- cloud_service_type: Database
- cloud_service_group: RDS
- provider: aws

~~~
'data': {
	'arn': 'arn:aws:rds:us-east-1:257706363616:db:terraform-20200811083041083200000001',
        'db_identifier': 'terraform-20200811083041083200000001',
	'role': 'instance',
	'status': 'stopping'
	...
	}
~~~

