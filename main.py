import boto3
import requests
import json
from time import sleep
from app import app
from flask import Flask, flash, request, redirect, render_template, url_for, send_from_directory

region_list = ['sa-east-1', 'us-west-2']
role_types = ['public', 'private']
shoutcast_aws_instances = []

for role_type in role_types:
    for region in region_list:
        session = boto3.Session(
            region_name=region
        )

        ec2 = session.resource('ec2')

        sc_instances = ec2.instances.filter(Filters=[{
            'Name': 'tag:shoutcast',
            'Values': [role_type]}])

        for instance in sc_instances:
            for tag in instance.tags:
                if 'Name' in tag['Key']:
                    name = tag['Value']
            # Add instance info to a dictionary
            shoutcast_aws_instances.append({'role': role_type, 'region': region, 'Id': instance.id, 'Name': name, 'Instance_Type': instance.instance_type,
                         'State': instance.state['Name'], 'Public_IP': instance.public_ip_address, 'Launch_Time': instance.launch_time})

print(shoutcast_aws_instances)


@app.route('/')
def dashboard_page():
    report = []
    for sc in shoutcast_aws_instances:
        if sc['State'].lower() == 'running':
            url = f"http://{sc['Public_IP']}:8000/statistics?json=1"
            headers = {
                'Accept': 'application/json'
            }
            stats_resp = requests.request("GET", url, headers=headers, data={})
            stats = json.loads(stats_resp.text)
            # print(stats)
            report.append({'role': sc['role'], 'region': sc['region'], 'id': sc['Id'], 'name': sc['Name'], 'instance_type': sc['Instance_Type'],
                           'state': sc['State'], 'public_ip': sc['Public_IP'], 'launch_time': sc['Launch_Time'],
                           'currentlisteners': stats['currentlisteners'], 'peaklisteners': stats['peaklisteners'],
                           'maxlisteners': stats['maxlisteners'], 'uniquelisteners': stats['uniquelisteners'],
                           'averagetime': stats['averagetime'], 'bitrate': stats['streams'][0]['bitrate']})
        else:
            report.append({'role': sc['role'], 'region': sc['region'], 'id': sc['Id'], 'name': sc['Name'], 'instance_type': sc['Instance_Type'],
                           'state': sc['State'], 'public_ip': '0.0.0.0', 'launch_time': 'n/a',
                           'currentlisteners': 0, 'peaklisteners': 0,
                           'maxlisteners': 0, 'uniquelisteners': 0,
                           'averagetime': 0, 'bitrate': 0})

    #report = [{'region': 'sa-east-1', 'name': 'i-what', 'currentlisteners': 400, 'peaklisteners': 702, 'maxlisteners': 1000, 'uniquelisteners': 299,'averagetime':'77', 'bitrate': '33', 'public_ip': '3.3.3.3', 'id': 'theone', 'type': 't2.small', 'state': 'running'},
    #           {'region': 'sa-east-1', 'name': 'i-what', 'currentlisteners': 309, 'peaklisteners': 444, 'maxlisteners': 1000, 'uniquelisteners': 301,'averagetime':'77', 'bitrate': '33', 'public_ip': '3.3.3.3', 'id': 'theone', 'type': 't2.small', 'state': 'running'}]
    total_current_listeners = 0
    total_peak_listeners = 0
    total_max_listeners = 0
    total_unique_listeners = 0

    for sc_record in report:
        total_current_listeners += sc_record['currentlisteners']
        total_peak_listeners += sc_record['peaklisteners']
        total_max_listeners += sc_record['maxlisteners']
        total_unique_listeners += sc_record['uniquelisteners']

    print(report)
    return render_template('dashboard.html', report=report, total_current_listeners=total_current_listeners, total_peak_listeners=total_peak_listeners, total_max_listeners=total_max_listeners, total_unique_listeners=total_unique_listeners)


if __name__ == "__main__":
    app.run()

