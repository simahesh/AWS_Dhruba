from flask import Flask, redirect, url_for, request, jsonify,render_template
import boto3
from botocore.exceptions import ClientError, ParamValidationError

app = Flask(__name__)
iam = boto3.client('iam')

@app.route('/ListUser')
def ListUser():
    try:
        allusers=iam.list_users()
        listusers=[]
        for temp in allusers['Users']:
            listusers.append(temp['UserName'])
        return jsonify(listusers)
    except Exception as e:
        return str(e)

@app.route('/CreateUser/<name>')
def CreateUser(name):
    try:
        response = iam.create_user(UserName=name)
        print (response)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return "Successfully created User: {}".format(name)
        else:
            return "Could not create user({}), got response code: {}".format(name,response['ResponseMetadata']['HTTPStatusCode'])
    except Exception as e:
        return str(e)

@app.route('/DeleteUser/<name>')
def DeleteUser(name):
    try:
        response = iam.delete_user(UserName=name)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return "Successfully deleted User: {}".format(name)
        else:
            return "Could not delete user({}), got response code: {}".format(name,response['ResponseMetadata']['HTTPStatusCode'])
    except ClientError as e:
        if 'cannot be found' in e.response['Error']['Message']:
            return str(e)
        elif 'delete login profile first' in e.response['Error']['Message']:
            response = iam.delete_login_profile(UserName=name)
        elif 'detach all policies first' in e.response['Error']['Message']:
            response = iam.get_account_authorization_details( Filter=['User'])
            for temp in response['UserDetailList']:
                if temp['UserName'] == name:
                    for temp2 in temp['AttachedManagedPolicies']:
                        response = iam.detach_user_policy(UserName=name,PolicyArn=temp2['PolicyArn'])
                    break
        elif 'delete policies first' in e.response['Error']['Message']:
            response = iam.list_user_policies(UserName=name)
            for temp in response['PolicyNames']:
                response = iam.delete_user_policy(UserName=name,PolicyName=temp)
        elif 'remove users from group first' in e.response['Error']['Message']:
             response = iam.list_groups_for_user(UserName=name)
             for temp in response['Groups']:
                 response2 = iam.remove_user_from_group(GroupName=temp['GroupName'],UserName=name)
        elif 'delete access keys first' in e.response['Error']['Message']:
             response = iam.list_access_keys(UserName=name)
             for temp in response['AccessKeyMetadata']:
                 response = iam.delete_access_key(UserName=name,AccessKeyId=temp['AccessKeyId'])
        elif 'delete MFA device first' in e.response['Error']['Message']:
             response = iam.list_mfa_devices(UserName=name)
             for temp in response['MFADevices']:
                 response = iam.deactivate_mfa_device(UserName=name,SerialNumber=temp['SerialNumber'])
        else:
            return str(e)
        return redirect(url_for('DeleteUser',name=name))
    except Exception as e:
        return str(e)

@app.route('/')
def admin2():
    return render_template('admin.html')

@app.route('/admin',methods = ['POST', 'GET'])
def admin():
   if request.method == 'POST':
       if request.form['submit_button'] == 'List User':
           return redirect(url_for('ListUser'))
       elif request.form['submit_button'] == 'Create User':
           name = request.form['name']
           return redirect(url_for('CreateUser',name=name))
       elif request.form['submit_button'] == 'Delete User':
           name = request.form['name']
           return redirect(url_for('DeleteUser',name=name))
       else:
           return "Cancelled user delete request"
   else:
      return 'PageNotFound'

if __name__ == '__main__':
   app.run(host='0.0.0.0', port=5050,debug = True)
