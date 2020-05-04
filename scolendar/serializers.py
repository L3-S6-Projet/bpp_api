import random
import string
import sys
from datetime import datetime

from django.conf import settings
from pytz import timezone
from rest_framework import serializers

from conf.auth import MIN_PASSWORD_LENGTH
from scolendar.models import Student, Class, Teacher, Classroom

try:
    import typing  # noqa: F401

    if sys.version_info >= (3, 4):
        from .method_serializers_with_typing import MethodFieldExampleSerializer
    else:
        from .method_serializers_without_typing import MethodFieldExampleSerializer
except ImportError:
    from .method_serializers_without_typing import MethodFieldExampleSerializer


######################################################
#                                                    #
#                       Teacher                      #
#                                                    #
######################################################


class TeacherCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'rank',
        ]
        extra_kwargs = {
            'password': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['password'] = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(MIN_PASSWORD_LENGTH))
        return ret

    def save(self, **kwargs):
        email = self.validated_data['email']
        phone_number = self.validated_data['phone_number']
        rank = self.validated_data['rank']

        dt = datetime.now(tz=timezone(settings.TIME_ZONE))
        dt_str = dt.strftime("%y%j%H%S")
        username = f"{self.validated_data['last_name'][0].lower()}{dt_str}"
        password = self.data['password']

        teacher = Teacher(email=email, username=username, phone_number=phone_number, rank=rank)

        teacher.set_password(password)
        teacher.save()

        return teacher


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
        ]


########################################################
#                                                      #
#                       Classroom                      #
#                                                      #
########################################################


class ClassroomCreationSerializer(serializers.ModelSerializer):
    def save(self, **kwargs):
        classroom = Classroom(name=self.validated_data['name'], capacity=self.validated_data['capacity'])
        classroom.save()
        return classroom

    class Meta:
        model = Classroom
        fields = [
            'name',
            'capacity',
        ]


class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classroom
        fields = [
            'id',
            'name',
            'capacity',
        ]


######################################################
#                                                    #
#                       Student                      #
#                                                    #
######################################################


class StudentCreationSerializer(serializers.ModelSerializer):
    class_id = serializers.IntegerField(required=False)

    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
            'class_id',
        ]
        extra_kwargs = {
            'password': {'required': False, 'allow_null': True}
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['password'] = ''.join(
            random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in
            range(MIN_PASSWORD_LENGTH))
        return ret

    def save(self, **kwargs):
        email = f"{self.validated_data['first_name']}{self.validated_data['last_name']}@etu.univ-amu.fr"

        dt = datetime.now(tz=timezone(settings.TIME_ZONE))
        dt_str = dt.strftime("%y%j%H%S")
        username = f"{self.validated_data['last_name'][0].lower()}{dt_str}"
        password = self.data['password']

        _class = Class.objects.get(id=self.validated_data['class_id'])

        student = Student(email=email, username=username, _class=_class)

        student.set_password(password)
        student.save()

        return student


class StudentSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'id',
            'first_name',
            'last_name',
            'class_name',
        ]
        extra_kwargs = {
            'class_name': {'required': False, 'allow_null': True},
        }
