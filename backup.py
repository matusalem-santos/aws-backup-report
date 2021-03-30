#!/usr/bin/python3

import boto3
import json
import sys
from datetime import datetime
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

now = datetime.now().strftime('%d/%m/%y')
today = datetime.strptime(now, '%d/%m/%y')
region = "sa-east-1"


backup = boto3.client('backup',aws_access_key_id=sys.argv[1],
    aws_secret_access_key=sys.argv[2], region_name=region)

backups = backup.list_backup_jobs(
    ByCreatedAfter= today
)
jobs = []
instances= []
for job in backups["BackupJobs"]:
    if job["ResourceType"] == "EC2":
        #print(json.dumps(job, indent=2,default=str))
        instance_id = job["ResourceArn"].split("/")[1]
        status = job["State"]
        create_date= job["CreationDate"].strftime('%d/%m/%y')
        create_hour= job["CreationDate"].strftime('%H:%M')
        completion_hour= job["CompletionDate"].strftime('%H:%M')
        exe_time = job["CompletionDate"] - job["CreationDate"]
        exe_time = str(exe_time).split(".")[0]
        if instance_id not in instances:
            jobs.append({"instance_id": instance_id, "status": status, "create_date": create_date, "create_hour":create_hour, "completion_hour":completion_hour, "exe_time": exe_time})
            instances.append(instance_id)
        
    #print(volume_id)
#print(json.dumps(backups, indent=2, default=str))

ec2 = boto3.client('ec2',aws_access_key_id=sys.argv[1],
    aws_secret_access_key=sys.argv[2], region_name=region)

for i, job in enumerate(jobs):
    instance = ec2.describe_instances(
        InstanceIds= [job['instance_id']]
    )
    instance_ip= instance["Reservations"][0]["Instances"][0]["PrivateIpAddress"]
    for name in instance["Reservations"][0]["Instances"][0]["Tags"]:
        if name["Key"] == "Name":
            instance_name = name["Value"]
    jobs[i]["instance_name"] = instance_name
    jobs[i]["instance_ip"] = instance_ip
    #print(json.dumps(instance, indent=2, default=str))
    #print(json.dumps(volumes, indent=2, default=str))
#print(json.dumps(jobs, indent=2, default=str))

text = """\
Hi
"""
html1= """\
<!DOCTYPE html>
<html>
<head>
<style>
table {
font-family: arial, sans-serif;
border-collapse: collapse;
width: 100%;
}

td, th {
border: 1px solid #dddddd;
text-align: left;
padding: 8px;
}

tr:nth-child(even) {
background-color: #dddddd;
}
</style>
"""
# write the HTML part
html2 = """\
</head>
<body>

<p>Prezados, bom dia! </p>
</br>
<p>Segue report dos backups das instâncias em {0}</p>
"""

now = datetime.now().strftime('%d/%m/%y')
html2 = html2.format(now)
html3 = """\
<table>
<tr bgcolor="GREEN"; border: 1px solid black>
    <th><img src="cid:image" width="50" height="50"></th>
    <th>IP APLICAÇÃO</th>
    <th>HOSTNAME APLICAÇÃO</th>
    <th>ID APLICAÇÃO</th>
    <th>DIA DO ULTIMO BACKUP</th>
    <th>HORA DE INICIO DO BACKUP</th>
    <th>HORA DE FINALIZAÇÃO DO BACKUP</th>
    <th>TEMPO DE EXECUÇÃO DO BACKUP</th>
    <th>STATUS DO ULTIMO BACKUP</th>
"""
html_total = html1+html2+html3
count = 1 
for job in jobs:
    html_td="""\
    </tr>
    <tr>
        <td>{8}</td>
        <td>{0}</td>
        <td>{1}</td>
        <td>{2}</td>
        <td>{3}</td>
        <td>{4}</td>
        <td>{5}</td>
        <td>{9}</td>
        <td bgcolor="{7}">{6}</td>
    """
    if job["status"] == "COMPLETED":
        html_td = html_td.format(job["instance_ip"],job["instance_name"], job["instance_id"], job["create_date"], job["create_hour"],job["completion_hour"], job["status"],"GREEN",count,job["exe_time"]) 
    else:
        html_td = html_td.format(job["instance_ip"],job["instance_name"], job["instance_id"], job["create_date"], job["create_hour"],job["completion_hour"], job["status"],"RED",count,job["exe_time"]) 

    html_total +=html_td
    count +=1
html_fim = """\
</tr>
</table>
</body>
</html>
"""
html_total += html_fim 

fp = open('logo.png', 'rb')
msgImage = MIMEImage(fp.read())
fp.close()
msgImage.add_header('Content-ID', '<image>')


sender_email = ""
receiver_emails = [""]
message = MIMEMultipart("alternative")
message["Subject"] = "Relatório de backup das instâncias"
message["From"] = sender_email
message["To"] = ', '.join(receiver_emails)
# write the plain text part

# convert both parts to MIMEText objects and add them to the MIMEMultipart message
part1 = MIMEText(text, "plain")
part2 = MIMEText(html_total, "html")
message.attach(part1)
message.attach(part2)
message.attach(msgImage)

client = boto3.client(
    'ses',
    region_name=region,
    aws_access_key_id=sys.argv[1],
    aws_secret_access_key=sys.argv[2]
)

response = client.send_raw_email(
    Source=message['From'],
    Destinations=receiver_emails,
    RawMessage={
        'Data': message.as_string()
    }
)

print('Sent') 
