# Create your views here.
import sys
sys.path.append('/opt/clemson/zfs_scripts/zettaknight')

from django.contrib.auth.models import User, Group
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework import status
from api.serializers import UserSerializer, GroupSerializer, DatasetSerializer
import zettaknight
import re
import logging

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class zettaknightview(APIView):
    """

    """
    def get(self, request):
        if self:
            print("User: {0}".format(self))

        if request:
            print("Dataset data: {0}".format(request.DATA))

        serializer = DatasetSerializer(request.DATA)
        #json = JSONRenderer().render(serializer.data)
        #print("Data Render: {0}".format(serializer.data))
        prog = "zettaknight.py"
        m_err = "mail_error"

        try:
            zfunc = re.sub(" u", " ", serializer.data['function'])
        except TypeError as e:
            zfunc = 'check_usage'
            pass

        if str(zfunc) != 'check_usage':
            logger.error("Exception: Accepted function calls are: check_usage.  Supplied call: {0}".format(zfunc))
            return Response("Exception: Accepted function calls are: check_usage.  Supplied call: {0}".format(zfunc), status=status.HTTP_400_BAD_REQUEST)

        if serializer.data['args']:
                zargs = re.sub(" u", " ", serializer.data['args'])

        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(m_err)
        try:
            if zargs:
                zarg_list.append(zargs)
                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2} {3}".format(serializer.data, prog, zfunc, zargs))
            else:
                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2}".format(serializer.data, prog, zfunc))
        except:
            pass

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_200_OK)


    def post(self, request):
        if self:
            print("User: {0}".format(self))

        if request:
            print("Dataset data: {0}".format(request.DATA))

        serializer = DatasetSerializer(request.DATA)
        #json = JSONRenderer().render(serializer.data)
        #print("Data Render: {0}".format(serializer.data))
        prog = "zettaknight.py"
        m_err = "mail_error"
        zfunc = re.sub(" u", " ", serializer.data['function'])
        if serializer.data['args']:
                zargs = re.sub(" u", " ", serializer.data['args'])

        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(m_err)
        try:
            if zargs:
                zarg_list.append(zargs)
                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2} {3}".format(serializer.data, prog, zfunc, zargs))
            else:
                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2}".format(serializer.data, prog, zfunc))
        except:
            pass

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_202_ACCEPTED)


class zettaknightshareview(APIView):

    def get(self, request):

        serializer = DatasetSerializer(request.DATA)
        prog = "zettaknight.py"
        zfunc = "check_group_quota"
        if serializer.data['user']:
            zargs = re.sub(" u", " ", serializer.data['user'])
        else:
            return Response("Function cannot be executed without providing a user or group.", status=status.HTTP_400_BAD_REQUEST)
        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(str(zargs))

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_200_OK)


    def post(self, request):

        serializer = DatasetSerializer(request.DATA)
        prog = "zettaknight.py"
        m_err = "mail_error"
        zfunc = "create_cifs_share"
        if serializer.data['args']:
                zargs = re.sub(" u", " ", serializer.data['args'])

        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(m_err)
        try:
            if zargs:
                for i in zargs.split(" "):
                    zarg_list.append(str(i))

                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2} {3}".format(serializer.data, prog, zfunc, zargs))
            else:
                logger.info("POST received.\nNo user or dataset supplied, cannot continue.  POST included the following data {0}.".format(serializer.data))
                return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_202_ACCEPTED)


class zettaknightquotaview(APIView):

    def get(self, request):

        serializer = DatasetSerializer(request.DATA)
        prog = "zettaknight.py"
        zfunc = "get_cifs_quota"
        if serializer.data['args']:
                zargs = re.sub(" u", " ", serializer.data['args'])
        else:
            return Response("Function cannot be executed without providing a user or group.", status=status.HTTP_400_BAD_REQUEST)
        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(str(zargs))

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_200_OK)
		
		
    def post(self, request):

        serializer = DatasetSerializer(request.DATA)
        prog = "zettaknight.py"
        m_err = "mail_error"
        zfunc = "set_cifs_quota"
        if serializer.data['args']:
                zargs = re.sub(" u", " ", serializer.data['args'])

        zarg_list = []
        zarg_list.append(prog)
        zarg_list.append(zfunc)
        zarg_list.append(m_err)
        try:
            if zargs:
                for i in zargs.split(" "):
                    zarg_list.append(str(i))

                logger.info("POST received.\nRequest included the following data: {0}\nAttempting to execute the following: {1} {2} {3}".format(serializer.data, prog, zfunc, zargs))
            else:
                logger.info("POST received.\nNo user or dataset supplied, cannot continue.  POST included the following data {0}.".format(serializer.data))
                return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        try:
            job_out = zettaknight._entry_point(zarg_list)
            print("Job Out: {0}".format(job_out))
            logger.info("Job Out: {0}".format(job_out))
        except Exception as e:
            logger.error("Exception: {0}".format(e))
            return Response("Function could not be executed.", status=status.HTTP_400_BAD_REQUEST)

        return Response(str(job_out), status=status.HTTP_202_ACCEPTED)
