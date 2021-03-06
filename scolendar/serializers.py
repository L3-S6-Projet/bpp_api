import random
import string
from datetime import datetime

from django.conf import settings
from pytz import timezone
from rest_framework import serializers

from conf.auth import MIN_PASSWORD_LENGTH
from scolendar.models import Student, Class, Teacher, Classroom, Occupancy, Subject, TeacherSubject


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
        def clean_phone_number(number_str: str) -> str:
            number_str = ''.join(''.join(number_str.split(' ')).split('-'))
            number_str = ' '.join(a + b for a, b in zip(number_str[::2], number_str[1::2]))
            return number_str

        email = self.validated_data['email']
        phone_number = clean_phone_number(self.validated_data['phone_number'])
        rank = self.validated_data['rank']
        first_name = self.validated_data['first_name'].title()
        last_name = self.validated_data['last_name'].upper()

        dt = datetime.now(tz=timezone(settings.TIME_ZONE))
        dt_str = dt.strftime("%y%j%H%S")
        username = f"{self.validated_data['last_name'][0].lower()}{dt_str}"
        password = self.data['password']

        teacher = Teacher(
            email=email,
            username=username,
            phone_number=phone_number,
            rank=rank,
            first_name=first_name,
            last_name=last_name,
        )

        teacher.set_password(password)
        teacher.save()

        return teacher


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
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


####################################################
#                                                  #
#                      Class                       #
#                                                  #
####################################################


class ClassCreationSerializer(serializers.ModelSerializer):
    def save(self, **kwargs):
        _class = Class(name=self.validated_data['name'])
        _class.save()
        return _class

    class Meta:
        model = Class
        fields = [
            'name',
        ]


class ClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = [
            'id',
            'name',
            'level',
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

    @staticmethod
    def get_class_name(obj):
        return obj._class.name


######################################################
#                                                    #
#                       Subject                      #
#                                                    #
######################################################

class SubjectCreationSerializer(serializers.ModelSerializer):
    class_id = serializers.IntegerField()
    teacher_in_charge_id = serializers.IntegerField()

    def save(self, **kwargs):
        _class = Class.objects.get(id=self.validated_data['class_id'])
        teacher_in_charge = Teacher.objects.get(id=self.validated_data['teacher_in_charge_id'])

        subject = Subject(_class=_class, name=self.validated_data['name'])
        subject.save()

        try:
            subject_teacher = TeacherSubject.objects.get(teacher=teacher_in_charge, subject=subject)
        except TeacherSubject.DoesNotExist:
            subject_teacher = TeacherSubject(teacher=teacher_in_charge, subject=subject)

        subject_teacher.in_charge = True
        subject_teacher.save()

        return subject

    class Meta:
        model = Subject
        fields = [
            'name',
            'class_id',
            'teacher_in_charge_id',
        ]


class SubjectSerializer(serializers.ModelSerializer):
    class_name = serializers.CharField(source='_class.name')

    class Meta:
        model = Subject
        fields = [
            'id',
            'class_name',
            'name',
        ]


########################################################
#                                                      #
#                      Occupancy                       #
#                                                      #
########################################################


class OccupancyCreationSerializer(serializers.ModelSerializer):
    def save(self, subject_id, **kwargs):
        classroom = Classroom.objects.get(id=self.validated_data['classroom_id'])
        subject = Subject.objects.get(id=subject_id)
        start_datetime = datetime.fromtimestamp(self.validated_data['start'])
        end_datetime = datetime.fromtimestamp(self.validated_data['end'])
        occupancy = Occupancy(
            classroom=classroom,
            subject=subject,
            start_datetime=start_datetime,
            duration=end_datetime - start_datetime,
            name=self.validated_data['name'],
            occupancy_type=self.validated_data['occupancy_type']
        )
        occupancy.save()
        return occupancy

    class Meta:
        model = Occupancy
        fields = [
            'classroom_id',
            'subject_id',
            'teacher',
            'start_date',
            'duration',
            'occupancy_type',
        ]


class OccupancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Occupancy
        fields = [
            'id',
            'classroom',
            'group_number',
            'subject',
            'teacher',
            'start_datetime',
            'duration',
            'occupancy_type',
        ]
