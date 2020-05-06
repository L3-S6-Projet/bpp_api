from drf_yasg.openapi import Schema, Response, Parameter, TYPE_OBJECT, TYPE_ARRAY, TYPE_INTEGER, TYPE_STRING, \
    TYPE_BOOLEAN, IN_QUERY
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response as RF_Response
from rest_framework.views import APIView

from scolendar.errors import error_codes
from scolendar.exceptions import TeacherInChargeError
from scolendar.models import Student, Teacher, occupancy_list, Classroom, Class, Subject, \
    SubjectTeacher
from scolendar.paginations import PaginationHandlerMixin, SubjectResultSetPagination
from scolendar.serializers import OccupancyCreationSerializer, SubjectSerializer, SubjectCreationSerializer
from scolendar.viewsets.auth_viewsets import TokenHandlerMixin


class SubjectViewSet(APIView, PaginationHandlerMixin, TokenHandlerMixin):
    pagination_class = SubjectResultSetPagination

    @swagger_auto_schema(
        operation_summary='Returns a paginated list of all subjects.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              '10 subjects should be returned per page. At least three characters should be provided '
                              'for the search.',
        responses={
            200: Response(
                description='A list of all subjects.',
                schema=Schema(
                    title='SubjectListResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'total': Schema(
                            type=TYPE_INTEGER,
                            description='Total number of subjects',
                            example=166
                        ),
                        'subjects': Schema(
                            type=TYPE_ARRAY,
                            items=Schema(
                                type=TYPE_OBJECT,
                                properties={
                                    'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                    'name': Schema(type=TYPE_STRING, example='PPPE'),
                                },
                                required=['class_name', 'name', ]
                            ),
                        ),
                    },
                    required=['status', 'total', 'subjects', ]
                )
            ),
            401: Response(
                description='Unauthorized access',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, value='error'),
                        'code': Schema(type=TYPE_STRING, value='InsufficientAuthorization', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        manual_parameters=[
            Parameter(name='query', in_=IN_QUERY, type=TYPE_STRING, required=False),
        ],
    )
    def get(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            queryset = Subject.objects.all()
            serializer = SubjectSerializer(queryset, many=True)
            data = {
                'status': 'success',
                'total': len(serializer.data),
                'students': serializer.data,
            }
            return RF_Response(data)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Creates a new subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            201: Response(
                description='Subject created',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                    },
                    required=['status', 'username', 'password', ]
                )
            ),
            401: Response(
                description='Unauthorized access',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InvalidCredentials',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InvalidCredentials',
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }
                )
            ),
            422: Response(
                description='Invalid email (code=`InvalidEmail`)\nInvalid phone number (code=`InvalidPhoneNumber`)\n'
                            'Invalid rank (code=`InvalidRank`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),

        },
        tags=['Subjects', ],
        request_body=Schema(
            title='SubjectCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='PPPE'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
                'teacher_in_charge_id': Schema(type=TYPE_INTEGER, example=166),
            },
            required=['name', 'class_id', 'teacher_in_charge_id', ]
        )
    )
    def post(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                serializer = SubjectCreationSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Class.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response(serializer.data, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Deletes the given students using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.\n'
                              'This request should trigger the re-organization of students in the affected groups.',
        responses={
            200: Response(
                description='Data deleted',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'success': Schema(
                            type=TYPE_STRING,
                            example='success'),
                    },
                    required=['success', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            value='InsufficientAuthorization',
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            example='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(
                type=TYPE_INTEGER,
                example=166
            )
        ),
    )
    def delete(self, request, *args, **kwargs):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            def delete_subject(student_id: int):
                subject = Subject.objects.get(id=student_id)
                subject.delete()

            for post_id in request.data:
                try:
                    delete_subject(post_id)
                except Subject.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectDetailViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets information on a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Subject information',
                schema=Schema(
                    title='SubjectResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'subject': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                'name': Schema(type=TYPE_STRING, example='PPPE'),
                                'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUEE'),
                                'total_hours': Schema(type=TYPE_INTEGER, example=166),
                                'teachers': Schema(
                                    type=TYPE_ARRAY,
                                    items=Schema(
                                        type=TYPE_OBJECT,
                                        properties={
                                            'id': Schema(type=TYPE_INTEGER, example=166),
                                            'first_name': Schema(type=TYPE_STRING, example='John'),
                                            'last_name': Schema(type=TYPE_STRING, example='Doe'),
                                            'in_charge': Schema(type=TYPE_BOOLEAN, example=False),
                                        },
                                        required=['id', 'first_name', 'last_name', 'in_charge', ]
                                    )
                                ),
                                'groups': Schema(
                                    type=TYPE_OBJECT,
                                    properties={
                                        'id': Schema(type=TYPE_INTEGER, example=166),
                                        'name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                        'count': Schema(type=TYPE_INTEGER, example=166),
                                    },
                                    required=['id', 'name', 'count', ]
                                ),
                            },
                            required=[
                                'name',
                                'class_name',
                                'total_hours',
                                'teachers',
                                'groups',
                            ]
                        ),
                    },
                    required=['status', 'subject', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ]
    )
    def get(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Student.objects.get(id=subject_id)

                def get_teachers() -> list:
                    teachers = []
                    # TODO so much shit...
                    return teachers

                def get_groups() -> list:
                    groups = []
                    # TODO too much shit...
                    return groups

                def count_hours() -> int:
                    total = 0
                    # TODO well...
                    return total

                subject = {
                    'name': subject.name,
                    'class_name': subject._class.name,
                    'total_hours': count_hours(),
                    'teachers': get_teachers(),
                    'groups': get_groups()
                }
                return RF_Response({'status': 'success', 'subject': subject})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Updates information for a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'The teacher designed by teacher_in_charge_id should already be a teacher of that '
                              'subject.',
        responses={
            200: Response(
                description='Subject updated',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success')
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(
                            type=TYPE_STRING,
                            value='error'),
                        'code': Schema(
                            type=TYPE_STRING,
                            enum=error_codes),
                    }, required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='SubjectUpdateRequest',
            type=TYPE_OBJECT,
            properties={
                'name': Schema(type=TYPE_STRING, example='PPPE'),
                'class_id': Schema(type=TYPE_INTEGER, example=166),
                'teacher_in_charge_id': Schema(type=TYPE_INTEGER, example=166),
            },
            required=['name', 'class_id', 'teacher_in_charge_id', ]
        )
    )
    def put(self, request, student_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                subject = Subject.objects.get(id=student_id)
                data = request.data
                data_keys = data.keys()
                if 'name' in data_keys:
                    subject.name = data['first_name']
                if 'class_id' in data_keys:
                    try:
                        _class = Class.objects.get(id=data['class_id'])
                        subject._class = _class
                    except Class.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                if 'teacher_in_charge_id' in data_keys:
                    try:
                        new_teacher_in_charge = Teacher.objects.get(id=data['teacher_in_charge_id'])
                        try:
                            subject_teacher = SubjectTeacher.objects.get(subject_id=subject.id, in_charge=True)
                            subject_teacher.in_charge = False
                        except SubjectTeacher.DoesNotExist:
                            pass
                        try:
                            subject_teacher = SubjectTeacher.objects.get(teacher=new_teacher_in_charge, subject=subject)
                        except SubjectTeacher.DoesNotExist:
                            subject_teacher = SubjectTeacher(teacher=new_teacher_in_charge, subject=subject)
                        subject_teacher.in_charge = True
                        subject_teacher.save()
                    except Teacher.DoesNotExist:
                        return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                subject.save()
                return RF_Response({'status': 'success'})
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a subject for the given time period.',
        operation_description='Note : only users with the role `administrator`, or professors who are a teacher of the'
                              ' subject should be able to access this route.',
        responses={
            200: Response(
                description='Subject occupancies',
                schema=Schema(
                    title='SubjectOccupancies',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='success'),
                        'occupancies': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                '05-01-2020': Schema(
                                    type=TYPE_OBJECT,
                                    properties={
                                        'id': Schema(type=TYPE_INTEGER, example=166),
                                        'classroom_name': Schema(type=TYPE_STRING, example='B.001'),
                                        'group_name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                        'subject_name': Schema(type=TYPE_STRING, example='Algorithmique'),
                                        'teacher_name': Schema(type=TYPE_STRING, example='John Doe'),
                                        'start': Schema(type=TYPE_INTEGER, example=1587776227),
                                        'end': Schema(type=TYPE_INTEGER, example=1587776227),
                                        'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                                        'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                        'name': Schema(type=TYPE_STRING, example='Algorithmique TP Groupe 1'),
                                    },
                                    required=[
                                        'id',
                                        'group_name',
                                        'subject_name',
                                        'teacher_name',
                                        'start',
                                        'end',
                                        'occupancy_type',
                                        'name',
                                    ]
                                )
                            },
                            required=[
                                'status',
                                'occupancies',
                            ]
                        ),
                    },
                    required=['status', 'occupancies', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidCredentials', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s) (code=`InvalidID`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, example='error'),
                        'code': Schema(type=TYPE_STRING, value='InvalidID', enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', 'role-professor', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ],
    )
    def get(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_403_FORBIDDEN)
            try:
                student = Subject.objects.get(id=subject_id)

                def get_occupancies() -> dict:
                    occupancies = {}
                    # TODO crawling under so much shit
                    return occupancies

                response = {
                    'status': 'success',
                    'occupancies': get_occupancies(),
                }
                return RF_Response(response)
            except Student.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Creates a new occupancy for a given subject.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this'
                              ' route.\nThe occupancy types `td` and `tp` should be rejected. Only classrooms that are'
                              ' free should be accepted. Only classes that are not (any of their groups too) in any'
                              ' classes at the specified time should be accepted.',
        responses={
            200: Response(
                description='Data saved',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    }
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    }
                )
            ),
        },
        tags=['role-professor', ],
        request_body=Schema(
            title='OccupancyCreationRequest',
            type=TYPE_OBJECT,
            properties={
                'classroom_id': Schema(type=TYPE_INTEGER, example=166),
                'start': Schema(type=TYPE_INTEGER, example=166),
                'end': Schema(type=TYPE_INTEGER, example=166),
                'name': Schema(type=TYPE_STRING, example='Algorithmique CM Groupe 1'),
                'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
            },
            required=['classroom_id', 'start', 'end', 'name', 'occupancy_type', ]
        )
    )
    def post(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                serializer = OccupancyCreationSerializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save(subject_id)
            except Classroom.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectTeacherViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Adds new teachers to a subject using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route.',
        responses={
            200: Response(
                description='Teachers added',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(type=TYPE_INTEGER, example=166),
        )
    )
    def post(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)
            try:
                subject = Subject.objects.get(id=subject_id)
                for post_id in request.data:
                    subject_teacher = SubjectTeacher(subject=subject, teacher_id=post_id)
                    subject_teacher.save()
            except Subject.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            except Teacher.DoesNotExist:
                return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
            return RF_Response({'status': 'success'}, status=status.HTTP_201_CREATED)
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)

    @swagger_auto_schema(
        operation_summary='Removes teachers from a subject using their IDs.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This request should be denied if there is less than one teacher in the subject, or if '
                              'the teacher is in charge.',
        responses={
            200: Response(
                description='Teachers removed',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects', ],
        request_body=Schema(
            title='IDRequest',
            type=TYPE_ARRAY,
            items=Schema(type=TYPE_INTEGER, example=166),
        )
    )
    def delete(self, request, subject_id):
        try:
            token = self._get_token(request)
            if not token.user.is_staff:
                return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                                   status=status.HTTP_401_UNAUTHORIZED)

            def remove_teacher_from_subject(teacher_id: int):
                subject_teachers = SubjectTeacher.objects.filter(subject_id=subject_id)
                if len(subject_teachers) <= 1:
                    raise TeacherInChargeError('Not enough teachers')

                subject_teacher = SubjectTeacher.objects.get(teacher_id=teacher_id, subject_id=subject_id)
                if subject_teacher.in_charge:
                    raise TeacherInChargeError('Teacher is in charge')
                subject_teacher.delete()

            for post_id in request.data:
                try:
                    remove_teacher_from_subject(post_id)
                except SubjectTeacher.DoesNotExist:
                    return RF_Response({'status': 'error', 'code': 'InvalidID'}, status=status.HTTP_404_NOT_FOUND)
                except TeacherInChargeError:
                    return RF_Response({'status': 'error', 'code': 'TeacherInCharge'},
                                       status=status.HTTP_422_UNPROCESSABLE_ENTITY)

            return RF_Response({'status': 'success'})
        except Token.DoesNotExist:
            return RF_Response({'status': 'error', 'code': 'InsufficientAuthorization'},
                               status=status.HTTP_401_UNAUTHORIZED)


class SubjectGroupViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Adds a new group to a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This should trigger the re-organization of groups.',
        responses={
            200: Response(
                description='Groups added',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects']
    )
    def post(self, request, subject_id):
        # TODO Need specs
        pass

    @swagger_auto_schema(
        operation_summary='Removes a group from a subject.',
        operation_description='Note : only users with the role `administrator` should be able to access this route. '
                              'This should trigger the re-organisation of groups. This request should be denied if '
                              'there is less than one group in the subject.',
        responses={
            200: Response(
                description='Groups removed',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['Subjects']
    )
    def delete(self, request, subject_id):
        # TODO Need specs
        pass


class SubjectGroupOccupancyViewSet(APIView, TokenHandlerMixin):
    @swagger_auto_schema(
        operation_summary='Gets the occupancies of a subject for the given time period.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this '
                              'route.',
        responses={
            200: Response(
                description='Groups occupancies',
                schema=Schema(
                    title='Occupancies',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'occupancies': Schema(
                            type=TYPE_OBJECT,
                            properties={
                                '05-01-2020': Schema(
                                    type=TYPE_OBJECT,
                                    properties={
                                        'id': Schema(type=TYPE_INTEGER, example=166),
                                        'classroom_name': Schema(type=TYPE_STRING, example='B.001'),
                                        'group_name': Schema(type=TYPE_STRING, example='Groupe 1'),
                                        'subject_name': Schema(type=TYPE_STRING, example='Algorithmique'),
                                        'teacher_name': Schema(type=TYPE_STRING, example='John Doe'),
                                        'start': Schema(type=TYPE_INTEGER, example=1587776227),
                                        'end': Schema(type=TYPE_INTEGER, example=1587776227),
                                        'occupancy_type': Schema(type=TYPE_STRING, enum=occupancy_list),
                                        'class_name': Schema(type=TYPE_STRING, example='L3 INFORMATIQUE'),
                                        'name': Schema(type=TYPE_STRING, example='Algorithmique TP Groupe 1'),
                                    },
                                    required=[
                                        'id',
                                        'group_name',
                                        'subject_name',
                                        'teacher_name',
                                        'start',
                                        'end',
                                        'occupancy_type',
                                        'name',
                                    ]
                                )
                            },
                            required=[
                                'status',
                                'occupancies',
                            ]
                        ),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['role-professor', ],
        manual_parameters=[
            Parameter(name='start', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='end', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
            Parameter(name='occupancies_per_day', in_=IN_QUERY, type=TYPE_INTEGER, required=True),
        ],
    )
    def get(self, request, subject_id, group_id):
        # TODO
        pass

    @swagger_auto_schema(
        operation_summary='Creates a new occupancy for a given group of a subject.',
        operation_description='Note : only professors who are a teacher of the subject should be able to access this '
                              'route.\nThe only accepted occupancy types should be `td` and `tp`.\nThe classroom id '
                              'should **NOT** be nullable. Only classrooms that are free should be accepted. Only '
                              'groups that are not (and their class too) in any classes at the specified time should '
                              'be accepted.',
        responses={
            200: Response(
                description='Data saved',
                schema=Schema(
                    title='SimpleSuccessResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                    },
                    required=['status', ]
                )
            ),
            401: Response(
                description='Invalid token (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            403: Response(
                description='Insufficient rights (code=`InvalidCredentials`)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            404: Response(
                description='Invalid ID(s)',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
            422: Response(
                description='Invalid data',
                schema=Schema(
                    title='ErrorResponse',
                    type=TYPE_OBJECT,
                    properties={
                        'status': Schema(type=TYPE_STRING, examplee='success'),
                        'code': Schema(type=TYPE_STRING, enum=error_codes),
                    },
                    required=['status', 'code', ]
                )
            ),
        },
        tags=['role-professor', ]
    )
    def post(self, request, subject_id, group_id):
        # TODO
        pass