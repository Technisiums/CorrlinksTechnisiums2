from .models import Account, VPS, APIKey, Customer, SMSCustomer, CorrlinksToSMS, SMSToCorrlinks, Image, SystemToCorrlinks
from .serializers import AccountSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json
from django.db.models import Q
from bandwidth.bandwidth_client import BandwidthClient
from bandwidth.messaging.models.message_request import MessageRequest
import os
from django.core.files import File
from time import sleep
import datetime
from .GoogleDriveManager import GoogleDrive
from django.conf import settings

MESSAGING_API_TOKEN = '2cca4a33c5a73d03f70c08d3a940fee867f57948b0d32936'
MESSAGING_API_SECRET = '1a5b70ca7a1aa0919ea33f87c48f9a327e7d0ef1a1430d18'
MESSAGING_APPLICATION_ID = '4895a45b-d5e6-4be1-a664-c3abfd26ae61'
MESSAGING_ACCOUNT_ID = '5004082'


class GetAccounts(APIView):

    def post(self, request):
        try:
            apikey = request.data['apikey']
            APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            vps = request.data['vps']
            vps = VPS.objects.get(VPS_Name=vps)
        except Exception as e:
            return Response(data={'error': 'VPS is not found ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        queryset = Account.objects.filter(VPS=vps.id)
        serializer = AccountSerializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)


class ABC(APIView):
    def get(self, request):
        return Response(data={'a': 'aa'}, status=status.HTTP_200_OK)


class PostCorrlinksToSMS(APIView):

    def post(self, request):
        try:
            apikey = request.data['apikey']
            APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            corrid = request.data['_from']
            inmate = Customer.objects.get(corrlinks_ID=corrid)
            if inmate.status!='act':
                print("Account is blocked")
                new = SystemToCorrlinks(subject='Sorry', body="Your account is due and the message cannot be processed, please have your people visit call4pennies.com to reactivate. Thanks", customer=inmate)
                new.save()

        except Exception as e:
            return Response(data={'error': 'Corrlink ID is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            relative = str(request.data['to']).lower()
            relative = SMSCustomer.objects.filter(corrlinks_Customer=inmate, name=relative)[0]
        except:
            try:
                relative = validate_phone(relative)
                relative = SMSCustomer.objects.filter(corrlinks_Customer=inmate, phone_Number=relative)[0]
            except:
                smsc = SMSCustomer(corrlinks_Customer=inmate, name=relative, phone_Number=relative)
                smsc.clean()
                smsc.save()
                relative = smsc
            # return Response(data={'error': 'name ID is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            body = request.data['body']
        except Exception as e:
            return Response(data={'error': 'Body is Required ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if inmate.status!='act':
                body = str(inmate)+ " was trying to message you but the account is due. To reactivate visit https://www.call4pennies.com/"
                sms = CorrlinksToSMS(_from=inmate, to=relative, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(inmate.phone_Number, relative.phone_Number,
                                                      inmate.allow_International_messages, body)
            else:
                sms = CorrlinksToSMS(_from=inmate, to=relative, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(inmate.phone_Number, relative.phone_Number,
                                                      inmate.allow_International_messages, body)
            emsg = str(emsg)
            # print("Here",emsg)
            if resp:
                sms.bandwidth_ID = emsg
                sms.save()
            else:
                if emsg == "you can't send message":
                    sms.status = 'dis'
                elif emsg == 'error':
                    sms.status = 'err'
                sms.save()
                return Response(data={'error': emsg}, status=status.HTTP_400_BAD_REQUEST)
            return Response(data={'info': 'all is well'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def validate_phone(phone):
    if len(phone) == 10:
        phone = '+1' + phone
    elif phone[0] == '1':
        phone = '+' + phone
    if phone[0] != '+':
        phone = '+' + phone
    return phone


def validate_number_and_send(from_, phone, inter, body):
    flag = False
    if len(phone) == 10:
        phone = '+1' + phone
        flag = True
    elif phone[0:2] == '+1':
        phone = phone
        flag = True
    elif phone[0] == '1':
        phone = '+' + phone
        flag = True
    if flag:
        return send_message(from_, phone, body)
    elif inter:
        if phone[0] != '+':
            phone = '+' + phone
        return send_message(from_, phone, body)
    else:
        return False, "you can't send message"


def send_message(from_, phone_number, b):
    bandwidth_client = BandwidthClient(messaging_basic_auth_user_name=MESSAGING_API_TOKEN,
                                       messaging_basic_auth_password=MESSAGING_API_SECRET)
    messaging_client = bandwidth_client.messaging_client.client
    body = MessageRequest()
    body.application_id = MESSAGING_APPLICATION_ID
    body.to = phone_number
    body.mfrom = from_
    body.text = b
    try:
        res = messaging_client.create_message(MESSAGING_ACCOUNT_ID, body)
        res = str(res)
        res = res.split('>')[0].replace('<', '').replace('ApiResponse', '').strip()
        res = json.loads(res)
        id = res[0]['id']
        return True, id
    except Exception as e:
        return False, 'error'


class ListenFormBandwith(APIView):
    def post(self, request):
        data = request.data
        data = json.loads(json.dumps(data))
        data = data[0]
        print("after", data)
        if data['type'] == 'message-received':
            from_ = data['message']['from']
            body = data['message']['text']
            to = data['message']['to'][0]
            try:
                media = data['message']['media']
            except:
                media = []
            received_a_new_message(from_, to, body, media)
        if data['type'] == 'message-delivered' or data['type'] == 'message-failed':
            sleep(2)
            id = data['message']['id']
            msg = CorrlinksToSMS.objects.get(bandwidth_ID=id)
            if 'message-failed' == data['type']:
                msg.status = 'err'
            else:
                msg.status = 'snt'
            msg.save()
        return Response(status=status.HTTP_202_ACCEPTED)


def get_media_id_and_filename(media_url):
    split_url = media_url.split("/")
    filename = media_url.split("/")[-1]
    if split_url[-2] == "media":
        return split_url[-1], filename
    else:
        return split_url[-3:], filename


def download_media_from_bandwidth(media_urls):
    bandwidth_client = BandwidthClient(messaging_basic_auth_user_name=MESSAGING_API_TOKEN,
                                       messaging_basic_auth_password=MESSAGING_API_SECRET)
    messaging_client = bandwidth_client.messaging_client.client
    downloaded_media_files = []
    for media_url in media_urls:
        media_id, filename = get_media_id_and_filename(media_url)
        if 'smil' in filename or 'xml' in filename:
            continue
        with open(filename, "wb") as f:
            try:
                downloaded_media = messaging_client.get_media(MESSAGING_ACCOUNT_ID, media_id)
                f.write(downloaded_media.body)
            except Exception as e:
                print("Error while downloading media", e)
        downloaded_media_files.append(filename)
    return downloaded_media_files


def remove_files(files):
    for file_name in files:
        os.remove(file_name)


def received_a_new_message(from_, to, body, media):
    try:
        inmate = Customer.objects.get(phone_Number=to)
    except Exception as e:
        print("Msg Recv, Customer not exists", e)
        return
    try:
        relative = SMSCustomer.objects.get(corrlinks_Customer=inmate, phone_Number=from_)
    except:
        relative = SMSCustomer(corrlinks_Customer=inmate, name=from_, phone_Number=from_)
        relative.clean()
        relative.save()
    sms = SMSToCorrlinks(_from=relative, body=body)
    sms.save()
    if inmate.status!='act':
        sms.status='dis'
        body = """Your message to {name} was not delivered because the account is due. To reactivate visit https://www.call4pennies.com/
                Call4Pennies.com – Talk with your loved one and save money!
                https://www.call4pennies.com
                """
        body = body.format(name=str(inmate))
        sms2 = CorrlinksToSMS(_from=inmate, to=relative, body=body)
        sms2.save()
        resp, emsg = validate_number_and_send(inmate.phone_Number, relative.phone_Number,
                                              True, body)
        if resp:
            sms2.bandwidth_ID = emsg
            sms2.save()
        else:
            if emsg == "you can't send message":
                sms2.status = 'dis'
            elif emsg == 'error':
                sms2.status = 'err'
            sms2.save()
    if len(media) == 0:
        print("media is not provided")
    else:
        print("media urls", media)
        files = download_media_from_bandwidth(media)
        for file in files:
            img = Image(message=sms, image=File(open(file, 'rb')))
            img.save()
        try:
            drive = GoogleDrive()
            drive.open_connection()
            for file in files:
                # img = Image(message=sms, corrCustomer=inmate)
                drive.upload_image(file, inmate.corrlinks_ID)
                # img.save()
                inmate.image_count += 1
                inmate.save()
            drive.close_connection()
        except Exception as e:
            print("Exception123",e)
        remove_files(files)


class SMSToCorrlinksView(APIView):
    def post(self, request):
        try:
            apikey = request.data['apikey']
            APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            vps1 = request.data['vps']
        except Exception as e:
            return Response(data={'error': 'VPS is not found' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            em = str(request.data['email']).lower()
        except Exception as e:
            return Response(data={'error': 'email is not found' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            objects = SMSToCorrlinks.objects.filter(Q(status='new') | Q(status='err'))
            data = dict()
            flag = False
            for obj in objects:
                id = str(obj.id)
                to =obj._from.corrlinks_Customer
                if to.status!='act':
                    obj.status = 'dis'
                    obj.save()
                    continue
                to = str(obj._from.corrlinks_Customer.corrlinks_ID)

                _from = obj._from.name
                body = obj.body
                acc = str(obj._from.corrlinks_Customer.corrlinks_Account.email).lower()
                vps = obj._from.corrlinks_Customer.corrlinks_Account.VPS.VPS_Name
                if vps == vps1 and em == acc:
                    flag = True
                    b = {'id': id, 'to': to, 'from': _from, 'body': body, 'acc': acc}
                    try:
                        data[to].append(b)
                    except:
                        data[to] = [b]
            if flag:
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)


class setSMStoCorrlinksStatus(APIView):
    def post(self, request):
        try:
            apikey = request.data['apikey']
            objs = APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            d = str(request.data['data']).strip(',').split(',')
            for info in d:
                info = info.split(":")
                try:
                    obj = SMSToCorrlinks.objects.get(id=int(info[0]))
                    obj.status = info[1]
                    obj.save()
                except Exception as e:
                    # print(e)
                    pass
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class addPhoneBook(APIView):
    def post(self, request):
        try:
            apikey = request.data['apikey']
            objs = APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            corrid = request.data['_from']
            inmate = Customer.objects.get(corrlinks_ID=corrid)
        except Exception as e:
            return Response(data={'error': 'Corrlink ID is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            body = request.data['body']
        except Exception as e:
            return Response(data={'error': 'Body is Required ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            print(body)
            d = body.replace('\n','NIMRALOVE').replace('\\n','NIMRALOVE')
            d = d.split('NIMRALOVE')
            print(d)
            for i in d:
                i = i.split(':')
                name =i[1].strip().lower()
                phone = i[0].strip()
                smsc = SMSCustomer(corrlinks_Customer=inmate, name=name, phone_Number=phone)
                smsc.clean()
                smsc.save()
                body = "{d} has added you to this message service. You can message now each other on this number."
                body = body.format(d=str(inmate))
                sms = CorrlinksToSMS(_from=inmate, to=smsc, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(inmate.phone_Number, smsc.phone_Number,
                                                      inmate.allow_International_messages, body)
                if resp:
                    sms.bandwidth_ID = emsg
                    sms.save()
                else:
                    if emsg == "you can't send message":
                        sms.status = 'dis'
                    elif emsg == 'error':
                        sms.status = 'err'
                    sms.save()
            return Response(data={'info': 'All is well'}, status=status.HTTP_200_OK)
        except Exception as e:
            SystemToCorrlinks(subject='Phonebook error',
                              body="The contact was not saved because you've used the wrong format. Please send it like this\nPhoneNumber:Name\nexample\n+12323232323:sis\n+100000000:bro\nYou can add multiple Contacts each contact should be on one line. Don't write anything else. Subject of the message must be phonebook.\nThanks",
                              customer=inmate).save()
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class setSystemtoCorrlinksStatus(APIView):
    def post(self, request):
        try:
            apikey = request.data['apikey']
            objs = APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            d = str(request.data['data']).strip(',').split(',')
            # print(d)
            for info in d:
                info = info.split(":")
                try:
                    obj = SystemToCorrlinks.objects.get(id=int(info[0]))
                    obj.status = info[1]
                    obj.save()
                except Exception as e:
                    pass
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response(data={'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SystemToCorrlinksPendingsView(APIView):
    def post(self, request):
        try:
            apikey = request.data['apikey']
            APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            vps1 = request.data['vps']
        except Exception as e:
            return Response(data={'error': 'VPS is not found' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            em = str(request.data['email']).lower()
        except Exception as e:
            return Response(data={'error': 'email is not found' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            objects = SystemToCorrlinks.objects.filter(Q(status='new') | Q(status='err'))
            data = dict()
            flag = False
            for obj in objects:
                id = str(obj.id)
                to = str(obj.customer.corrlinks_ID)
                subject = str(obj.subject)
                body = obj.body
                acc = str(obj.customer.corrlinks_Account.email).lower()
                vps = obj.customer.corrlinks_Account.VPS.VPS_Name
                if vps == vps1 and em == acc:
                    flag = True
                    b = {'id': id, 'to': to, 'subject': subject, 'body': body, 'acc': acc, }
                    try:
                        data[to].append(b)
                    except:
                        data[to] = [b]
            if flag:
                return Response(data=data, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_204_NO_CONTENT)
        except:
            return Response(status=status.HTTP_204_NO_CONTENT)



class RUN_AT_8PM(APIView):
    def check_dues_send_messages(self):
        now = datetime.datetime.now()
        tdays = now + datetime.timedelta(3)
        odays = now + datetime.timedelta(1)
        tdCustomers = Customer.objects.filter(due_Date__year=tdays.year, due_Date__month=tdays.month,
                                              due_Date__day=tdays.day)
        odCustomers = Customer.objects.filter(due_Date__year=odays.year, due_Date__month=odays.month,
                                              due_Date__day=odays.day)

        for td in tdCustomers:
            SystemToCorrlinks(subject='Look Out',
                              body="Your message account will be due in 3 days. Please have your people go to call4pennies.com to reload",
                              customer=td).save()
            smscusts = SMSCustomer.objects.filter(corrlinks_Customer=td)
            for smscust in smscusts:
                body = "The message account of {name} will be due in 3 days. To avoid service interruption visit https://www.call4pennies.com/"
                body = body.format(name=str(td))
                sms = CorrlinksToSMS(_from=td, to=smscust, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(td.phone_Number, smscust.phone_Number,
                                                      True, body)
                if resp:
                    sms.bandwidth_ID = emsg
                    sms.save()
                else:
                    if emsg == "you can't send message":
                        sms.status = 'dis'
                    elif emsg == 'error':
                        sms.status = 'err'
                    sms.save()

        for td in odCustomers:
            SystemToCorrlinks(subject='Look Out',
                              body="Your message account will be due tomorrow. Please have your people go to call4pennies.com to reload",
                              customer=td).save()
            smscusts = SMSCustomer.objects.filter(corrlinks_Customer=td)
            for smscust in smscusts:
                body = """The message account of {name} will be due tomorrow.\n To avoid service interruption visit https://www.call4pennies.com"""
                body = body.format(name=str(td))
                sms = CorrlinksToSMS(_from=td, to=smscust, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(td.phone_Number, smscust.phone_Number,
                                                      True, body)
                if resp:
                    sms.bandwidth_ID = emsg
                    sms.save()
                else:
                    if emsg == "you can't send message":
                        sms.status = 'dis'
                    elif emsg == 'error':
                        sms.status = 'err'
                    sms.save()

    def check_images_send_message(self):
        end = datetime.datetime.now()
        start = datetime.datetime.now() - datetime.timedelta(1)
        msgs = SMSToCorrlinks.objects.filter(createdAt__lte=end, createdAt__gte=start, )
        msgs2 = [x for x in msgs if int(x.get_image_count()) >= 1]
        inmate_dict = {}
        for msg in msgs2:
            try:
                inmate_dict[msg._from.corrlinks_Customer.corrlinks_ID][msg._from.name] += int(msg.get_image_count())
            except:
                try:
                    inmate_dict[msg._from.corrlinks_Customer.corrlinks_ID][msg._from.name] = int(msg.get_image_count())
                except:
                    inmate_dict[msg._from.corrlinks_Customer.corrlinks_ID] = {
                        msg._from.name: int(msg.get_image_count())}
        for inmate, info in inmate_dict.items():
            inmateobj = Customer.objects.get(corrlinks_ID=inmate)
            b = """You received pictures from the following people:
{msgs}
We process 20 pics for $10.  You currently have {balance} dollars to process pictures. If you are out of credit, please tell your people to go to call4pennies.com to reload. If you already have credit, we will process them soon."""
            temp = ''
            for relative, counts in info.items():
                dd = """{name}  number of pictures={no}""".format(name=relative, no=str(counts))
                temp += dd + '\n'
                body = "You sent {no} pictures to {idn}. Remember you can purchase picture credit at https://www.call4pennies.com/"
                body = body.format(no=str(counts), idn=str(inmateobj))
                relativeobj = SMSCustomer.objects.filter(name=relative, corrlinks_Customer=inmateobj)[0]
                sms = CorrlinksToSMS(_from=inmateobj, to=relativeobj, body=body)
                sms.save()
                resp, emsg = validate_number_and_send(inmateobj.phone_Number, relativeobj.phone_Number,
                                                      True, body)
                if resp:
                    sms.bandwidth_ID = emsg
                    sms.save()
                else:
                    if emsg == "you can't send message":
                        sms.status = 'dis'
                    elif emsg == 'error':
                        sms.status = 'err'
                    sms.save()
            b = b.format(msgs=temp, balance='$' + str(inmateobj.balance))
            new = SystemToCorrlinks(subject='New Pics', body=b, customer=inmateobj)
            new.save()

    def post(self, request):
        try:
            apikey = request.data['apikey']
            objs = APIKey.objects.get(API_Key=apikey)
        except Exception as e:
            return Response(data={'error': 'API Key is not valid ' + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        self.check_images_send_message()
        self.check_dues_send_messages()
        return Response(status=status.HTTP_200_OK)



class ImageUpload(APIView):
    def get(self, request):
        drive = GoogleDrive()
        drive.open_connection()
        objs = Image.objects.all()
        images = len(objs)
        print('Total', images)
        for obj in objs:
            imgpath = str(settings.BASE_DIR) + '/media/' + str(obj.image)
            drive.upload_image(imgpath, obj.corrCustomer.corrlinks_ID)
        return Response(data={'total':images},status=status.HTTP_200_OK)

